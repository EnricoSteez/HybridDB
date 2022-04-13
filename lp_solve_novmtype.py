from cmath import inf
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

N = params.N
cost_write = params.COST_WRITE_UNIT
cost_read = params.COST_READ_UNIT
cost_storage = params.COST_STORAGE
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


def gather_stats_ycsb(which: str) -> list:
    throughputs = []
    if which == "r":
        filename = "readStats.txt"
    elif which == "w":
        filename = "writeStats.txt"

    # print(f"Opening file {filename} for required throughputs -->{which}")

    with open(filename, mode="r") as file:
        i = 0
        while i < N:
            line = file.readline()
            if not re.match("user[0-9]+ [0-9]+", line):
                print(f"Found errors in throughputs in line {line}")
                i += 1
                continue

            tp = int(line.split()[1])  # kv[0]=key, kv[1]=value

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


def generate_items(distribution="custom", max_size=400):
    # ycsb: constant 100KB sizes, zipfian throughputs
    # uniform: everything uniformely distribuetd
    # custom: sizes from ibm traces, throughputs from YCSB
    allowed_dist = ["ycsb", "uniform", "custom"]
    if not distribution in allowed_dist:
        raise ValueError(f"Cannot generate sizes with distribution: {distribution}")
    if distribution == "ycsb":
        s = [100] * N
        t_r = gather_stats_ycsb("r")
        t_w = gather_stats_ycsb("w")

    elif distribution == "uniform":
        # uniform distribution
        s = list((max_size - 1) * np.random.rand(N) + 1)  # size in Bytes
        t_r = np.random.randint(1, 500, N)
        t_w = np.random.randint(1, 500, N)

    # sizes are IBM, throughputs are YCSB
    elif distribution == "custom":
        s = gather_sizes_ibm()
        t_r = gather_stats_ycsb("r")
        t_w = gather_stats_ycsb("w")

    print(f"Size of s: {len(s)}, max(s)={max(s)}, min(s)={min(s)}")
    print(f"Size of t_r: {len(t_r)}, max(t_r)={max(t_r)}, min(t_r)={min(t_r)}")
    print(f"Size of t_w: {len(t_w)}, max(t_w)={max(t_w)}, min(t_w)={min(t_w)}")
    # print(s)
    # print("SEPARATOR")
    # print(t_r)
    # print("SEPARATOR")
    # print(t_w)
    # print("SEPARATOR")
    return s, t_r, t_w


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
# PLACE HERE THE DESIRED DISTRIBUTION ["ycsb", "uniform", "custom"]
dist = params.DISTRIBUTION

# sizes in KB, throughputs in ops/s
s, t_r, t_w = generate_items(distribution=dist, max_size=400)
# print("Retrieved real world data:")
# print(f"S->{len(s)}, t_r->{len(t_r)}, t_w->{len(t_w)}")
# print(f"Throughputs read min {min(t_r)}, max {max(t_r)}")
# print(f"Throughputs write min min {min(t_w)}, max {max(t_w)}")


total_size = sum(s)

# for every machine type, it contains a tuple (pair) of the cost-wise best number of machines and its associated cost
costs_per_type = []
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

notify(message=message)

for mt in range(13):
    m = 0  # we will start from RF in the future
    machine_step = 10
    fine_tuning_stage = False  # whether we are in the binary search phase or not
    prev_cost = inf

    while m <= 300:
        print(f"Evaluating {m} machines of type {vm_types[mt]}")
        # Optimization Problem
        problem = pulp.LpProblem("ItemsDisplacement", pulp.LpMinimize)

        # objective function
        problem += (
            # Dynamo
            lpSum([(1 - x[i]) * s[i] for i in range(N)]) * cost_storage
            + lpSum([(1 - x[i]) * s[i] / 8 * t_r[i] for i in range(N)])
            * 60
            * 60
            * cost_read
            + lpSum([(1 - x[i]) * s[i] * t_w[i] for i in range(N)])
            * 60
            * 60
            * cost_write
            # Cassandra
            + m * vm_costs[mt]
        ), "Minimization of the total cost of the hybrid solution"

        # constraints
        # --------------------########## MEMORY ##########--------------------
        problem += lpSum([x[i] * s[i] for i in range(N)]) * RF <= params.MAX_SIZE * m

        # --------------------########## COMPUTATION POWER ##########--------------------
        problem += (
            lpSum([x[i] * (t_r[i] + t_w[i]) for i in range(N)]) *60 * 60 <= vm_IOPS[mt] * m
        )

        result = problem.solve(solver)

        # cost of Dynamo
        cost_dynamo = sum([(1 - x[i].value()) * s[i] for i in range(N)]) * cost_storage
        +sum(
            [
                (1 - x[i].value()) * (s[i] / 8) * t_r[i] * 60 * 60 * cost_read
                for i in range(N)
            ]
        )
        +sum(
            [
                (1 - x[i].value()) * s[i] * t_w[i] * 60 * 60 * cost_write
                for i in range(N)
            ]
        )
        print(f"Cost of Dynamo (1 hour) = {cost_dynamo}")

        # cost of Cassandra
        cost_cassandra = m * vm_costs[mt]
        print(f"Cost of Cassandra (1 hour) = {cost_cassandra:.3f}")

        items_cassandra = sum(x[i].value() for i in range(N))
        iops_cassandra = sum(x[i].value() * (t_r[i] + t_w[i]) for i in range(N))

        print(
            f"Number of items on Cassandra :{items_cassandra}, items on Dynamo: {N-items_cassandra}"
        )
        print(f"Percentage of items on Cassandra: {items_cassandra/N}%")
        print(f"Percentage of iops on Cassandra: {iops_cassandra/N}%")
        size_cassandra = sum([(x[i].value()) * s[i] for i in range(N)])
        print(
            f"Amount of data on Cassandra:{int(size_cassandra/2**20)}/{int(total_size/2**20)} [GB] ({size_cassandra/total_size:.2f}%)"
        )

        total_cost = cost_dynamo + cost_cassandra
        print(f"TOTAL COST: {total_cost:}\n")
        if (
            total_cost < prev_cost and not fine_tuning_stage and items_cassandra != N
        ):  # total cost is decreasing -> proceed normally
            prev_cost = total_cost
            best_cost = total_cost
            best_placement = [x[i].value() for i in range(N)]
            best_machines = m
            prev_m = m
            m += machine_step
        elif (
            not fine_tuning_stage
        ):  # total cost is increasing --> enter fine_tuning_stage phase to find the perfect m
            prev_cost = total_cost
            fine_tuning_stage = True
            m = (
                prev_m + 1
            )  # start by exploring linearly the last unexplored sector of possible sizes
        elif (
            total_cost < best_cost
        ):  # fine_tuning_stage phase, cost is still decreasing: increase m by 1 and keep exploring
            prev_m = m
            m += 1
            best_cost = total_cost
            best_machines = m
            prev_cost = total_cost
            best_placement = [x[i].value() for i in range(N)]
        else:  # fine_tuning_stage phase, cost is increasing: best is previous
            plural = "s" if best_machines > 1 else ""
            print(
                f"Optimal cluster of type {vm_types[mt]} has {best_machines} machine{plural}, with a cost per hour of {best_cost}"
            )
            print("-" * 80)
            new_result = mt, prev_m, best_cost
            costs_per_type.append(new_result)
            target_items_per_type.append(
                [abs(a - b) for a, b in zip(old_placement, best_placement)]
            )
            break

t1 = time()
print("FINAL RESULTS:")
for mtype, n, cost in costs_per_type:
    print(f"{mtype}: {n} machines --> {cost:.3f}€ per hour")

best_cost = inf
for (mt, number, cost) in costs_per_type:
    if cost < best_cost:
        best_cost = cost
        best_option = (mt, number, cost)

print(
    f"BEST OPTION IS {vm_types[best_option[0]]}, CLUSTER OF {best_option[1]} MACHINES,\nTOTAL COST --> {best_option[2]}€ PER HOUR \n"
)

cost_dynamo = sum(s) * cost_storage

cost_dynamo += sum(
    (s[i] / 8 * t_r[i] * cost_read + t_w[i] * cost_write) * 60 * 60 for i in range(N)
)

print(f"Cost saving: {cost_dynamo-best_option[2]:.2f}€ / h")

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

notify(message=message)

if N <= 100:
    print("Distribution: ")
    print("Item\tSize\tT_R\tT_w\tPlacement\n")
    for i in range(N):
        print(f"{i}\t{s[i]}\t{t_r[i]}\t{t_w[i]}\t{x[i].value()}")
