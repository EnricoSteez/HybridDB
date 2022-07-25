from math import ceil
import os
import pulp as pulp
from openpyxl import Workbook
from pulp import constants
from pulp.pulp import lpSum
import params
import numpy as np
import sys
from time import time

# from time import gmtime
# from time import strftime
import json
import telegram
from os import path

# import threading
from functools import partial

from zipfianMerger import mergeZipfians

print = partial(print, flush=True)
cost_write = params.COST_DYNAMO_WRITE_UNIT
cost_read = params.COST_DYNAMO_READ_UNIT
cost_storage = params.COST_DYNAMO_STORAGE
cost_volume_storage = params.COST_VOLUME_STORAGE  # per hour
cost_volume_iops = params.COST_VOLUME_IOPS
cost_volume_tp = params.COST_VOLUME_THROUGHPUT
vm_types = params.vm_types
vm_IOPS = params.vm_IOPS
vm_bandwidths = params.vm_bandwidths
vm_costs = params.vm_costs
stability_period = params.WORKLOAD_STABILITY
RF = params.REPLICATION_FACTOR
num_machines = len(vm_types)
M = 1e5
max_storage = params.MAX_SIZE
volume_types = params.volumes
max_volume_iops = params.MAX_VOLUME_IOPS
max_volume_bandwidths = params.MAX_VOLUME_THROUGHPUT
b = 1


def notify(message):
    with open("./keys/keys.json", "r") as keys_file:
        k = json.load(keys_file)
        token = k["telegram_token"]
        chat_id = k["telegram_chat_id"]
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=message)


def extract_type_name(machine_counts):
    for i in range(len(machine_counts)):
        if machine_counts[i].value() != 0:
            return vm_types[i]
    return None


if len(sys.argv) != 11:
    sys.exit(
        f"Usage: python3 {path.basename(__file__)}"
        " <N1> <items_size 1 [MB]> <tot_throughput 1> <skew 1> <read % 1>"
        " <N2> <items_size 2 [MB]> <tot_throughput 2> <skew 2> <read % 2>"
        f"\n (you inserted {len(sys.argv)} args)"
    )
try:
    N1 = int(sys.argv[1])
    size_1 = float(sys.argv[2])
    tot_throughput_1 = float(sys.argv[3])
    skew_1 = float(sys.argv[4])
    read_percent_1 = float(sys.argv[5])
    N2 = int(sys.argv[6])
    size_2 = float(sys.argv[7])
    tot_throughput_2 = float(sys.argv[8])
    skew_2 = float(sys.argv[9])
    read_percent_2 = float(sys.argv[10])
except ValueError:
    sys.exit("Check args: N:int, everything else:float")
N = N1 + N2

size_for_filename1 = str(size_1)
throughput_for_filename1 = str(tot_throughput_1)
skew_for_filename1 = str(skew_1)
read_percent_filename1 = str(read_percent_1)
size_for_filename2 = str(size_2)
throughput_for_filename2 = str(tot_throughput_2)
skew_for_filename2 = str(skew_2)
read_percent_filename2 = str(read_percent_2)
# if integer, remove .0 else replace dot with comma
if size_1.is_integer():
    size_for_filename1 = size_for_filename1[:-2]
else:
    size_for_filename2 = size_for_filename1.replace(".", ",")
if tot_throughput_1.is_integer():
    throughput_for_filename1 = throughput_for_filename1[:-2]
else:
    throughput_for_filename1 = throughput_for_filename1.replace(".", ",")
if skew_1.is_integer():
    skew_for_filename1 = skew_for_filename1[:-2]
else:
    skew_for_filename1 = skew_for_filename1.replace(".", ",")

if size_2.is_integer():
    size_for_filename2 = size_for_filename2[:-2]
else:
    size_for_filename2 = size_for_filename2.replace(".", ",")
if tot_throughput_2.is_integer():
    throughput_for_filename2 = throughput_for_filename2[:-2]
else:
    throughput_for_filename2 = throughput_for_filename2.replace(".", ",")
if skew_2.is_integer():
    skew_for_filename2 = skew_for_filename2[:-2]
else:
    skew_for_filename2 = skew_for_filename2.replace(".", ",")

# these are always decimal ehehe
read_percent_filename1 = read_percent_filename1.replace(".", ",")
read_percent_filename2 = read_percent_filename2.replace(".", ",")

filename = ( 
    f"../results/"
    f"{N1}_{size_for_filename1}_{throughput_for_filename1}_"
    f"{skew_for_filename1}_r{read_percent_filename1}_" 
    f"{N2}_{size_for_filename2}_{throughput_for_filename2}_"
    f"{skew_for_filename2}_r{read_percent_filename2}"
    ".txt" 
)

sys.stdout = open(filename, "w")

items = [i for i in range(N)]

# x vector x
x = pulp.LpVariable.dicts("x", indices=(items, vm_types), cat=constants.LpBinary)

m = pulp.LpVariable.dicts(
    "Number of used machines per type",
    indices=vm_types,
    cat=constants.LpInteger,
    lowBound=0,
)

z = pulp.LpVariable.dicts(
    "m outside of 0..RF interval",
    indices=vm_types,
    cat=constants.LpBinary,
)

d = pulp.LpVariable.dicts(
    "Which machine types are used",
    indices=vm_types,
    cat=constants.LpBinary,
)

# sizes in MB, throughputs in ops/s
s, t_r, t_w = mergeZipfians(
    n1=N1,
    skew1=skew_1,
    tot_tp_1=tot_throughput_1,
    read_percent_1=read_percent_1,
    size1=size_1,
    n2=N2,
    skew2=skew_2,
    tot_tp_2=tot_throughput_2,
    read_percent_2=read_percent_2,
    size2=size_2,
)
total_size = sum(s)
total_iops = sum((t_r[i] + t_w[i] * RF) for i in range(N))
total_band = sum((t_r[i] + t_w[i] * RF) * s[i] for i in range(N))
num_vms = len(vm_types)
solver = pulp.getSolver("GUROBI_CMD")
best_cost_hybrid = np.inf
best_vms_hybrid = dict()
best_placement_hybrid = dict()
best_volume_hybrid = ""
t0 = time()
for v_type in volume_types:
    # Optimization Problem
    problem = pulp.LpProblem("Placement", pulp.LpMinimize)

    # objective function
    problem += (
        lpSum([m[vmtype] * vm_costs[vmtype] for vmtype in vm_types])
        + lpSum([m[vmtype] for vmtype in vm_types])
        * max_storage
        * cost_volume_storage[v_type]
        + lpSum(
            [(t_r[i] + t_w[i] * RF) * s[i] * params.IO_FACTOR[v_type] for i in range(N)]
        )
        * 60
        * 60
        * cost_volume_iops[v_type]
        + lpSum([(t_r[i] + t_w[i] * RF) * s[i] for i in range(N)])
        * 60
        * 60
        * cost_volume_tp[v_type],
        "Minimization of the total cost of the hybrid solution",
    )

    # constraints
    # at least RF machines in total
    # problem += lpSum([m[vmtype] for vmtype in vm_types]) >= RF

    # --------------------########## ENOUGH STORAGE (COMBINED) ##########--------------------
    problem += (
        max_storage * lpSum([m[vmtype] for vmtype in vm_types]) >= total_size * RF
    )

    # --------------------########## EVERY ITEM IS PLACED IN ONLY ONE MACHINE TYPE ##########--------------------
    for i in range(N):
        problem += lpSum([x[i][vmtype] for vmtype in vm_types]) == 1

    for vmtype in vm_types:
        # --------------------########## ENOUGH IOPS ##########--------------------
        # VMs
        problem += (
            lpSum(
                [
                    x[i][vmtype]
                    * (t_r[i] + t_w[i] * RF)
                    * s[i]
                    * 10**6
                    / 2**10
                    / 16
                    for i in range(N)
                ]
            )
            <= m[vmtype] * vm_IOPS[vmtype]
        )
        # VOLUMES
        problem += (
            lpSum(
                [
                    x[i][vmtype]
                    * (t_r[i] + t_w[i] * RF)
                    * s[i]
                    * params.IO_FACTOR[v_type]
                    for i in range(N)
                ]
            )
            <= m[vmtype] * max_volume_iops[v_type]
        )

        # --------------------########## ENOUGH BANDWIDTH ##########--------------------
        # VMs
        problem += (
            lpSum([x[i][vmtype] * (t_r[i] + t_w[i] * RF) * s[i] for i in range(N)])
            <= m[vmtype] * vm_bandwidths[vmtype]
        )
        # VOLUMES
        problem += (
            lpSum([x[i][vmtype] * (t_r[i] + t_w[i] * RF) * s[i] for i in range(N)])
            * 10**6
            / 2**20
            <= m[vmtype] * max_volume_bandwidths[v_type]
        )

        # --------------------########## ENOUGH STORAGE ##########--------------------
        problem += (
            lpSum([x[i][vmtype] * s[i] for i in range(N)]) * RF
            <= max_storage * m[vmtype]
        )
        problem += lpSum(x[i][vmtype] for i in range(N)) >= -M * (1 - d[vmtype])
        problem += lpSum(x[i][vmtype] for i in range(N)) <= M * d[vmtype]
        problem += m[vmtype] <= M * d[vmtype]
        problem += m[vmtype] >= RF - M * (1 - d[vmtype])


    result = problem.solve(solver)
    cost = problem.objective.value()
    tot_vms = sum(m[vm].value() for vm in vm_types)
    allocated_machine_iops = dict()
    allocated_size = dict()
    allocated_band = dict()
    available_machine_iops = dict()
    available_band_machines = dict()
    available_band_volumes = dict()
    allocated_volume_iops = dict()
    available_volume_iops = dict()
    available_size = dict()
    print("*" * 20, end="")
    print(f" {v_type} ", end="")
    print("*" * 20)
    for vm in vm_types:
        # MACHINE IOPS are NOT absolute user's issued IOPS but:
        # IOPS * size (KiB) / 16 -> { 16KiB per IO }
        allocated_machine_iops[vm] = sum(
            x[i][vm].value() * (t_r[i] + t_w[i] * RF) * s[i] * 10**6 / 2**10 / 16
            for i in range(N)
        )
        allocated_volume_iops[vm] = sum(
            x[i][vm].value() * (t_r[i] + t_w[i] * RF) * s[i] * params.IO_FACTOR[v_type]
            for i in range(N)
        )
        # this is always in MB/s so no conversion necessary
        allocated_band[vm] = sum(
            x[i][vm].value() * (t_r[i] + t_w[i] * RF) * s[i] for i in range(N)
        )
        # also in MB/s
        allocated_size[vm] = sum(x[i][vm].value() * s[i] for i in range(N))
        available_machine_iops[vm] = vm_IOPS[vm] * m[vm].value()
        available_volume_iops[vm] = max_volume_iops[v_type] * m[vm].value()
        available_band_machines[vm] = vm_bandwidths[vm] * m[vm].value()
        available_band_volumes[vm] = max_volume_bandwidths[v_type] * m[vm].value()
        available_size[vm] = params.MAX_SIZE * m[vm].value()

    for vm in vm_types:
        if m[vm].value() > 0:
            print(f"***** {m[vm].value()} {vm} *****")
            print(
                f"Solver allocated {allocated_machine_iops[vm]:.4f} MACHINE IOPS "
                f"out of {total_iops*total_size*10**6/2**10/16:.4f} MACHINE IOPS\n"
                f"which is equivalent to {allocated_volume_iops[vm]:.4f} VOLUME IOPS "
                f"out of {total_iops*total_size*params.IO_FACTOR[v_type]:.4f} VOLUME IOPS"
            )
            print(
                f"{m[vm].value()} {vm} MACHINES provide max {available_machine_iops[vm]:.4f} MACHINE IOPS"
            )
            print(
                f"{m[vm].value()} {v_type} VOLUMES provide max {max_volume_iops[v_type] * m[vm].value()} IOPS"
            )
            print("-----")
            print(
                f"Solver allocated {allocated_band[vm]:.2f} MB/s"
                f"out of {total_band:.2f} MB/s"
            )
            print(
                f"{m[vm].value()} {vm} MACHINES provide max {available_band_machines[vm]:.2f} MB/s "
            )
            print(
                f"{m[vm].value()} {v_type} VOLUMES provide max {max_volume_bandwidths[v_type] * m[vm].value():.0f} MB/s "
            )
            print("-----")
            print(f"Solver allocated {allocated_size[vm]} MB")
            print(
                f"{m[vm].value()} {v_type} VOLUMES provide max {params.MAX_SIZE*m[vm].value():.0f} MB"
            )
    iops_sat_vm = sum(allocated_machine_iops.values()) / sum(
        available_machine_iops.values()
    )
    iops_sat_vol = sum(allocated_volume_iops.values()) / sum(
        available_volume_iops.values()
    )
    band_sat_vm = sum(allocated_band.values()) / sum(available_band_machines.values())
    band_sat_vol = sum(allocated_band.values()) / sum(available_band_volumes.values())
    size_sat_vol = total_size / (params.MAX_SIZE * tot_vms)
    print(f"TOTAL IOPS SATURATION (VMs): {iops_sat_vm:.2%}")
    print(f"TOTAL IOPS SATURATION (Volumes): {iops_sat_vol:.2%}")
    print(f"TOTAL BANDWIDTH SATURATION (VMs): {band_sat_vm:.2%}")
    print(f"TOTAL BANDWIDTH SATURATION (Volumes): {band_sat_vol:.2%}")
    print(f"TOTAL SIZE SATURATION (Volumes): {size_sat_vol:.2%}")

    if cost < best_cost_hybrid:
        best_cost_hybrid = round(cost, 4)
        best_placement_hybrid = x
        best_volume_hybrid = v_type
        best_vms_hybrid = {vmtype: m[vmtype].value() for vmtype in vm_types}

    # prettier print :)
    hybrid = "HYBRID" if sum(m[vm].value() for vm in vm_types) > 0 else "SOLVER"
    print(f"{hybrid} COST ({v_type} volumes)-> {cost:.2f}€")
    print("-" * 80)


print("-" * 80)
print()
print("!!!Best solution!!!")
print("Used machines:")
for vmtype, count in best_vms_hybrid.items():
    if count > 0:
        print(
            f"{count} {vmtype} -> {int(sum(best_placement_hybrid[i][vmtype].value() for i in range(N)))} items"
        )

print(f"Used volume: {best_volume_hybrid}\n")
total_iops = sum(
    (t_r[i] + t_w[i] * RF) * s[i] * 10**6 / 2**10 / 16 for i in range(N)
)
allocated_iops = sum(
    best_placement_hybrid[i][vmtype].value()
    * (t_r[i] + t_w[i] * RF)
    * s[i]
    * 10**6
    / 2**10
    / 16
    for i in range(N)
    for vmtype in best_vms_hybrid.keys()
    if best_vms_hybrid[vmtype] > 0
)
allocated_band = sum(
    best_placement_hybrid[i][vmtype].value() * (t_r[i] + t_w[i] * RF) * s[i]
    for i in range(N)
    for vmtype in best_vms_hybrid.keys()
    if best_vms_hybrid[vmtype] > 0
)
# print("4" * 10, end="\n")
allocated_size = sum(
    best_placement_hybrid[i][vmtype].value() * s[i]
    for i in range(N)
    for vmtype in best_vms_hybrid.keys()
    if best_vms_hybrid[vmtype] > 0
)
# print("5" * 10, end="\n")
max_iops_vms = sum(
    vm_IOPS[vmtype] * number
    for vmtype, number in best_vms_hybrid.items()
    if best_vms_hybrid[vmtype] > 0
)
# print("6" * 10, end="\n")
max_band_vms = sum(
    vm_bandwidths[vmtype] * number
    for vmtype, number in best_vms_hybrid.items()
    if best_vms_hybrid[vmtype] > 0
)
max_iops_volumes = sum(
    max_volume_iops["gp2"] * number for number in best_vms_hybrid.values()
)

print("*" * 80, end="\n")
print("Non hybrid approach: cheapest 'single VM type' clusters per volume type")
print("*" * 80, end="\n")
best_vm_cassandra = dict()
best_n_cassandra = dict()
best_costs_cassandra = {vtype: np.inf for vtype in volume_types}
best_machines_standard = "Error"
best_machine_count_standard = 0
best_volume_standard = ""

best_cost_standard_overall = np.inf
for v_type in volume_types:
    n_vms_io = 0
    n_vms_band = 0
    n_volumes_band = 0
    n_volumes_io = 0
    n_size = 0
    for vmtype in vm_types:
        volumes_size = total_size * RF / max_storage
        vms_io = (
            round(
                sum(
                    (t_r[i] + t_w[i] * RF) * s[i] * 10**6 / 2**10 / 16
                    for i in range(N)
                ),
                4,
            )
            / vm_IOPS[vmtype]
        )
        vms_band = (
            round(sum((t_r[i] + t_w[i] * RF) * s[i] for i in range(N)), 4)
            / vm_bandwidths[vmtype]
        )
        volumes_io = (
            round(
                sum(
                    (t_r[i] + t_w[i] * RF) * s[i] * params.IO_FACTOR[v_type]
                    for i in range(N)
                ),
                4,
            )
            / max_volume_iops[v_type]
        )
        volumes_band = (
            round(sum((t_r[i] + t_w[i] * RF) * s[i] for i in range(N)), 4)
            / max_volume_bandwidths[v_type]
        )

        min_m = int(
            ceil(max(volumes_size, vms_io, vms_band, RF, volumes_band, volumes_io))
        )

        cost_only_cassandra = round(
            min_m * vm_costs[vmtype]
            # Cassandra volumes baseline charge
            + max_storage * min_m * cost_volume_storage[v_type]
            # Cassandra volumes IOPS charge
            + sum(
                (t_r[i] + t_w[i] * RF) * s[i] * params.IO_FACTOR[v_type]
                for i in range(N)
            )
            * 60
            * 60
            * cost_volume_iops[v_type]
            # Cassandra volumes performance charge
            + sum((t_r[i] + t_w[i] * RF) * s[i] for i in range(N))
            * 60
            * 60
            * cost_volume_tp[v_type],
            4,
        )
        if cost_only_cassandra < best_costs_cassandra[v_type]:
            best_costs_cassandra[v_type] = cost_only_cassandra
            best_vm_cassandra[v_type] = vmtype
            best_n_cassandra[v_type] = min_m
            n_vms_io = vms_io
            n_volumes_io = volumes_io
            n_vms_band = vms_band
            n_volumes_band = volumes_band
            n_size = volumes_size

    print(f"### Volume type: '{v_type}'")
    print(f"Min VMs due to VM IOPS: {n_vms_io}")
    print(f"Min VMs due to VM Bandwidth: {n_vms_band}")
    print(f"Min VMs due to Volume IOPS: {n_volumes_io}")
    print(f"Min VMs due to Volume Bandwidth: {n_volumes_band}")
    print(f"Min VMs due to Size: {n_size}")

    print(
        f"Best cost: {best_costs_cassandra[v_type]} €/h, "
        f"achieved with {best_n_cassandra[v_type]} machines "
        f"of type {best_vm_cassandra[v_type]}"
    )
    print("-" * 80)
    if best_costs_cassandra[v_type] < best_cost_standard_overall:
        best_cost_standard_overall = round(best_costs_cassandra[v_type], 4)
        best_volume_standard = v_type
        best_machines_standard = best_vm_cassandra[v_type]
        best_machine_count_standard = best_n_cassandra[v_type]

saving_amount = round(best_cost_standard_overall - best_cost_hybrid, 4)
saving_percent = 1 - round(best_cost_hybrid / best_cost_standard_overall, 4)
row = [
    N1,
    size_1,
    tot_throughput_1,
    skew_1,
    read_percent_1,
    N2,
    size_2,
    tot_throughput_2,
    skew_2,
    read_percent_2,
    best_machines_standard,
    best_machine_count_standard,
    best_volume_standard,
    round(saving_percent, 3),
]

if saving_amount > 0:
    print("COMPARISON with non-hybrid approach:")
    print(f"SOLVER: {best_cost_hybrid} <-> {best_cost_standard_overall}: MANUAL")
    print(
        f"Cost saving compared to best option: {saving_amount} €/h\n"
        f"Cost saving percentage: {saving_percent:.2%}"
    )
    with open("../hybridFiles.txt", "a") as file:
        file.write(
            f"{filename} -> {best_cost_hybrid/best_cost_standard_overall:.2%} ({best_volume_hybrid})\n"
        )

    # eventually append hybrid stuff to workloads
    for vm, n in best_vms_hybrid.items():
        if n != 0:
            row.append(vm)
            row.append(n)
    row.append(best_volume_hybrid)

# write all workload parameters and outcome in txt file to be parsed later
with open("../workloads.txt", "a") as file:
    file.write(" ".join([str(element) for element in row]))
    file.write("\n")

# Write placement in excel file
wb = Workbook()
filename = (
    f"../placements/"
    f"{N1}_"
    f"{size_for_filename1}_"
    f"{throughput_for_filename1}_"
    f"{skew_for_filename1}_"
    f"r{read_percent_filename1}_"
    f"{N2}_"
    f"{size_for_filename2}_"
    f"{throughput_for_filename2}_"
    f"{skew_for_filename2}_"
    f"r{read_percent_filename2}.xlsx"
)
os.system(f"touch {filename}")
ws = wb.active
ws.title = "Items"
ws.append(
    [
        "ID",
        "Size [MB]",
        "Throughput Read [OPS/s]",
        "Throughput Write [OPS/s]",
        "Required Bandwidth",
        "Placement",
    ]
)
for i in range(N):
    row = [i, s[i], t_r[i], t_w[i], t_r[i] + t_w[i] * RF * s[i]]
    for vm in vm_types:
        if best_placement_hybrid[i][vm].value() != 0:
            row.append(vm)
    ws.append(row)
wb.save(filename=filename)

tot_time = time() - t0
print(f"Took {tot_time:.2f} seconds ")

sys.stdout.close()


sys.stdout = sys.__stdout__
