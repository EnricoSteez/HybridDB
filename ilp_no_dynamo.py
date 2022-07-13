from math import ceil
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
        f"{distribution} distribution, skew={skew}\n"
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

# this one is always decimal ehehe
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
t0 = time()
best_cost_hybrid = np.inf
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
        problem += (
            lpSum(
                [
                    x[i][vmtype]
                    * (t_r[i] + t_w[i] * RF)
                    * s[i]
                    * 10 ** 6
                    / 2 ** 10
                    / 16
                    for i in range(N)
                ]
            )
            <= m[vmtype] * vm_IOPS[vmtype]
        )
        # MAX IOPS per volume
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
        problem += (
            lpSum([x[i][vmtype] * (t_r[i] + t_w[i] * RF) * s[i] for i in range(N)])
            <= m[vmtype] * vm_bandwidths[vmtype]
        )
        problem += (
            lpSum([x[i][vmtype] * (t_r[i] + t_w[i] * RF) * s[i] for i in range(N)])
            * 10 ** 6
            / 2 ** 20
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
    cost = round(problem.objective.value(), 2)
    if cost < best_cost_hybrid:
        best_cost_hybrid = cost
        best_placement_hybrid = x
        best_volume_hybrid = v_type
        best_vms_hybrid = {vmtype: m[vmtype].value() for vmtype in vm_types}

    print(f"HYBRID COST ({v_type} volumes)-> {cost}€")

print("!!!Best solution!!!")
print("Used machines:")
for vmtype in vm_types:
    items = sum(best_placement_hybrid[i][vmtype].value() for i in range(N))
    if items > 0:
        print(f"{best_vms_hybrid[vmtype]} {vmtype} -> {int(items)} items")

print(f"Used volume: {best_volume_hybrid}\n")

print("*" * 80, end="\n")
print("Non hybrid approach: cheapest 'single VM type' clusters per volume type")
best_vm_cassandra = dict()
best_n_cassandra = dict()
best_costs_cassandra = {vtype: np.inf for vtype in volume_types}

best_cost_standard_overall = np.inf
for volumetype in volume_types:
    for vmtype in vm_types:
        vms_size = total_size * RF / max_storage
        vms_io = (sum(t_r) + sum(t_w) * RF) / vm_IOPS[vmtype]
        vms_band = (
            sum((t_r[i] + t_w[i] * RF) * s[i] for i in range(N)) / vm_bandwidths[vmtype]
        )

        min_m = int(ceil(max(vms_size, vms_io, vms_band, RF)))

        cost_only_cassandra = (
            min_m * vm_costs[vmtype]
            # Cassandra volumes baseline charge
            + max_storage * min_m * cost_volume_storage[volumetype]
            # Cassandra volumes IOPS charge
            + sum(
                (t_r[i] + t_w[i] * RF) * s[i] * params.IO_FACTOR[volumetype]
                for i in range(N)
            )
            * 60
            * 60
            * cost_volume_iops[volumetype]
            # Cassandra volumes performance charge
            + sum((t_r[i] + t_w[i] * RF) * s[i] for i in range(N))
            * 60
            * 60
            * cost_volume_tp[volumetype]
        )
        if cost_only_cassandra < best_costs_cassandra[volumetype]:
            best_costs_cassandra[volumetype] = cost_only_cassandra
            best_vm_cassandra[volumetype] = vmtype
            best_n_cassandra[volumetype] = min_m

    print(f"### Volume type: '{volumetype}'")
    print(
        f"Best cost: {best_costs_cassandra[volumetype]:.2f}€/h, "
        f"achieved with {best_n_cassandra[volumetype]} machines "
        f"of type {best_vm_cassandra[volumetype]}"
    )
    print("-" * 80)
    if best_costs_cassandra[volumetype] < best_cost_standard_overall:
        best_cost_standard_overall = best_costs_cassandra[volumetype]
        best_volume_standard = volumetype
        best_machines_standard = best_vm_cassandra[volumetype]
        best_machine_count_standard = best_n_cassandra[volumetype]

best_cost_standard_overall = round(best_cost_standard_overall, 2)
# here they are both rounded to 2 decimals in the same way
if best_cost_hybrid != best_cost_standard_overall:
    print("COMPARISON with non-hybrid approach:")
    print(
        f"Cost saving compared to best option: {best_cost_standard_overall - best_cost_hybrid} €/h\n"
        f"Cost saving percentage: {best_cost_hybrid/best_cost_standard_overall:.2%}"
    )
    with open("../results/hybridScenarios.txt", "a") as file:
        file.write(f"{filename} -> {best_cost_hybrid/best_cost_standard_overall:.2%}\n")

tot_time = time() - t0
print(f"Took {tot_time:.2f} seconds ")

sys.stdout.close()
sys.stdout = sys.__stdout__
