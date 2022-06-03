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
        f"throughput read: max={max(t_r)}, min={min(t_r)}\n"
        f"throughput write: max={max(t_w)}, min={min(t_w)}\n"
        f"Access ratio: {read_percent:.0%} reads | {write_percent:.0%} writes"
    )
    # print(s)
    # print("SEPARATOR")
    # print(t_r)
    # print("SEPARATOR")
    # print(t_w)
    # print("SEPARATOR")
    return s, t_r, t_w


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

filename = (
    f"results/{N}_{size_for_filename}_{throughput_for_filename}_{skew_for_filename}.txt"
)
allowed_dists = ["ycsb", "uniform", "custom", "java", "zipfian"]
if dist not in allowed_dists:
    raise ValueError(f'Distribution: "{dist}" is not allowed')

sys.stdout = open(filename, "w")

items = [i for i in range(N)]
placements = [j for j in range(len(vm_types) + 1)]

# Placement vector x
x = pulp.LpVariable.dicts(
    "Placement",
    indices=(items, placements),
    cat=constants.LpInteger,
    lowBound=0,
    upBound=1,
)

m = pulp.LpVariable.dicts(
    "Number of machines per type",
    indices=[i for i in range(len(vm_types))],
    cat=constants.LpInteger,
)
z = pulp.LpVariable.dicts(
    "Binary variables for m outside of 0..RF interval",
    indices=[i for i in range(len(vm_types))],
    cat=constants.LpBinary,
)

# sizes in MB, throughputs in ops/s
s, t_r, t_w = generate_items(
    distribution=dist,
    skew=skew,
    custom_size=custom_size,
    max_throughput=max_throughput,
)
t0 = time()
solver = pulp.getSolver("GUROBI_CMD")

# Optimization Problem
problem = pulp.LpProblem("ItemsPlacement", pulp.LpMinimize)

# objective function
problem += (
    lpSum([x[i][0] * s[i] for i in range(N)]) * cost_storage
    + lpSum([x[i][0] * t_r[i] * (s[i] * 1000 / 8) for i in range(N)])
    * 60
    * 60
    * cost_read
    + lpSum([x[i][0] * s[i] * 1000 * t_w[i] for i in range(N)]) * 60 * 60 * cost_write
    + lpSum([m[i] * vm_costs[i] for i in range(len(vm_types))])
    + params.MAX_SIZE
    * lpSum([m[i] for i in range(len(vm_types))])
    * cost_volume_storage
    + lpSum(
        x[i][j] * (t_r[i] + t_w[i] * RF)
        for i in range(N)
        for j in range(1, len(vm_types) + 1)
    )
    * 60
    * 60
    * cost_volume_iops
    + lpSum(
        x[i][j] * (t_r[i] + t_w[i] * RF) * s[i]
        for i in range(N)
        for j in range(1, len(vm_types) + 1)
    )
    * 60
    * 60
    * cost_volume_tp,
    "Minimization of the total cost of the hybrid solution",
)

# constraints

for j in range(1, len(vm_types) + 1):
    # --------------------########## ENOUGH MEMORY ##########--------------------
    # per each VM type, sum of all the items in that sub-cluster <= max_size * VMs(of that type)
    problem += (
        lpSum([x[i][j] * s[i] for i in range(N)]) * RF <= params.MAX_SIZE * m[j - 1]
    )

    # assuming WRITE ALL, READ ANY CONSISTENCY
    # --------------------########## ENOUGH IOPS ##########--------------------
    problem += (
        lpSum([x[i][j] * (t_r[i] + t_w[i] * RF) for i in range(N)])
        <= m[j - 1] * vm_IOPS[j - 1]
    )

    # --------------------########## ENOUGH BANDWIDTH ##########--------------------
    problem += (
        lpSum([x[i][j] * (t_r[i] + t_w[i] * RF) * s[i] for i in range(N)])
        <= m[j - 1] * vm_bandwidths[j - 1]
    )

    # --------------------########## EITHER VMs=0 OR VMs>=RF (PER TYPE), linearization ##########--------------------
    problem += m[j - 1] >= RF * z[j - 1]
    problem += m[j - 1] <= 1e5 * z[j - 1]

# --------------------########## ONLY ONE PLACEMENT ##########--------------------
for i in range(N):
    problem += lpSum([x[i][j] for j in range(len(vm_types) + 1)]) == 1
    # problem += x[i][0] == 1

result = problem.solve(solver)
print(f"HYBRID COST -> {problem.objective.value():.2f}€")
placement = np.ndarray((N, len(vm_types) + 1), dtype=int)
for i in range(N):
    for j in range(len(vm_types) + 1):
        placement[i][j] = x[i][j].value()

items_cassandra = placement[:, 1:].sum()  # all IaaS columns
items_dynamo = placement[:, 0].sum()  # only first column
print(
    f"Tot items on Cassandra: {int(items_cassandra)}\n"
    f"Tot items on Dynamo: {int(items_dynamo)}"
)

# cost of Dynamo
# 1 read unit every 8 KB (multiply the iops by size[MB]*1000/8)
# 1 write unit every KB (multiply the iops by the size[MB]*1000 to obtain the units)
cost_dynamo_storage = sum(placement[i][0] * s[i] for i in range(N)) * cost_storage
cost_dynamo_reads = (
    sum(placement[i][0] * (s[i] * 1000 / 8) * t_r[i] for i in range(N))
    * 60
    * 60
    * cost_read
)
cost_dynamo_writes = (
    sum(placement[i][0] * (s[i] * 1000) * t_w[i] for i in range(N))
    * 60
    * 60
    * cost_write
)

cost_dynamo = cost_dynamo_storage + cost_dynamo_reads + cost_dynamo_writes
print(
    f"Cost of Dynamo storage (hybrid) = {cost_dynamo_storage:.2f}€/h\n"
    f"Cost of Dynamo reads (hybrid) = {cost_dynamo_reads:.2f}€/h\n"
    f"Cost of Dynamo writes (hybrid) = {cost_dynamo_writes:.2f}€/h\n"
    f"Total Cost of Dynamo (hybrid) = {cost_dynamo:.2f}€/h"
)
tot_vms = sum(m[j].value() for j in range(len(vm_types)))

size_cassandra = sum(placement[i, 1:].sum() * s[i] for i in range(N)) * RF
iops_cassandra = sum(placement[i, 1:].sum() * (t_r[i] + t_w[i] * RF) for i in range(N))
mbs_cassandra = sum(
    sum(placement[i, 1:]) * (t_r[i] + t_w[i] * RF) * s[i] for i in range(N)
)
tot_size = sum(s)
tot_iops = sum(t_r[i] + t_w[i] * RF for i in range(N))
tot_mbs = sum((t_r[i] + t_w[i] * RF) * s[i] for i in range(N))
available_size = params.MAX_SIZE * tot_vms
available_iops = sum(m[j].value() * vm_IOPS[j] for j in range(len(vm_types)))
available_bandwidth = sum(m[j].value() * vm_bandwidths[j] for j in range(len(vm_types)))


cost_cassandra = (
    sum(m[j].value() * vm_costs[j] for j in range(len(vm_types)))  # cost VMs
    + params.MAX_SIZE * tot_vms * cost_volume_storage  # cost provisioned MB
    + iops_cassandra * 60 * 60 * cost_volume_iops  # cost IOPS
    + mbs_cassandra * 60 * 60 * cost_volume_tp  # cost band
)

print(f"Cost of Cassandra (hybrid) = {cost_cassandra:.2f}€/h\n")
if tot_vms != 0 and iops_cassandra != 0 and size_cassandra != 0 and mbs_cassandra != 0:
    cassandra_storage_saturation = size_cassandra / available_size
    cassandra_iops_saturation = iops_cassandra / available_iops
    cassandra_bandwidth_saturation = mbs_cassandra / available_bandwidth

    print(
        f"IOPS saturation of the whole cluster: {cassandra_iops_saturation:.2%}\n"
        f"Bandwidth saturation of the whole cluster: {cassandra_bandwidth_saturation:.2%}\n"
        f"Storage saturation: {size_cassandra:.2f}MB allocated / {params.MAX_SIZE * tot_vms:.2f}MB available ({cassandra_storage_saturation:.2%})\n"
    )

print("Machines in use:")
for j in range(len(vm_types)):
    print(f"{int(m[j].value())} {vm_types[j]}")

print("-" * 80)

best_cost_cassandra = np.inf
for mt in range(len(vm_types)):
    vms_size = tot_size * RF / params.MAX_SIZE
    vms_io = (sum(t_r) + sum(t_w) * RF) / vm_IOPS[mt]
    vms_band = sum((t_r[i] + t_w[i] * RF) * s[i] for i in range(N)) / vm_bandwidths[mt]

    min_m = int(ceil(max(vms_size, vms_io, vms_band, 3)))

    cost_only_cassandra = (
        min_m * vm_costs[mt]
        # Cassandra volumes baseline charge
        + params.MAX_SIZE * min_m * cost_volume_storage
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
        best_vm_cassandra = mt
        best_n_cassandra = min_m
        best_vms_size = vms_size
        best_vms_io = vms_io
        best_vms_band = vms_band

print("COMPARISON with non-hybrid approaches:")
# COST OF NON-HYBRID SOLUTIONS
cost_dynamo = (
    tot_size * cost_storage
    + sum((s[i] * 1000 / 8) * t_r[i] for i in range(N)) * 60 * 60 * cost_read
    + sum(s[i] * 1000 * t_w[i] for i in range(N)) * 60 * 60 * cost_write
)

print(f"Cost of only DYNAMO: {cost_dynamo:.2f}€/h")

print(
    f"Cost of only CASSANDRA: {best_cost_cassandra:.2f}€/h, "
    f"achieved with {best_n_cassandra} machines "
    f"of type {vm_types[best_vm_cassandra]}\n"
    f"(min machines due to size: {best_vms_size} (->{ceil(best_vms_size)}))\n"
    f"(min machines due to iops: {best_vms_io} (->{ceil(best_vms_io)}))\n"
    f"(min machines due to bandwidth: {best_vms_band} (->{ceil(best_vms_band)}))\n"
)
print("-" * 80)
best_no_hybrid = min(cost_dynamo, best_cost_cassandra)
cost_hybrid = problem.objective.value()
saving = best_no_hybrid - cost_hybrid
print(f"Cost saving compared to best option: {saving/best_no_hybrid:.2%} €/h")
if saving != 0:
    print(f"Cost savinf percentage: {saving/best_no_hybrid:.2f}")
    with open("results/hybridScenarios.txt", "wa") as file:
        file.write(f"{filename} -> {saving/best_no_hybrid:.2%}\n")

tot_time = time() - t0
print(f"Took {tot_time:.2f} seconds ")

sys.stdout.close()
sys.stdout = sys.__stdout__

# message = (
#     f"N = {N},\n"
#     f"Diverse cluster\n"
#     f"Optimisation took: {strftime('%H:%M:%S',gmtime(tot_time))}\n"
#     f"See {filename} for detailed info"
# )
# threading.Thread(target=notify(message=message)).start()

# with open("placement", "wb") as file:
#     for num in best_placement:
#         file.write(bytes([int(num)]))

# system("pmset sleepnow")
