from cmath import inf
import pulp as pulp
from pulp import constants
from pulp.pulp import lpSum
import params
import numpy as np
import sys

cost_write = 1.4842e5 / 1e6  # cost per write
cost_read = 0.2968e5 / 1e6  # cost per read
cost_storage = 0.29715e5  # cost per GB

vm_types = np.array(
    [
        "m4.large",
        "m4.xlarge",
        "m4.2xlarge",
        "m4.4xlarge",
        "m4.10xlarge",
        "m4.16xlarge",
        "i3.large",
        "i3.xlarge",
        "i3.2xlarge",
        "i3.4xlarge",
        "i3.8xlarge",
        "i3.16xlarge",
        "i3.metal",
    ]
)
vm_IOPS = np.array(
    [
        3600,
        6000,
        8000,
        16000,
        32000,
        65000,
        3000,
        6000,
        12000,
        16000,
        32500,
        65000,
        80000,
    ]
)
vm_costs = [
    0.1,
    0.2,
    0.4,
    0.8,
    2,
    3.2,
    0.156,
    0.312,
    0.624,
    1.248,
    2.496,
    1.992,
    4.992,
]


def estimateCost(noVMs: int, which_vm: int) -> float:
    # print(self.vm_costs)
    # print(which_vm)
    return noVMs * vm_costs[which_vm]


def getIops(which_vm: int):
    return vm_IOPS[which_vm]


def getType(which_type: int):
    return vm_types[which_type]


sys.stdout = open("/Users/enrico/Desktop/results.txt", "w")
N = params.N
s = list((2 ** 30 - 1) * np.random.rand(N) + 1)

# Number of items N
RF = params.REPLICATION_FACTOR
# Placement vector x
x = pulp.LpVariable.dicts(
    "Placement",
    indices=[i for i in range(N)],
    cat=constants.LpBinary,
)
# Item sizes (Bytes) -> [1B-1GB] (s)

# Items' read/write throughput (tr, tw) (ops per second)
t_r = np.random.randint(1, 500, N)
t_w = np.random.randint(1, 500, N)
iops = [x + y for (x, y) in zip(t_r, t_w)]

# for every machine type, it contains a tuple (pair) of the cost-wise best number of machines and its associated cost
costs_per_type = []
# print(f"Items: {s}")
solver = pulp.getSolver("PULP_CBC_CMD")

for mt in range(13):
    m = 1  # we will start from RF in the future
    machine_step = 10
    fine_tuning_stage = False  # whether we are in the binary search phase or not
    prev_cost = inf

    while m <= 100:
        print(f"Evaluating {m} machines of type {getType(mt)}")
        # Optimization Problem
        problem = pulp.LpProblem("ItemsDisplacement", pulp.LpMinimize)

        # objective function
        problem += (
            # Dynamo
            lpSum([(1 - x[i]) * s[i] for i in range(N)]) * cost_storage
            + lpSum([(1 - x[i]) * t_r[i] for i in range(N)]) * cost_read
            + lpSum([(1 - x[i]) * t_w[i] for i in range(N)]) * cost_write
            # Cassandra
            + m * vm_costs[mt]
        ), "Minimization of the total cost of the hybrid solution"

        # constraints
        # --------------------########## MEMORY ##########--------------------
        problem += lpSum([x[i] * s[i] for i in range(N)]) * RF <= params.MAX_SIZE * m

        # --------------------########## COMPUTATION POWER ##########--------------------
        # *** *** *** *** *** INFEASIBILITY: DIVIDING BY DECISION VARIABLE *** *** *** *** ***
        problem += lpSum([x[i] * iops[i] for i in range(N)]) <= vm_IOPS[mt] * m

        result = problem.solve(solver)
        # print(f"Final Displacement: {x}")
        # cost of Dynamo if all the items were stored there
        cost_dynamo = sum([(1 - x[i].value()) * s[i] for i in range(N)]) * cost_storage
        +sum([(1 - x[i].value()) * t_r[i] for i in range(N)]) * cost_read
        +sum([(1 - x[i].value()) * t_w[i] for i in range(N)]) * cost_write

        print(f"Cost of Dynamo = {cost_dynamo}")
        cost_cassandra = m * vm_costs[mt]
        print(f"Cost of Cassandra = {cost_cassandra}")
        items_cassandra = sum(x[i].value() for i in range(N))
        print(
            f"Items on Cassandra :{items_cassandra}, items on Dynamo: {N-items_cassandra}"
        )
        total_cost = cost_dynamo + cost_cassandra
        print(f"TOTAL COST: {total_cost}\n\n")
        if total_cost < prev_cost and not fine_tuning_stage:  # proceed normally
            prev_cost = total_cost
            best_cost = total_cost
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
            total_cost < prev_cost
        ):  # fine_tuning_stage phase, cost is still decreasing: increase m by 1 and keep exploring
            prev_m = m
            m += 1
            if total_cost < best_cost:
                best_cost = total_cost
                best_machines = prev_m
            prev_cost = total_cost
        else:  # fine_tuning_stage phase, cost is increasing: best is previous
            print(
                f"Optimal cluster of type {vm_types[mt]} has {best_machines} machines, with a cost per hour of {best_cost}"
            )
            print("-" * 80)
            new_result = vm_types[mt], prev_m, best_cost
            costs_per_type.append(new_result)
            break

print("FINAL RESULTS:")
print(costs_per_type)

best_cost = inf
for (mtype, number, cost) in costs_per_type:
    if cost < best_cost:
        best_cost = cost
        best_option = (mtype, number, cost)

print(
    f"BEST OPTION IS {best_option[0]}. CLUSTER OF {best_option[1]} MACHINES, TOTAL COST -> {best_option[2]}"
)
sys.stdout.close()
sys.stdout = sys.__stdout__
