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
x = pulp.LpVariable.dicts("Placement", indices=items, cat=constants.LpBinary)

m1 = pulp.LpVariable.dicts(
    "Number of machines used in cluster 1",
    indices=[i for i in range(num_machines)],
    cat=constants.LpInteger,
)
m2 = pulp.LpVariable.dicts(
    "Number of machines used in cluster 2",
    indices=[i for i in range(num_machines)],
    cat=constants.LpInteger,
)

z1 = pulp.LpVariable.dicts(
    "Binary variables of m1 outside of 0..RF interval",
    indices=[i for i in range(num_machines)],
    cat=constants.LpBinary,
)
z2 = pulp.LpVariable.dicts(
    "Binary variables of m2 outside of 0]..[RF interval",
    indices=[i for i in range(num_machines)],
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
len(vm_types)
solver = pulp.getSolver("GUROBI_CMD")
t0 = time()

# Optimization Problem
problem = pulp.LpProblem("ItemsPlacement", pulp.LpMinimize)

# objective function
problem += (
    lpSum([(m1[i] + m2[i]) * vm_costs[i] for i in range(num_machines)])
    + lpSum([m1[i] + m2[i] for i in range(num_machines)])
    * params.MAX_SIZE
    * cost_volume_storage
    + lpSum(t_r[i] + t_w[i] * RF for i in range(N)) * 60 * 60 * cost_volume_iops
    + lpSum((t_r[i] + t_w[i] * RF) * s[i] for i in range(N)) * 60 * 60 * cost_volume_tp,
    "Minimization of the total cost of the hybrid solution",
)

# constraints
problem += lpSum([m1[i] + m2[i] for i in range(num_machines)]) >= RF

# --------------------########## ENOUGH MEMORY COMBINED TO STORE ALL THE ITEMS ##########--------------------
problem += (
    params.MAX_SIZE * lpSum([m1[i] + m2[i] for i in range(num_machines)])
    >= total_size * RF
)

# --------------------########## ENOUGH IOPS ##########--------------------
problem += lpSum([x[i] * (t_r[i] + t_w[i] * RF) for i in range(N)]) <= lpSum(
    [m1[i] * vm_IOPS[i] for i in range(num_machines)]
)
problem += lpSum([(1 - x[i]) * (t_r[i] + t_w[i] * RF) for i in range(N)]) <= lpSum(
    [m2[i] * vm_IOPS[i] for i in range(num_machines)]
)
# --------------------########## ENOUGH BANDWIDTH ##########--------------------
problem += lpSum([x[i] * (t_r[i] + t_w[i] * RF) * s[i] for i in range(N)]) <= lpSum(
    [m1[i] * vm_bandwidths[i] for i in range(num_machines)]
)
problem += lpSum(
    [(1 - x[i]) * (t_r[i] + t_w[i] * RF) * s[i] for i in range(N)]
) <= lpSum([m2[i] * vm_bandwidths[i] for i in range(num_machines)])

# --------------------########## EITHER VMs=0 OR VMs>=RF (per every machine type), linearization trick ##########--------------------
for j in range(num_machines):
    problem += m1[j] >= RF * z1[j]
    problem += m1[j] <= 1e5 * z1[j]

    problem += m2[j] >= RF * z2[j]
    problem += m2[j] <= 1e5 * z2[j]


result = problem.solve(solver)
cost_hybrid = round(problem.objective.value(), 2)
print(f"HYBRID COST -> {cost_hybrid}€")
placement = [x[i].value() for i in range(N)]
clustername_1 = extract_type_name(m1)
clustername_2 = extract_type_name(m2)
# make the arrays easier to manipulate, eliminate the Variables
m1 = [int(m1[i].value()) for i in range(num_machines)]
m2 = [int(m2[i].value()) for i in range(num_machines)]
m1_count = sum(m1)
m2_count = sum(m2)

items_m1 = int(sum(placement))
items_m2 = N - items_m1

print(
    f"Used machines: {clustername_1} and {clustername_2}\n"
    f"Tot items on {clustername_1}: {items_m1}\n"
    f"Tot items on {clustername_2}: {items_m2}"
)
# *** *** *** *** *** *** *** *** Allocated items *** *** *** *** *** *** *** ***
size_cluster1 = sum(placement[i] * s[i] for i in range(N)) * RF
iops_cluster1 = sum(placement[i] * (t_r[i] + t_w[i] * RF) for i in range(N))
bandwidth_cluster1 = sum(placement[i] * (t_r[i] + t_w[i] * RF) * s[i] for i in range(N))
size_cluster2 = sum((1 - placement[i]) * s[i] for i in range(N)) * RF
iops_cluster2 = sum((1 - placement[i]) * (t_r[i] + t_w[i] * RF) for i in range(N))
bandwidth_cluster2 = sum(
    (1 - placement[i]) * (t_r[i] + t_w[i] * RF) * s[i] for i in range(N)
)
# *** *** *** *** *** *** *** *** Available space *** *** *** *** *** *** *** ***
available_size_1 = params.MAX_SIZE * m1_count
available_size_2 = params.MAX_SIZE * m2_count
available_iops_1 = np.dot(m1, vm_IOPS) * m1_count
available_iops_2 = np.dot(m2, vm_IOPS) * m2_count
available_bandwidth_1 = np.dot(m1, vm_bandwidths) * m1_count
available_bandwidth_2 = np.dot(m2, vm_bandwidths) * m2_count
# *** *** *** *** *** *** *** *** Costs *** *** *** *** *** *** *** ***
cost_vms_1 = np.dot(m1, vm_costs)  # cost VMs
cost_vms_2 = np.dot(m2, vm_costs)  # cost VMs
cost_volume_1 = (
    params.MAX_SIZE * m1_count * cost_volume_storage
)  # cost per provisioned MB (MAX SIZE per VM allocated and paid for)
cost_volume_2 = params.MAX_SIZE * m2_count * cost_volume_storage
cost_iops_1 = iops_cluster1 * 60 * 60 * cost_volume_iops  # cost IOPS
cost_iops_2 = iops_cluster2 * 60 * 60 * cost_volume_iops  # cost IOPS
cost_throughput_1 = bandwidth_cluster1 * 60 * 60 * cost_volume_tp  # cost band
cost_throughput_2 = bandwidth_cluster2 * 60 * 60 * cost_volume_tp  # cost band

cost_cluster1 = cost_vms_1 + cost_volume_1 + cost_iops_1 + cost_throughput_1
cost_cluster2 = cost_vms_2 + cost_volume_2 + cost_iops_2 + cost_throughput_2

print(
    f"Cost of {clustername_1} = {cost_cluster1:.2f}€/h\n"
    f"Cost of {clustername_2} = {cost_cluster2:.2f}€/h\n"
)
if m1_count > 0:
    print(
        f"IOPS saturation of {clustername_1}: {iops_cluster1/available_iops_1:.2%}\n"
        f"Bandwidth saturation of cluster {clustername_1}: {bandwidth_cluster1/available_bandwidth_1:.2%}\n"
        f"Storage saturation of cluster {clustername_1}: {size_cluster1/available_size_1:.2%}"
    )

if m2_count > 0:
    print(
        f"IOPS saturation of {clustername_2}: {iops_cluster2/available_iops_2:.2%}\n"
        f"Bandwidth saturation of cluster {clustername_2}: {bandwidth_cluster2/available_bandwidth_2:.2%}\n"
        f"Storage saturation of cluster {clustername_2}: {size_cluster2/available_size_2:.2%}"
    )

print("-" * 80)

best_cost_cassandra = np.inf
for mt in range(num_machines):
    vms_size = total_size * RF / params.MAX_SIZE
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
        only_cassandra_vms = min_m * vm_costs[mt]
        only_cassandra_volume = params.MAX_SIZE * min_m * cost_volume_storage
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
