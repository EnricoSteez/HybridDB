from cmath import inf
from math import ceil, dist
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
vm_costs = params.vm_costs
stability_period = params.WORKLOAD_STABILITY


def notify(message):
    with open("./keys/keys.json", "r") as keys_file:
        k = json.load(keys_file)
        token = k["telegram_token"]
        chat_id = k["telegram_chat_id"]
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=message)


def gather_stats_ycsb(which: str, scale: float) -> list:
    throughputs = []
    if which == "r":
        filename = "readStats.txt"
    elif which == "w":
        filename = "writeStats.txt"

    print(f'Gathering ycsb throughputs mode="{which}" scale={scale}')

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

        while len(throughputs) < N:
            print(f"Appending one zero to throughputs t_{which}")
            throughputs.append(0)

    # print(f"Returning throughputs mode->{which}")
    return throughputs


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


def generate_items(distribution, scale=1.0):
    # ycsb: constant 100KB sizes, zipfian throughputs
    # uniform: everything uniformely distribuetd
    # custom: sizes from ibm traces, throughputs from YCSB
    if distribution == "ycsb":
        s = [100] * N
        t_r = gather_stats_ycsb("r", scale)
        t_w = gather_stats_ycsb("w", scale)

    elif distribution == "uniform":
        # uniform distribution
        # max size for DynamoDB is 400KB
        s = list((400 - 1) * np.random.rand(N) + 1)  # size in Bytes
        t_r = np.random.rand(N) * 500 * scale
        t_w = np.random.rand(N) * 500 * scale

    # sizes are IBM, throughputs are YCSB
    elif distribution == "custom":
        s = gather_sizes_ibm()
        t_r = gather_stats_ycsb("r", scale)
        t_w = gather_stats_ycsb("w", scale)

    print(f"Number of items: {len(s)}, max_size={max(s)}, min_size={min(s)}")
    print(f"Throughputs scale: {scale}")
    print(f"Size of t_r: {len(t_r)}, max(t_r)={max(t_r)}, min(t_r)={min(t_r)}")
    print(f"Size of t_w: {len(t_w)}, max(t_w)={max(t_w)}, min(t_w)={min(t_w)}")
    print("\n")
    # print(s)
    # print("SEPARATOR")
    # print(t_r)
    # print("SEPARATOR")
    # print(t_w)
    # print("SEPARATOR")
    return s, t_r, t_w


if len(sys.argv) < 3 or len(sys.argv) > 5:
    sys.exit(
        f"Usage: python3 {path.basename(__file__)} <N> <uniform|ycsb|custom> [TPscaling]"
    )
try:
    N = int(sys.argv[1])
    if len(sys.argv) == 4:
        scaling = float(sys.argv[3])
    else:
        scaling = 1
except ValueError:
    sys.exit("N and TPscaling must be numbers")

dist = sys.argv[2]
allowed_dists = ["ycsb", "uniform", "custom"]
if not dist in allowed_dists:
    raise ValueError(f"Cannot generate sizes with distribution: {dist}")

sys.stdout = open("results.txt", "w")

# Number of items N
RF = params.REPLICATION_FACTOR
# Placement vector x
x = pulp.LpVariable.dicts(
    "Placement",
    indices=[i for i in range(N)],
    cat=constants.LpBinary,
)

rng = default_rng()

# sizes in KB, throughputs in ops/s
s, t_r, t_w = generate_items(distribution=dist, scale=scaling)
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
t0 = time()
message = (
    f"Optimisation id= {run_id}\n"
    f"N = {N:.0e}, {dist} distribution\n"
    f"Started on {strftime('%a at %H:%M:%S',gmtime(t0))}\n"
    "AWAITING TERMINATION"
)
threading.Thread(target=notify(message=message)).start()
# notify(message=message)

best_overall = inf

significant_vm_types = [3, 4, 5, 9, 10, 11, 12]

for mt in range(13):
    if total_size < 3 * params.MAX_SIZE:
        m = 3
    else:
        m = ceil(total_size / params.MAX_SIZE)  # we will start from RF in the future
    machine_step = 5
    fine_tuning_stage = False  # whether we are in the binary search phase or not
    prev_cost = inf
    while True:
        print(f"Evaluating {m} machines of type {vm_types[mt]}")
        # Optimization Problem
        problem = pulp.LpProblem("ItemsDisplacement", pulp.LpMinimize)

        # objective function
        problem += (
            # Dynamo static cost
            lpSum([(1 - x[i]) * s[i] for i in range(N)]) * cost_storage
            # Dynamo accesses cost
            + lpSum([(1 - x[i]) * t_r[i] * (s[i] / 8) for i in range(N)])
            * 60
            * 60
            * cost_read
            + lpSum([(1 - x[i]) * s[i] * t_w[i] for i in range(N)])
            * 60
            * 60
            * cost_write
            # Cassandra VMs cost
            + m * vm_costs[mt]
            # Cassandra volumes baseline charge
            + lpSum(x[i] * s[i] for i in range(N)) * cost_volume_storage
            # Cassandra volumes IOPS charge
            + lpSum(x[i] * (t_r[i] + t_w[i]) for i in range(N))
            * 60
            * 60
            * cost_volume_iops
            # Cassandra volumes performance charge
            + lpSum(x[i] * (t_r[i] + t_w[i]) * s[i] for i in range(N)) * cost_volume_tp,
            "Minimization of the total cost of the hybrid solution",
        )

        # constraints
        # --------------------########## MEMORY ##########--------------------
        problem += lpSum([x[i] * s[i] for i in range(N)]) * RF <= params.MAX_SIZE * m

        # --------------------########## COMPUTATION POWER ##########--------------------
        problem += (
            lpSum([x[i] * (t_r[i] + t_w[i]) for i in range(N)]) <= vm_IOPS[mt] * m
        )

        result = problem.solve(solver)

        # cost of Dynamo
        # 1 read unit every 8 KB (multiply the throughput by size/8)
        cost_dynamo = (
            sum((1 - x[i].value()) * s[i] for i in range(N)) * cost_storage
            + sum((1 - x[i].value()) * (s[i] / 8) * t_r[i] for i in range(N))
            * 60
            * 60
            * cost_read
            # 1 write unit every KB (multiply the throughput by the size in KB to obtain the units)
            + sum((1 - x[i].value()) * s[i] * t_w[i] for i in range(N))
            * 60
            * 60
            * cost_write
        )
        print(f"Cost of Dynamo (1 hour) = {cost_dynamo:.3f}")

        # cost of Cassandra
        cost_cassandra = (
            m * vm_costs[mt]
            # Cassandra volumes baseline charge
            + sum(x[i].value() * s[i] for i in range(N)) * cost_volume_storage
            # Cassandra volumes IOPS charge
            + sum(x[i].value() * (t_r[i] + t_w[i]) for i in range(N))
            * 60
            * 60
            * cost_volume_iops
            # Cassandra volumes performance charge
            + sum(x[i].value() * (t_r[i] + t_w[i]) * s[i] for i in range(N))
            * cost_volume_tp
        )

        print(f"Cost of Cassandra (1 hour) = {cost_cassandra:.3f}")

        items_cassandra = sum(x[i].value() for i in range(N))
        items_dynamo = sum(1 - x[i].value() for i in range(N))
        iops_cassandra = int(sum(x[i].value() * (t_r[i] + t_w[i]) for i in range(N)))
        tot_iops = sum(t_r[i] + t_w[i] for i in range(N))
        print(
            f"Number of items on Cassandra :{items_cassandra}, items on Dynamo: {int(items_dynamo)}"
        )
        print(f"Percentage of items on Cassandra: {items_cassandra/N*100:.2f}%")
        print(f"Percentage of iops on Cassandra: {iops_cassandra/tot_iops*100:.2f}%")
        size_cassandra = sum((x[i].value()) * s[i] for i in range(N))
        print(
            f"Amount of data on Cassandra: {size_cassandra/2**10:.3f}/{total_size/2**10:.3f} [MB] ({size_cassandra/total_size*100:.3f}%)"
        )

        total_cost = cost_dynamo + cost_cassandra
        print(f"TOTAL COST: {total_cost:.2f}\n")
        if (
            total_cost < prev_cost and not fine_tuning_stage and items_cassandra != N
        ):  # total cost is decreasing and placement is still hybrid -> proceed normally
            prev_cost = total_cost
            best_cost_current_vmtype = total_cost
            best_placement = [x[i].value() for i in range(N)]
            best_machines = m
            prev_m = m
            m += machine_step
        elif (
            not fine_tuning_stage
        ):  # total cost is increasing --> enter fine_tuning_stage phase to find the perfect m
            prev_cost = total_cost
            fine_tuning_stage = True
            # start by exploring linearly the last unexplored sector of possible sizes
            m = prev_m + 1
        elif (
            total_cost < best_cost_current_vmtype
        ):  # fine_tuning_stage phase, cost is still decreasing: increase m by 1 and keep exploring
            prev_m = m
            best_machines = m
            m += 1
            best_cost_current_vmtype = total_cost
            prev_cost = total_cost
            best_placement = [x[i].value() for i in range(N)]
        else:  # fine_tuning_stage phase, cost is increasing: best is previous
            plural = "s" if best_machines > 1 else ""
            print(
                f"Optimal cluster of type {vm_types[mt]} has {best_machines} machine{plural}, with a cost per hour of {best_cost_current_vmtype:.2f}"
            )
            print("-" * 80)
            new_result = prev_m, best_cost_current_vmtype
            costs_per_type[mt] = new_result
            # target_items_per_type.append(
            #     [abs(a - b) for a, b in zip(old_placement, best_placement)]
            # )

            break

t1 = time()
print("FINAL RESULTS:")
# mt, n, cost
best = inf
for mt in costs_per_type:
    cost = costs_per_type[mt][1]
    number = costs_per_type[mt][0]
    print(f"{vm_types[mt]}: {number} machines --> {cost:.3f} € per hour")
    if cost < best:
        best = cost
        best_option = (mt, number, cost)

print(
    f"BEST OPTION IS {vm_types[best_option[0]]}, CLUSTER OF {best_option[1]} MACHINES,\nTOTAL COST --> {best_option[2]}€ PER HOUR \n"
)

cost_dynamo = (
    sum(s) * cost_storage
    + sum((s[i] / 8) * t_r[i] for i in range(N)) * 60 * 60 * cost_read
    + sum(s[i] * t_w[i] for i in range(N)) * 60 * 60 * cost_write
)

print(
    f"Cost of only DYNAMO: {cost_dynamo}\n"
    f"Cost saving compared to using only DynamoDB: {cost_dynamo-best_option[2]:.2f} € / h"
)

tot_time = t1 - t0
print(f"Took {tot_time} seconds ")
if t1 - t0 > 60:
    print(f"({int((tot_time-(tot_time%60))/60)}min {int(tot_time%60)}s)\n")
sys.stdout.close()
sys.stdout = sys.__stdout__

message = (
    f"Optimisation id= {run_id}\n"
    f"N = {N:.0e}, {dist} distribution\n"
    f"Started on {strftime('%a at %H:%M:%S',gmtime(t0))}\n"
    f"Finished on {strftime('%a at %H:%M:%S',gmtime(t1))}\n"
    f"Took: {strftime('%H:%M:%S',gmtime(tot_time))}\n"
    'See "results.txt" for more info'
)
threading.Thread(target=notify(message=message)).start()
# notify(message=message)
