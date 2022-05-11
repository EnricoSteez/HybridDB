"""Numerical parameters file"""
MAX_SIZE = 4 * 1e6  # 4TB with MB as baseline
REPLICATION_FACTOR = 3
COST_DYNAMO_WRITE_UNIT = 1.4842 / 1e6  # cost per million write requests: 1.4842 / 1e6
COST_DYNAMO_READ_UNIT = 0.2968 / 1e6  # cost per million read requests: 0.2968 / 1e6
COST_DYNAMO_STORAGE = (
    0.29715 / 30 / 24 / 1e3
)  # 0.29715 cost per GB per month -> per Mega byte per hour
# period (hours) of stability over which the optimizer calculates the total cost
WORKLOAD_STABILITY = 10

vm_types = [
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
    # "e2-standard-16",
    # "e2-standard-32",
]

vm_IOPS = [
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
    # 0.536048,
    # 1.072096,
]

# GCP
# Machine type	 Virtual CPUs	Memory	    Price (USD)
# e2-standard-16	16	        64GB	    $0.536048
# e2-standard-32	32	        128GB	    $1.072096

# AWS volume pricing
# General Purpose SSD (gp3) - Storage	$0.0924/GB-month
# General Purpose SSD (gp3) - IOPS	3,000 IOPS free and $0.0058/provisioned IOPS-month over 3,000
# General Purpose SSD (gp3) - Throughput	125 MB/s free and $0.0462/provisioned MB/s-month over 125

COST_VOLUME_STORAGE = 0.0924 / 30 / 24 / 1e3  # per MB per hour
COST_VOLUME_IOPS = 0.0058 / 30 / 24  # per IOPS-hour
COST_VOLUME_THROUGHPUT = 0.0462 / 30 / 24  # $ per MB/s per hour
