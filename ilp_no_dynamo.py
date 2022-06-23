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


def notify(message):
    with open("./keys/keys.json", "r") as keys_file:
        k = json.load(keys_file)
        token = k["telegram_token"]
        chat_id = k["telegram_chat_id"]
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=message)


def generate_items(distribution, skew=1.0, custom_size=0.1, max_throughput=20000):
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
        for i in range(N):
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

filename = f"results/{N}_{size_for_filename}_{throughput_for_filename}_{skew_for_filename}_r{read_percent_filename}.txt"
allowed_dists = ["ycsb", "uniform", "custom", "java", "zipfian"]
if dist not in allowed_dists:
    raise ValueError(f'Distribution: "{dist}" is not allowed')

sys.stdout = open(filename, "w")

items = [i for i in range(N)]

# Placement vector x
x = pulp.LpVariable.dicts(
    "Placement", indices=(items, vm_types), cat=constants.LpBinary
)

m = pulp.LpVariable.dicts(
    "Type of machine used",
    indices=vm_types,
    cat=constants.LpBinary,
)

z = pulp.LpVariable.dicts(
    "m outside of 0..RF interval",
    indices=vm_types,
    cat=constants.LpBinary,
)

d = pulp.LpVariable.dicts(
    "Ensure feasiblity between number of machines and placement",
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


# Optimization Problem
problem = pulp.LpProblem("ItemsPlacement", pulp.LpMinimize)

# objective function
problem += (
    lpSum([m[vmtype] * vm_costs[vmtype] for vmtype in vm_types])
    + lpSum([m[vmtype] for vmtype in vm_types]) * max_storage * cost_volume_storage
    + lpSum([t_r[i] + t_w[i] * RF for i in range(N)]) * 60 * 60 * cost_volume_iops
    + lpSum([(t_r[i] + t_w[i] * RF) * s[i] for i in range(N)]) * 60 * 60 * cost_volume_tp,
    "Minimization of the total cost of the hybrid solution",
)

# constraints
# at least RF machines in total
problem += lpSum([m[vmtype] for vmtype in vm_types]) >= RF

# --------------------########## ENOUGH STORAGE (COMBINED) ##########--------------------
problem += max_storage * lpSum([m[vmtype] for vmtype in vm_types]) >= total_size * RF

# --------------------########## EVERY ITEM IS PLACED IN ONLY ONE MACHINE TYPE ##########--------------------
for i in range(N):
    problem += lpSum([x[i][vmtype] for vmtype in vm_types]) == 1

# --------------------########## ENOUGH IOPS ##########--------------------
for vmtype in vm_types:
    problem += lpSum(
        [x[i][vmtype] * (t_r[i] + t_w[i] * RF) for i in range(N)]
    ) <= m[vmtype] * vm_IOPS[vmtype]
    # --------------------########## ENOUGH BANDWIDTH ##########--------------------
    problem += lpSum(
        [x[i][vmtype] * (t_r[i] * t_w[i] * RF) * s[i] for i in range(N)]
    ) <= m[vmtype] * vm_bandwidths[vmtype]

    # ---------########## ENSURE THAT sum(x[:][vmtype])>0 <--> m[vmtype]>0 ##########----------
    # introduce binary delta: {lpSum(x[i][vmtype] for i in range(N))} == 0 <--> d==0 | d==1
    # # these are fixing d
    # problem += lpSum(x[i][vmtype] for i in range(N)) >= -M * (1 - d[vmtype])
    # problem += lpSum(x[i][vmtype] for i in range(N)) <= M * d[vmtype]
    # These two are binding the number of machines to d
    # problem += m[vmtype] <= M * d[vmtype]
    # problem += m[vmtype] >= RF - M * (1 - d[vmtype])


result = problem.solve(solver)
cost_hybrid = round(problem.objective.value(), 2)
print(f"HYBRID COST -> {cost_hybrid}€")
placement = [x[i][vmtype].value() for i in range(N) for vmtype in vm_types]

print("Used machines:")
for vmtype in vm_types:
    tot_items = sum(x[i][vmtype] for i in range(N))
    if tot_items > 0:
        print(f"{vmtype} -> {tot_items} items", end=",")
print()

# *** *** *** *** *** *** *** *** Allocated items *** *** *** *** *** *** *** ***
clustersizes = [
    sum(placement[i][vmtype] * s[i] * RF for i in range(N)) for vmtype in vm_types
]
iops = [
    sum(placement[i][vmtype] * (t_r[i] + t_w[i] * RF) for i in range(N))
    for vmtype in vm_types
]
bandwidths = [
    sum(placement[i][vmtype] * (t_r[i] + t_w[i] * RF) * s[i] for i in range(N))
    for vmtype in vm_types
]
# *** *** *** *** *** *** *** *** Availabilities *** *** *** *** *** *** *** ***
available_space_per_cluster = [
    max_storage * m[vmtype].value() for vmtype in vm_types
]
available_iops_per_cluster = [
    vm_IOPS[vmtype] * m[vmtype].value() for vmtype in vm_types
]
available_bandwidth_per_cluster = [
    vm_bandwidths[vmtype] * m[vmtype].value() for vmtype in vm_types
]

# *** *** *** *** *** *** *** *** Costs *** *** *** *** *** *** *** ***
cost_vms_per_cluster = [m[vmtype] * vm_costs[vmtype] for vmtype in vm_types]
cost_volume_per_cluster = [
    max_storage * m[vmtype].value() * cost_volume_storage for vmtype in vm_types
]  # cost per provisioned MB (MAX SIZE per VM allocated and paid for)

cost_iops_per_cluster = np.dot(iops, 60 * 60 * cost_volume_iops)  # cost IOPS
cost_bandwidth_per_cluster = np.dot(
    bandwidths, 60 * 60 * cost_volume_iops
)  # cost bandwidth

cost_per_cluster = sum(
    cost_vms_per_cluster
    + cost_volume_per_cluster
    + cost_iops_per_cluster
    + cost_bandwidth_per_cluster
)


print("-" * 80)

best_cost_cassandra = np.inf
for mt in range(num_machines):
    vms_size = total_size * RF / max_storage
    vms_io = (sum(t_r) + sum(t_w) * RF) / vm_IOPS[mt]
    vms_band = sum((t_r[i] + t_w[i] * RF) * s[i] for i in range(N)) / vm_bandwidths[mt]

    min_m = int(ceil(max(vms_size, vms_io, vms_band, 3)))

    cost_only_cassandra = (
        min_m * vm_costs[mt]
        # Cassandra volumes baseline charge
        + max_storage * min_m * cost_volume_storage
        # Cassandra volumes IOPS charge
        + (sum(t_r) + sum(t_w) * RF) * 60 * 60 * cost_volume_iops
        # Cassandra volumes performance charge
        + sum((t_r[i] + t_w[i] * RF) * s[i] for i in range(N))
        * 60
        * 60
        * cost_volume_tp
    )
    if cost_only_cassandra < best_cost_cassandra:
        best_cost_cassandra = cost_only_cassandra
        only_cassandra_vms = min_m * vm_costs[mt]
        only_cassandra_volume = max_storage * min_m * cost_volume_storage
        only_cassandra_iops = (sum(t_r) + sum(t_w) * RF) * 60 * 60 * cost_volume_iops
        only_cassandra_band = (
            sum((t_r[i] + t_w[i] * RF) * s[i] for i in range(N))
            * 60
            * 60
            * cost_volume_tp
        )
        best_vm_cassandra = mt
        best_n_cassandra = min_m
        best_vms_size = vms_size
        best_vms_io = vms_io
        best_vms_band = vms_band

best_cost_cassandra = round(best_cost_cassandra, 2)
print("COMPARISON with non-hybrid approach:")
print(
    f"Cost of only CASSANDRA: {best_cost_cassandra:.2f}€/h, "
    f"achieved with {best_n_cassandra} machines "
    f"of type {vm_types[best_vm_cassandra]}\n"
    f"(min machines due to size: {best_vms_size:.3f} (->{ceil(best_vms_size)}))\n"
    f"(min machines due to iops: {best_vms_io:.3f} (->{ceil(best_vms_io)}))\n"
    f"(min machines due to bandwidth: {best_vms_band:.3f} (->{ceil(best_vms_band)}))"
)
print("-" * 80)

if cost_hybrid != best_cost_cassandra:
    print(
        f"Cost saving compared to best option: {best_cost_cassandra - cost_hybrid} €/h\n"
        f"Cost saving percentage: {cost_hybrid/best_cost_cassandra:.2%}"
    )
    with open("results/hybridScenarios.txt", "a") as file:
        file.write(f"{filename} -> {cost_hybrid/best_cost_cassandra:.2%}\n")

tot_time = time() - t0
print(f"Took {tot_time:.2f} seconds ")

sys.stdout.close()
sys.stdout = sys.__stdout__
