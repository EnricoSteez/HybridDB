import pulp as pulp
from pulp import constants
from pulp.pulp import lpSum
import params
import numpy as np
import random


class dynamoDB:
    def __init__(self):
        self.cost_write = 1.4842 / 1e6  # cost per write
        self.cost_read = 0.2968 / 1e6  # cost per read
        self.cost_storage = 0.29715  # cost per GB

    def estimateCost_hour(self, placement, t_read, t_write, db_size):
        # DynamoDB cost as per AWS website
        storage_cost = (db_size - 25) * self.cost_storage if db_size > 25 else 0
        return (
            np.dot(list(placement), t_read) * 60 * 60 * self.cost_read
            # t_r is in ops/sec, we are estimating the cost per hour so we need the throughput in ops/hour
            + np.dot(list(placement), t_write) * 60 * 60 * self.cost_write
            # same for t_w
            + storage_cost
        )


class cassandra:
    replication_factor = 3

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
    vm_costs = np.array(
        [0.1, 0.2, 0.4, 0.8, 2, 3.2, 0.156, 0.312, 0.624, 1.248, 2.496, 1.992, 4.992]
    )

    def __init__(self) -> None:
        pass

    ### returns the cost per hour ###
    def estimateCost(self, noVMs: int, which_vm) -> float:
        return noVMs * np.dot(self.vm_costs, list(which_vm))


dynamoDB = dynamoDB()
cassandra = cassandra()
# Number of items N
N = params.N
# Placement vector x
x = pulp.LpVariable.dicts("x", (i for i in range(N)), 0, 1)

# Item sizes (Bytes) -> [1B-1GB] (s)
s = (2e30 - 1) * np.random.random(N) + 1
# Items' read/write throughput (tr, tw) (ops per second)
t_r = np.random.randint(1, 50, N)
t_w = np.random.randint(1, 50, N)

# Number of VMs
# (in the Mathematical formulation, this corresponds to M)
m = pulp.LpVariable("M", lowBound=3, cat=constants.LpInteger)
# Type of VM employed, we assume we are going to use only one type (see pdf)
# (in the PDF formulation, this corresponds to \vec{m})
mt = pulp.LpVariable.dicts(
    "mt", (i for i in range(13)), lowBound=0, upBound=1, cat=constants.LpBinary
)
# Optimization Problem
problem = pulp.LpProblem("ItemsDisplacement", pulp.LpMinimize)

total_size_dynamo = np.dot(list(x), s)  # only items placed in Dynamo

# objective function
problem += (
    dynamoDB.estimateCost_hour(
        placement=x, t_read=t_r, t_write=t_w, db_size=total_size_dynamo
    )
    + cassandra.estimateCost(noVMs=m, which_vm=mt),
    "Minimization of the total cost of the hybrid solution",
)

# constraints
# --------------------########## SIZE ##########--------------------
# 1: enough storage in m machines of type mt to hold all data * RF
problem += (
    lpSum(x[i] * s[i] for i in range(N))
    <= params.MAX_SIZE * np.dot(m, list(mt)) / cassandra.replication_factor
)

# np.dot(list(x), s) * cassandra.replication_factor / m.value() <= params.MAX_SIZE

# 2: enough IOPS in the machines to sustain the total throughput of all data.
# --------------------########## IOPS ##########--------------------
problem += lpSum((list(x) * (t_w + t_r))[i] for i in range(N)) <= m * np.dot(
    cassandra.vm_IOPS, list(mt)
)

# 3: only one type of VM used in the cluster
# --------------------########## ONEVM ##########--------------------
problem += pulp.lpSum(mt[i] for i in range(N)) == 1

# 4: continous relaxation of placement vector to avoid a bunch of binary variables.
# --------------------########## RELAXATION ##########--------------------
# at the end, if x[i] > 0.5 --> IaaS, otherwise DBaaS
for i in range(N):
    problem += x[i] <= 1

# there is a good chance that this can be dropped as it is already constrained
# by the definition of x with lowBound=0 and upBound=1

# --------------------########## ATLEAST3VMS ##########--------------------
problem += m >= 3

print(f"Items: {s}")
print(f"Initial Displacement: {x}")
solver = pulp.getSolver("PULP_CBC_CMD")
result = problem.solve(solver)
print(f"Final Displacement: {x}")
# cost of Dynamo if all the items were stored there
cost_dynamo = dynamoDB.estimateCost(t_read=t_r, t_write=t_w, db_size=sum(s))

for i in range(13):
    if mt[i] == 1:
        vm_type = i
        break
cost_cassandra = cassandra.estimateCost(noVMs=m.value, which_vm=vm_type)

print(
    f"The best solution is: {'Dynamo' if cost_dynamo > cost_cassandra else 'Cassandra'} and costs {max(cost_cassandra,cost_dynamo)}",
)
