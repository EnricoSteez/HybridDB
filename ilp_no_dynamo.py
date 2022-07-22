from math import ceil
import os
from openpyxl import Workbook
import pulp as pulp
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


def generate_items(distribution, skew=1.0, custom_size=0.1, max_throughput=20000.0):
    # ycsb: constant 100KB sizes = 0.1MB, zipfian throughputs
    # uniform: everything uniformely distribuetd
    # custom: sizes from ibm traces, throughputs from YCSB
    # if distribution == "ycsb":
    #     s = [custom_size] * N
    #     t_r = gather_throughputs("readStats.txt", scale)
    #     t_w = gather_throughputs("writeStats.txt", scale)

    # elif distribution == "uniform":
    #     # uniform distribution
    #     # max size for DynamoDB is 400KB = 0.4MB
    #     s = list((0.4 - 1) * np.random.rand(N) + 1)  # size in MB
    #     t_r = np.random.rand(N) * 500 * scale
    #     t_w = np.random.rand(N) * 500 * scale

    # # sizes are IBM, throughputs are YCSB
    # elif distribution == "custom":
    #     s = gather_sizes_ibm()
    #     t_r = gather_throughputs("readStats.txt", scale)
    #     t_w = gather_throughputs("writeStats.txt", scale)

    # elif distribution == "java":
    #     s, t_r, t_w = gather_data_java(scale)
    # elif distribution == "zipfian":
    s = [custom_size] * N
    t_r = []
    t_w = []
    with open(f"zipfian/{N}_{int(skew)}", "r") as file:
        for _ in range(N):
            prob = float(file.readline().split()[0])
            t_r.append(prob * max_throughput * read_percent)
            t_w.append(prob * max_throughput * write_percent)

    print(
        f"Number of items: {len(s)}, max_size={max(s)}MB, min_size={min(s)}MB\n"
        f"{distribution.capitalize()} distribution, skew={skew}\n"
        f"throughput read: max={max(t_r):.2e}, min={min(t_r):.2e}\n"
        f"throughput write: max={max(t_w):.2e}, min={min(t_w):.2e}\n"
        f"Access ratio: {read_percent:.0%} reads | {write_percent:.0%} writes"
    )
    # print(s)
    # print("SEPARATOR")
    # print(t_r)
    # print("SEPARATOR")
    # print(t_w)
    # print("SEPARATOR")
    return s, t_r, t_w


def extract_type_name(machine_counts):
    for i in range(len(machine_counts)):
        if machine_counts[i].value() != 0:
            return vm_types[i]
    return None


if len(sys.argv) != 7:
    sys.exit(
        f"Usage: python3 {path.basename(__file__)} <N> <items_size [MB]> <tot_throughput> "
        f"<uniform|ycsb|custom|java|zipfian> <skew> <read %>"
    )
try:
    N = int(sys.argv[1])
    custom_size = float(sys.argv[2])
    max_throughput = float(sys.argv[3])
    skew = float(sys.argv[5])
    read_percent = float(sys.argv[6])
    write_percent = 1 - read_percent
except ValueError:
    sys.exit("N, items_size, max_throughput and TPscaling must be numbers")

dist = sys.argv[4]
size_for_filename = str(custom_size)
throughput_for_filename = str(max_throughput)
skew_for_filename = str(skew)
read_percent_filename = str(read_percent)
# if integer, remove .0 else replace dot with comma
if custom_size.is_integer():
    size_for_filename = size_for_filename[:-2]
else:
    size_for_filename = size_for_filename.replace(".", ",")
if max_throughput.is_integer():
    throughput_for_filename = throughput_for_filename[:-2]
else:
    throughput_for_filename = throughput_for_filename.replace(".", ",")
if skew.is_integer():
    skew_for_filename = skew_for_filename[:-2]
else:
    skew_for_filename = skew_for_filename.replace(".", ",")

# this one is always decimal
read_percent_filename = read_percent_filename.replace(".", ",")

filename = f"../results/{N}_{size_for_filename}_{throughput_for_filename}_{skew_for_filename}_r{read_percent_filename}.txt"
allowed_dists = ["ycsb", "uniform", "custom", "java", "zipfian"]
if dist not in allowed_dists:
    raise ValueError(f'Distribution: "{dist}" is not allowed')

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
v = pulp.LpVariable.dicts(
    "Number of used volumes per type",
    indices=volume_types,
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
s, t_r, t_w = generate_items(
    distribution=dist,
    skew=skew,
    custom_size=custom_size,
    max_throughput=max_throughput,
)
total_size = sum(s)
num_vms = len(vm_types)
solver = pulp.getSolver("GUROBI_CMD")
best_cost_hybrid = np.inf
best_vms_hybrid = dict()
best_placement_hybrid = dict()
best_volume_hybrid = ""

t0 = time()

total_iops = sum(
    (t_r[i] + t_w[i] * RF) * s[i] * 10**6 / 2**10 / 16 for i in range(N)
)
total_band = sum((t_r[i] + t_w[i] * RF) * s[i] for i in range(N))
print()
print("-" * 80)
print(f"Total IOPS: {total_iops:.3f} IO/s")
print(f"Total BANDWIDTH: {total_band:.3f}MB/s")
print(f"Total SIZE: {total_size}")
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
        #  Ensure that:
        #  sum(x[:][vmtype])==0 <--> m[vmtype]==0
        #  sum(x[:][vmtype])>0 <--> m[vmtype]>=RF
        # ---------########## ENSURE THAT sum(x[:][vmtype])==0 <--> m[vmtype]==0 ##########----------
        # introduce binary delta: {lpSum(x[i][vmtype].value() for i in range(N))} == 0 <--> d==0 | d==1
        # these are fixing d
        problem += lpSum(x[i][vmtype] for i in range(N)) >= -M * (1 - d[vmtype])
        problem += lpSum(x[i][vmtype] for i in range(N)) <= M * d[vmtype]
        # These two are binding the number of machines to d
        problem += m[vmtype] <= M * d[vmtype]
        problem += m[vmtype] >= RF - M * (1 - d[vmtype])

    result = problem.solve(solver)
    cost = problem.objective.value()
    allocated_iops = dict()
    allocated_size = dict()
    allocated_band = dict()
    max_iops_vms = dict()
    max_band_vms = dict()
    print("*" * 20, end="")
    print(f" {v_type} ",end="")
    print("*" * 20)
    for vm in vm_types:
        allocated_iops[vm] = sum(
            x[i][vm].value() * (t_r[i] + t_w[i] * RF) * s[i] * 10**6 / 2**10 / 16
            for i in range(N)
        )
        allocated_band[vm] = sum(
            x[i][vm].value() * (t_r[i] + t_w[i] * RF) * s[i] for i in range(N)
        )
        allocated_size[vm] = sum(x[i][vm].value() * s[i] for i in range(N))
        max_iops_vms[vm] = vm_IOPS[vm] * m[vm].value()
        max_band_vms[vm] = vm_bandwidths[vm] * m[vm].value()
    # tot IOPS available from volumes
    max_iops_volumes = (
        max_volume_iops[v_type]
        * params.IO_FACTOR[v_type]
        * sum(m[vm].value() for vm in vm_types)
    )
    # tot bandwidth available from volumes
    max_band_volumes = (
        max_volume_bandwidths[v_type]
        * sum(m[vm].value() for vm in vm_types)
        * 2**20
        / 10**6
    )  # volumes band is in MiB -> convert to MB
    for vm in vm_types:
        if m[vm].value() > 0:
            print(f"***** {m[vm].value()} {vm} *****")
            print(
                f"Solver allocated {allocated_iops[vm]:.2f} IOPS, "
                f"these MACHINES provide max {max_iops_vms[vm]:.2f} IOPS"
            )
            print(
                f"Solver allocated {allocated_band[vm]:.2f} MB/s "
                f"out of {total_band:.2f}, these MACHINES provide "
                f"max {max_band_vms[vm]:.3f} MB/s "
            )

    print(
        f"Solver allocated {sum(allocated_iops[vm] for vm in vm_types):.2f}MB/s, "
        f"VOLUMES provide max {max_iops_volumes:.2f} MB/s "
    )
    print(
        f"Solver allocated {sum(allocated_iops[vm] for vm in vm_types):.2f}IOPS, "
        f"VOLUMES provide max {max_iops_volumes:.2f} IOPS"
    )
    print(
        f"Solver allocated {sum(allocated_size[vm] for vm in vm_types):.2f}MB in total, "
        f"VOLUMES provide max {params.MAX_SIZE} MB"
    )
    iops_sat_vm = sum(allocated_iops[vm] for vm in vm_types) / sum(
        vm_IOPS[vm] * m[vm].value() for vm in vm_types
    )
    iops_sat_vol = sum(allocated_iops[vm] for vm in vm_types) / max_iops_volumes
    band_sat_vm = sum(allocated_band[vm] for vm in vm_types) / sum(
        vm_bandwidths[vm] * m[vm].value() for vm in vm_types
    )
    band_sat_vol = sum(allocated_band[vm] for vm in vm_types) / max_band_volumes
    size_sat_vol = sum(allocated_size[vm] for vm in vm_types) / (
        params.MAX_SIZE * sum(m[vm].value() for vm in vm_types)
    )
    print(f"IOPS SATURATION (VMs): {iops_sat_vm:.2%}")
    print(f"IOPS SATURATION (Volumes): {iops_sat_vol:.2%}")
    print(f"BANDWIDTH SATURATION (VMs): {band_sat_vm:.2%}")
    print(f"BANDWIDTH SATURATION (Volumes): {band_sat_vol:.2%}")
    print(f"SIZE SATURATION (Volumes): {size_sat_vol:.2%}")
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
row = [N, custom_size, max_throughput, skew, read_percent]
print("!!!Best solution!!!")
print("Used machines:")
for vmtype, count in best_vms_hybrid.items():
    if count > 0:
        print(
            f"{count} {vmtype} -> {int(sum(best_placement_hybrid[i][vmtype].value() for i in range(N)))} items"
        )
print(f"Used volume:{best_volume_hybrid}")

print("*" * 80, end="\n")
print("Non hybrid approach: cheapest 'single VM type' clusters per volume type")
print("*" * 80, end="\n")
best_vm_cassandra = dict()
best_n_cassandra = dict()
best_costs_cassandra = {vtype: np.inf for vtype in volume_types}
best_machines_standard = "Error"
best_machine_count_standard = 0

best_cost_standard_overall = np.inf
for v_type in volume_types:
    for vmtype in vm_types:
        vms_size = total_size * RF / max_storage
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
            * 10**6
            / 2**20
            / max_volume_bandwidths[v_type]
        )

        min_m = int(ceil(max(vms_size, vms_io, vms_band, RF, volumes_band, volumes_io)))

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

    print(f"### Volume type: '{v_type}'")
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
    N,
    custom_size,
    max_throughput,
    skew,
    read_percent,
    best_machines_standard,
    best_machine_count_standard,
    round(saving_percent, 3),
]

if saving_amount > 0:
    print("COMPARISON with non-hybrid approach:")
    print(f"SOLVER: {best_cost_hybrid} <-> {best_cost_standard_overall}: MANUAL")
    print(
        f"Cost saving compared to best option: {saving_amount} €/h\n"
        f"Cost saving percentage: {saving_percent:.2%}"
    )
    with open("../results/hybridFiles.txt", "a") as file:
        file.write(f"{filename} -> {best_cost_hybrid/best_cost_standard_overall:.2%}\n")

    for vm, n in best_vms_hybrid.items():
        if n != 0:
            row.append(vm)
            row.append(n)

# write workload parameters and outcome in txt file to be parsed later
with open("../results/workloads.txt", "a") as file:
    file.write(" ".join([str(element) for element in row]))
    file.write("\n")

# Write placement in excel file
wb = Workbook()
filename = (
    f"../placements/{N}"
    f"_{size_for_filename}_"
    f"{throughput_for_filename}"
    f"_{skew_for_filename}"
    f"_r{read_percent_filename}.xlsx"
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
