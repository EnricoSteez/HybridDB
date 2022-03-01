import pulp as pulp
from pulp import constants
from pulp.pulp import lpSum
import params
import numpy as np


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


#%%
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

    def __init__(self) -> None:
        pass

    ### returns the cost per hour ###
    def estimateCost(self, noVMs: int, which_vm: int) -> float:
        # print(self.vm_costs)
        # print(which_vm)
        return noVMs * self.vm_costs[which_vm]

    def getIops(self, which_vm: int):
        return self.vm_IOPS[which_vm]

    def getType(self, which_type: int):
        return self.vm_types[which_type]


#%%
dynamoDB = dynamoDB()
cassandra = cassandra()
# Number of items N
N = params.N
# Placement vector x
x = pulp.LpVariable.dicts("placement", (i for i in range(N)), lowBound=0, upBound=1)

# Item sizes (Bytes) -> [1B-1GB] (s)
s = (2e30 - 1) * np.random.rand(N) + 1


# Items' read/write throughput (tr, tw) (ops per second)
t_r = np.random.randint(1, 50, N)
t_w = np.random.randint(1, 50, N)
iops = [x + y for (x, y) in zip(t_r, t_w)]
# Number of VMs
# (in the Mathematical formulation, this corresponds to M)
m = pulp.LpVariable("M", lowBound=3, cat=constants.LpInteger)
# Type of VM employed, we assume we are going to use only one type (see pdf)
# (in the PDF formulation, this corresponds to \vec{m})
# THIS VERSION AIMS AT MAKING THE PROBLEM FEASIBLE. THE MACHINE TYPE WILL THEN BE
# A PARAMETER RATHER THAN A DECISION VARIABLE
# WE WILL SOLVE A STANDALONE INSTANCE OF THE PROBLEM FOR EVERY TYPE OF MACHINE
# AND COMPARE THE SOLUTIONS

print(f"Items: {s}")
solver = pulp.getSolver("PULP_CBC_CMD")

for mt in range(13):
    print(f"Instantiating the problem with {cassandra.getType(mt)}")
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
    # 1: total size of the items will not exceed
    # the limit of MAX SIZE TB per employed machine

    problem += (
        lpSum(x[i] * s[i] for i in range(N))
        <= params.MAX_SIZE * m / cassandra.replication_factor
    )

    # np.dot(list(x), s) * cassandra.replication_factor / m.value() <= params.MAX_SIZE

    # 2: enough IOPS in the machines to sustain the total throughput of all data.
    # --------------------########## IOPS ##########--------------------

    # contains iops (t_r+t_w) of only cassandra items
    # the iops of indexes of items stored in Dynamo
    # are 0
    cassandra_iops = [x * y for (x, y) in zip(x, iops)]

    # sum of all iops of items stored in cassandra <= total iops of m machines
    problem += lpSum(cassandra_iops[i] for i in range(N)) <= m * cassandra.getIops(
        which_vm=mt
    )

    # 3: only one type of VM used in the cluster
    # --------------------########## ONEVM ##########--------------------
    # problem += pulp.lpSum(mt[i] for i in range(N)) == 1
    # THIS CAN BE DROPPED

    # 4: Ensuring that mt[i] is binary
    # already done in the definition of the variable
    # CAN BE DROPPED AS WELL

    # --------------------########## ATLEAST3VMS ##########--------------------
    problem += m >= 3

    result = problem.solve(solver)
    print(f"Cassandra cluster will have {m.value()} machines")
    print(f"Final Displacement: {x}")
    # cost of Dynamo if all the items were stored there
    cost_dynamo = dynamoDB.estimateCost_hour(
        placement=x, t_read=t_r, t_write=t_w, db_size=sum(s)
    )
    print(f"Cost of Dynamo = {cost_dynamo}")

    cost_cassandra = cassandra.estimateCost(noVMs=m.value(), which_vm=mt)
    print(f"Cost of Cassandra = {cost_cassandra}")

    print(
        f"The best solution is: {'Dynamo' if cost_dynamo > cost_cassandra else 'Cassandra'}\n\n\n",
    )

# %%
