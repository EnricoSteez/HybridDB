from cmath import inf
from math import ceil
from uuid import uuid4
import pulp as pulp
from pulp import constants
from pulp.pulp import lpSum
import params
import numpy as np
import sys
from time import time
from time import gmtime
from time import strftime
from numpy.random import default_rng
import re
import json
import telegram
from os import path
import threading
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


def notify(message):
    with open("./keys/keys.json", "r") as keys_file:
        k = json.load(keys_file)
        token = k["telegram_token"]
        chat_id = k["telegram_chat_id"]
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=message)


def gather_throughputs(filename: str, scale: float) -> list:

    print(f'Gathering ycsb throughputs from file "{filename}" scale={scale}')

    if filename == "readStats.txt" or filename == "writeStats.txt":
        throughputs = []
        with open(filename, mode="r") as file:
            i = 0
            while i < N:
                line = file.readline()
                if not re.match("user[0-9]+ [0-9]+", line) and line != "\n":
                    print(f"Found errors in throughputs in line {line}")
                    i += 1
                    continue

                tp = int(line.split()[1]) * scale  # kv[0]=key, kv[1]=value

                throughputs.append(tp)
                i += 1

        # while len(throughputs) < N:
        #     print(f"Appending one zero to throughputs t_{which}")
        #     throughputs.append(0)

        # print(f"Returning throughputs mode->{which}")
        return throughputs
    elif filename == "throughputs.txt":
        tr = []
        tw = []
        with open(filename, mode="r") as file:
            i = 0
            while i < N:
                line = file.readline()
                # line[0]=key, line[1]=tp_read, line[2]=tp_write
                tr.append = int(line.split()[1]) * scale
                tw.append = int(line.split()[2]) * scale
                i += 1
        return tr, tw


def gather_sizes_ibm():
    # scan the file first to get the range of values
    min_size = inf
    max_size = 0

    with open("sizes.txt", "r") as file:
        i = 0
        while i < N:
            size = int(file.readline().split()[0])
            if size < min_size:
                min_size = size
            if size > max_size:
                max_size = size
            i += 1

        values_range = max_size - min_size
        # rewind and normalize each value in the range [0,400]
        file.seek(0)
        s = []
        i = 0
        while i < N:
            number = int(file.readline().split()[0])
            size = number / values_range * 400
            s.append(size)
            i += 1
    return s


def gather_data_java(scale=1.0):
    s = []
    t_r = []
    t_w = []
    min_size = inf
    max_size = 0
    with open("throughputs.txt", "r") as file:
        i = 0
        while i < N:
            size = int(file.readline().split()[1])
            if size < min_size:
                min_size = size
            if size > max_size:
                max_size = size
            i += 1

        values_range = max_size - min_size
        # rewind and normalize each value in the range [0,400]
        file.seek(0)
        i = 0
        while i < N:
            line = file.readline().split()
            s[i] = int(line[1]) / values_range * 400
            t_r[i] = int(line[2]) * scale
            t_w[i] = int(line[3]) * scale
            i += 1
    return s, t_r, t_w


def generate_items(distribution, scale=1.0, custom_size=0.1, max_throughput=20000):
    # ycsb: constant 100KB sizes = 0.1MB, zipfian throughputs
    # uniform: everything uniformely distribuetd
    # custom: sizes from ibm traces, throughputs from YCSB
    if distribution == "ycsb":
        s = [custom_size] * N
        t_r = gather_throughputs("readStats.txt", scale)
        t_w = gather_throughputs("writeStats.txt", scale)

    elif distribution == "uniform":
        # uniform distribution
        # max size for DynamoDB is 400KB = 0.4MB
        s = list((0.4 - 1) * np.random.rand(N) + 1)  # size in MB
        t_r = np.random.rand(N) * 500 * scale
        t_w = np.random.rand(N) * 500 * scale

    # sizes are IBM, throughputs are YCSB
    elif distribution == "custom":
        s = gather_sizes_ibm()
        t_r = gather_throughputs("readStats.txt", scale)
        t_w = gather_throughputs("writeStats.txt", scale)

    elif distribution == "java":
        s, t_r, t_w = gather_data_java(scale)
    elif distribution == "zipfian":
        a = int(scale)
        s = [custom_size] * N
        t_r = []
        t_w = []
        with open(f"zipfian/{N}_{a}", "r") as file:
            for i in range(N):
                prob = float(file.readline().split()[0])
                t_r.append(prob * max_throughput / 2)
                t_w.append(prob * max_throughput / 2)

    print(
        f"Number of items: {len(s)}, max_size={max(s)}MB, min_size={min(s)}MB\n"
        f"Throughputs scale: {scale}\n"
        f"len(t_r): {len(t_r)}, max(t_r)={max(t_r)}, min(t_r)={min(t_r)}\n"
        f"len(t_w): {len(t_w)}, max(t_w)={max(t_w)}, min(t_w)={min(t_w)}\n"
    )
    # print(s)
    # print("SEPARATOR")
    # print(t_r)
    # print("SEPARATOR")
    # print(t_w)
    # print("SEPARATOR")
    return s, t_r, t_w


if len(sys.argv) < 3 or len(sys.argv) > 7:
    sys.exit(
        f"Usage: python3 {path.basename(__file__)} <N> <items_size [MB]> <tot_throughput> "
        f"<uniform|ycsb|custom|java|zipfian> <TP_scale_factor|skew> outputFileName"
    )
try:
    N = int(sys.argv[1])
    custom_size = float(sys.argv[2])
    max_throughput = int(sys.argv[3])
    scalingFactor = float(sys.argv[5])
except ValueError:
    sys.exit("N, items_size, max_throughput and TPscaling must be numbers")

dist = sys.argv[4]
filename = sys.argv[6]
allowed_dists = ["ycsb", "uniform", "custom", "java", "zipfian"]
if dist not in allowed_dists:
    raise ValueError(f'Distribution: "{dist}" is not allowed')

sys.stdout = open(filename, "w")

# Number of items N
RF = params.REPLICATION_FACTOR
# Placement vector x
x = pulp.LpVariable.dicts(
    "Placement",
    indices=[i for i in range(N)],
    cat=constants.LpContinuous,
    lowBound=0,
    upBound=1,
)

rng = default_rng()

# sizes in MB, throughputs in ops/s
t0 = time()
s, t_r, t_w = generate_items(
    distribution=dist,
    scale=scalingFactor,
    custom_size=custom_size,
    max_throughput=max_throughput,
)
t_items = time()
# print("Retrieved real world data:")
# print(f"S->{len(s)}, t_r->{len(t_r)}, t_w->{len(t_w)}")
# print(f"Throughputs read min {min(t_r)}, max {max(t_r)}")
# print(f"Throughputs write min min {min(t_w)}, max {max(t_w)}")

total_size = sum(s)

# for every machine type, it contains a tuple (pair) of the cost-wise best number of machines and its associated cost
costs_per_type = dict()
target_items_per_type = []
old_placement = [0] * N
# print(f"Items: {s}")
solver = pulp.getSolver("PULP_CBC_CMD")
run_id = uuid4()

message = (
    f"Optimisation id= {run_id}\n"
    f"N = {N:.0e}, {dist} distribution\n"
    f"Started on {strftime('%a at %H:%M:%S',gmtime(t0))}\n"
    # f"Items generation took: {strftime('%H:%M:%S',gmtime(t_items-t0))}\n"
    # now probabilities are not generated anymore but retrieved from file
    "AWAITING TERMINATION"
)
threading.Thread(target=notify(message=message)).start()
# notify(message=message)

best_overall = inf

for mt in range(len(vm_types)):
    m = 3
    machine_step = 2
    fine_tuning_stage = False  # whether we are in the binary search phase or not
    best_cost = inf
    while True:
        print(f"Evaluating {m} machines of type {vm_types[mt]}")
        # Optimization Problem
        problem = pulp.LpProblem("ItemsPlacement", pulp.LpMinimize)

        # objective function
        problem += (
            lpSum([(1 - x[i]) * s[i] for i in range(N)]) * cost_storage
            + lpSum([(1 - x[i]) * t_r[i] * (s[i] * 1000 / 8) for i in range(N)])
            * 60
            * 60
            * cost_read
            + lpSum([(1 - x[i]) * s[i] * 1000 * t_w[i] for i in range(N)])
            * 60
            * 60
            * cost_write
            + m * vm_costs[mt]
            + params.MAX_SIZE * m * cost_volume_storage
            + lpSum(x[i] * (t_r[i] + t_w[i]) for i in range(N))
            * 60
            * 60
            * cost_volume_iops
            + lpSum(x[i] * (t_r[i] + t_w[i]) * s[i] for i in range(N))
            * 60
            * 60
            * cost_volume_tp,
            "Minimization of the total cost of the hybrid solution",
        )

        # constraints
        # --------------------########## MEMORY ##########--------------------
        problem += lpSum([x[i] * s[i] for i in range(N)]) * RF <= params.MAX_SIZE * m

        # assuming write all and read any
        # --------------------########## COMPUTATION POWER ##########--------------------
        problem += (
            lpSum([x[i] * (t_r[i] + t_w[i] * RF) for i in range(N)]) <= vm_IOPS[mt] * m
        )

        # --------------------########## BANDWIDTH ##########--------------------
        problem += (
            lpSum([x[i] * (t_r[i] + t_w[i] * RF) * s[i] for i in range(N)])
            <= vm_bandwidths[mt] * m
        )

        result = problem.solve(solver)

        items_cassandra = sum(1 if x[i].value() > 0.5 else 0 for i in range(N))
        items_dynamo = sum(1 if x[i].value() < 0.5 else 0 for i in range(N))
        print(
            f"Tot items on Cassandra: {int(items_cassandra)}\n"
            f"Tot items on Dynamo: {int(items_dynamo)}\n"
            f"Items Dynamo should be {N-items_cassandra} (for double check)"
        )

        placement = [1 if x[i].value() > 0.5 else 0 for i in range(N)]

        # cost of Dynamo
        # 1 read unit every 8 KB (multiply the iops by size[MB]*1000/8)
        # 1 write unit every KB (multiply the iops by the size[MB]*1000 to obtain the units)
        cost_dynamo = (
            sum((1 - placement[i]) * s[i] for i in range(N)) * cost_storage
            + sum((1 - placement[i]) * (s[i] * 1000 / 8) * t_r[i] for i in range(N))
            * 60
            * 60
            * cost_read
            + sum((1 - placement[i]) * s[i] * 1000 * t_w[i] for i in range(N))
            * 60
            * 60
            * cost_write
        )
        print(f"Cost of Dynamo (hybrid) = {cost_dynamo:.2f}€/h")

        # # cost of Cassandra
        # cost_iops = (
        #     sum(placement[i] * (t_r[i] + t_w[i]) for i in range(N))
        #     * 60
        #     * 60
        #     * cost_volume_iops
        # )
        # cost_performance = (
        #     sum(placement[i] * (t_r[i] + t_w[i]) * s[i] for i in range(N))
        #     * cost_volume_tp
        # )
        # cost_baseline = params.MAX_SIZE * m * cost_volume_storage
        # cost VMs + storage charge + iops charge + tp charge
        cost_cassandra = (
            m * vm_costs[mt]
            + params.MAX_SIZE * m * cost_volume_storage
            + sum(placement[i] * (t_r[i] + t_w[i]) for i in range(N))
            * 60
            * 60
            * cost_volume_iops
            + sum(placement[i] * (t_r[i] + t_w[i]) * s[i] for i in range(N))
            * 60
            * 60
            * cost_volume_tp
        )
        print(
            # f"Cassandra machines = {m * vm_costs[mt]:.2f}\n"
            # f"Cassandra baseline = {cost_baseline:.2f}\n"
            # f"Cassandra iops = {cost_iops:.2f}\n"
            # f"Cassandra baseline = {cost_performance:.2f}\n"
            f"Cost of Cassandra (hybrid) = {cost_cassandra:.2f}€/h"
        )

        iops_cassandra = sum(placement[i] * (t_r[i] + t_w[i]) for i in range(N))
        tot_iops = sum(t_r[i] + t_w[i] for i in range(N))
        size_cassandra = sum((placement[i]) * s[i] for i in range(N)) * RF
        print(f"Amount of data on Cassandra: {size_cassandra:.2f} [MB]")
        print(
            f"Percentage of items on Cassandra: {items_cassandra/N:.2%}\n"
            f"Percentage of iops on Cassandra: {iops_cassandra/tot_iops:.2%}\n"
            f"IOPS saturation in the cluster: {iops_cassandra} allocated / {m*vm_IOPS[mt]} available\n"
            f"Storage saturation: {size_cassandra} allocated / {params.MAX_SIZE*m}"
        )
        total_cost = problem.objective.value()
        print(
            f"TOTAL COST: {total_cost:.2f}\n"
            f"(Should be equal to {cost_dynamo+cost_cassandra:.2f})\n"
        )

        if total_cost < best_cost:  # total cost is decreasing -> proceed normally
            best_cost = total_cost
            best_placement = placement
            best_machines = m
            m += 1
        else:  # total cost is increasing -->  best is previous
            print(
                f"Optimal cluster of type {vm_types[mt]} has {best_machines} machines, with a cost of {best_cost:.2f}€/h"
            )
            print("-" * 80)
            new_result = best_machines, best_cost
            costs_per_type[mt] = new_result
            break

t_end = time()
print("FINAL RESULTS:")

best = inf
for mt in costs_per_type:
    cost = costs_per_type[mt][1]
    num_vms = costs_per_type[mt][0]
    print(f"{vm_types[mt]}: {num_vms} machines --> {cost:.2f} € per hour")
    if cost < best:
        best = cost
        best_option = (mt, num_vms, cost)

print(
    f"BEST OPTION IS {vm_types[best_option[0]]}, CLUSTER OF {best_option[1]} MACHINES,\n"
    f"TOTAL COST --> {best_option[2]:.2f}€/h\n"
)
# COST OF ONLY DYNAMO
cost_dynamo = (
    total_size * cost_storage
    + sum((s[i] * 1000 / 8) * t_r[i] for i in range(N)) * 60 * 60 * cost_read
    + sum(s[i] * 1000 * t_w[i] for i in range(N)) * 60 * 60 * cost_write
)

print(f"Cost of only DYNAMO: {cost_dynamo:.2f}€/h")
# COST OF ONLY CASSANDRA
best_cost_cassandra = inf
for mt in range(len(vm_types)):
    vms_size = total_size * RF / params.MAX_SIZE
    vms_io = (sum(t_r) + sum(t_w)) / vm_IOPS[mt]

    m = ceil(
        max(total_size * RF / params.MAX_SIZE, (sum(t_r) + sum(t_w)) / vm_IOPS[mt], 3)
    )
    cost = (
        m * vm_costs[mt]
        # Cassandra volumes baseline charge
        + params.MAX_SIZE * m * cost_volume_storage
        # Cassandra volumes IOPS charge
        + (sum(t_r) + sum(t_w)) * 60 * 60 * cost_volume_iops
        # Cassandra volumes performance charge
        + sum((t_r[i] + t_w[i]) * s[i] for i in range(N)) * 60 * 60 * cost_volume_tp
    )
    if cost < best_cost_cassandra:
        best_cost_cassandra = cost
        best_vm_cassandra = mt
        best_n_cassandra = m

print(
    f"Cost of only CASSANDRA: {best_cost_cassandra:.2f}€/h, "
    f"achieved with {best_n_cassandra} machines "
    f"of type {vm_types[best_vm_cassandra]}\n"
    f"(min machines due to size: {vms_size} (->{ceil(vms_size)}))\n"
    f"(min machines due to iops: {vms_io} (->{ceil(vms_io)}))\n"
)

print(
    f"Cost saving compared to best option: {min(cost_dynamo,best_cost_cassandra)-best_option[2]:.2f} €/h"
)

tot_time = t_end - t_items
print(f"Took {tot_time:.2f} seconds ")
if t_end - t0 > 60:
    print(f"({int((tot_time-(tot_time%60))/60)}min {int(tot_time%60)}s)")
sys.stdout.close()
sys.stdout = sys.__stdout__

message = (
    f"Optimisation id= {run_id}\n"
    f"N = {N:.0e}, {dist} distribution\n"
    f"Started on {strftime('%a at %H:%M:%S',gmtime(t0))}\n"
    f"Finished on {strftime('%a at %H:%M:%S',gmtime(t_end))}\n"
    f"Optimisation took: {strftime('%H:%M:%S',gmtime(tot_time))}\n"
    f"See {filename} for detailed info"
)
threading.Thread(target=notify(message=message)).start()

with open("placement", "wb") as file:
    for num in best_placement:
        file.write(bytes([int(num)]))

# system("pmset sleepnow")
