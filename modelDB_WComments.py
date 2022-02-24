import numpy as np
import csv

class dynamoDB:
    def __init__(self):
        self.cost_write = 1.25 / 1e6
        self.cost_read = 0.25 / 1e6

        #Unidades de solicitação de gravação	1,25 USD por milhão de unidades de solicitação de gravação
        #Unidades de solicitação de leitura	0,25 USD por milhão de unidades de solicitação de gravação

    def estimateCost(self, t_read, t_write, db_size):
        return t_read * self.cost_read + t_write * self.cost_write



class cassandra:
    def __init__(self):
        self.replication_factor = 3
        

    def VMprice_per_hour(self, type):
        if type == "m4.large":
            return 0.1
        elif type == "m4.xlarge":
            return 0.2
        elif type == "m4.2xlarge":
            return 0.4
        elif type == "m4.4xlarge":
            return 0.8
        elif type == "m4.10xlarge":
            return 2.0
        elif type == "m4.16xlarge":
            return 3.2
        elif type == "i3.large":
            return 0.156
        elif type == "i3.xlarge":
            return 0.312
        elif type == "i3.2xlarge":
            return 0.624
        elif type == "i3.4xlarge":
            return 1.248
        elif type == "i3.8xlarge":
            return 2.496
        elif type == "i3.16xlarge":
            return 4.992
        elif type == "i3.metal":
            return 4.992

        print("Wrong VM type")
        return -1


    def maxIOPs(self, type):
        if type == "m4.large":
            return 3600.0
        elif type == "m4.xlarge":
            return 6000.0
        elif type == "m4.2xlarge":
            return 8000.0
        elif type == "m4.4xlarge":
            return 16000.0
        elif type == "m4.10xlarge":
            return 32000.0
        elif type == "m4.16xlarge":
            return 65000.0
        elif type == "i3.large":
            return 3000.0
        elif type == "i3.xlarge":
            return 6000.0
        elif type == "i3.2xlarge":
            return 12000.0
        elif type == "i3.4xlarge":
            return 16000.0
        elif type == "i3.8xlarge":
            return 32500.0
        elif type == "i3.16xlarge":
            return 65000.0
        elif type == "i3.metal":
            return 80000.0

        print("Wrong VM type")
        return -1

    def Cost_cassandra(self, noVM, VMtype):
        priceVM = self.VMprice_per_hour(VMtype)
        cost = noVM * priceVM
        return cost

    def estimateCost(self, tr_read, tr_write, db_size):
        list_price = []
        # for each type of VM, estimate the number of needed VMs and the total cost
        for vm_type in ["m4.large","m4.xlarge","m4.2xlarge","m4.4xlarge","m4.10xlarge","m4.16xlarge"#]:
                        ,"i3.large","i3.xlarge","i3.2xlarge","i3.4xlarge","i3.8xlarge","i3.16xlarge","i3.metal"]:

            tr_total_s = (tr_read + tr_write)/3600.0 # total throughput in seconds

            noVMs = self.numberVMs(db_size, tr_total_s, vm_type) * self.replication_factor 
            cost = self.Cost_cassandra(noVMs, vm_type)
            list_price.append([db_size, tr_read, tr_write, tr_total_s, vm_type, noVMs, cost])

        list_price.sort(key=lambda x: x[-1]) 

        #return cost, noVMs, vm_type of the cheaper Cassandra cluster configuration
        return list_price[0][-1], list_price[0][-2], list_price[0][-3] 



dynamoDB = dynamoDB()
cassandra = cassandra()
perc_hot_data = 0.1
perc_request_hot = 0.9

list_data = []
for db_size in [1e3, 1e4, 1e5, 1e6]:
    for tr_write in [1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9]:
        for tr_read in [1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9]:
            #throughput per hour

            #only dynamo
            dynamo_cost = dynamoDB.estimateCost(tr_read, tr_write, db_size)

            #only cassandra
            cassandra_cost, noVM, vmType = cassandra.estimateCost(tr_read, tr_write, db_size)

            #hybrid 

            hybrid_dynamo_cost = dynamoDB.estimateCost(tr_read*(1-perc_request_hot), tr_write*(1-perc_request_hot), db_size*(1-perc_hot_data))
            hybrid_cassandra_cost,  hybrid_noVM,  hybrid_vmType = cassandra.estimateCost(tr_read*perc_request_hot, tr_write*perc_request_hot, db_size*perc_hot_data)


            list_data.append([db_size, tr_read, tr_write, dynamo_cost, cassandra_cost, noVM, vmType, hybrid_dynamo_cost+hybrid_cassandra_cost, hybrid_dynamo_cost, hybrid_cassandra_cost,  hybrid_noVM,  hybrid_vmType])



with open('DB_cost.csv', mode='w') as cost_file:
    cost_write = csv.writer(cost_file, delimiter=';')
    cost_write.writerow(["db_size", "tr_read", "tr_write", "DynamoCost", "CassandraCost", "CassandraVMs", "CassandraVMtype", "hybridCost", "hybridDynamoCost", "hybridCassandraCost", "hybridCassandraVMs", "hybridCassandraVMtype"])

    for d in list_data:
        cost_write.writerow(d)


#------------------------WHY IS THIS PART HERE?------------------------

#Throughput (ops/s)
tr = 1000
db_size = 1000

tr_read = tr/2.0 * 3600.0
tr_write = tr/2.0 * 3600.0

dynamo_cost = dynamoDB.estimateCost(tr_read, tr_write, db_size)
cassandra_cost, noVM, vmType = cassandra.estimateCost(tr_read, tr_write, db_size)

#hybrid 
hybrid_dynamo_cost = dynamoDB.estimateCost(tr_read*(1-perc_request_hot), tr_write*(1-perc_request_hot), db_size*(1-perc_hot_data))
hybrid_cassandra_cost,  hybrid_noVM,  hybrid_vmType = cassandra.estimateCost(tr_read*perc_request_hot, tr_write*perc_request_hot, db_size*perc_hot_data)


print("db_size " + str(db_size) + " tr " + str(tr) + " tr_read " + str(tr_read) + " tr_write " + str(tr_write) )
print("dynamo cost " + str(dynamo_cost))
print("cassandra cost " + str(cassandra_cost) + " cassandra vm " + str(noVM) + " cassandra type " + str(vmType))
print("hybrid cost " + str(hybrid_cassandra_cost+hybrid_dynamo_cost) + " dynamo cost " + str(hybrid_dynamo_cost) + " cassandra cost " + str(cassandra_cost) + " cassandra vm " + str(noVM) + " cassandra type " + str(vmType))
print()