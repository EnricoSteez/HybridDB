import numpy as np

"""Parameters file"""
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

vm_IOPS = dict(zip(vm_types, vm_IOPS))

vm_bandwidths = [
    450,
    750,
    1000,
    2000,
    8000,
    10000,
    425,
    850,
    1700,
    3500,
    7000,
    14000,
    19000,
]

vm_bandwidths = dict(zip(vm_types, vm_bandwidths))

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

vm_costs = dict(zip(vm_types, vm_costs))

# GCP
# Machine type	 Virtual CPUs	Memory	    Price (USD)
# e2-standard-16	16	        64GB	    $0.536048
# e2-standard-32	32	        128GB	    $1.072096

# AWS volume pricing
# General Purpose SSD (gp3) - Storage	$0.0924/GB-month
# General Purpose SSD (gp3) - IOPS	3,000 IOPS free and $0.0058/provisioned IOPS-month over 3,000
# General Purpose SSD (gp3) - Throughput	125 MB/s free and $0.0462/provisioned MB/s-month over 125

volumes = ["gp2", "gp3", "io1", "st1", "sc1"]

COST_VOLUME_STORAGE = [
    0.1155,
    0.0924,
    0.1449,
    0.525,
    0.01764,
]  # / 30 / 24 / 1e3  # per MB per hour
COST_VOLUME_STORAGE = np.multiply(COST_VOLUME_STORAGE, 1 / 30 / 24 / 1e3)
COST_VOLUME_STORAGE = dict(zip(volumes, COST_VOLUME_STORAGE))

COST_VOLUME_IOPS = [0, 0.0058, 0.0756, 0, 0]  # per IOPS-month
COST_VOLUME_IOPS = np.multiply(COST_VOLUME_IOPS, 1 / 30 / 24)  # per IOPS-hour
COST_VOLUME_IOPS = dict(zip(volumes, COST_VOLUME_IOPS))

COST_VOLUME_THROUGHPUT = [0, 0.0462 / 30 / 24, 0, 0, 0]  # $ per MB/s per hour
COST_VOLUME_THROUGHPUT = dict(zip(volumes, COST_VOLUME_THROUGHPUT))
# TODO update cost formulation to include different volume costs
# TODO convert everything to MiB or MB
# MB to MiB --> * 10^6 / 2^20
# MiB to MB --> * 2^20 / 10^6
# General Purpose SSD (gp3) - Storage	    $0.0924/GB-month
# General Purpose SSD (gp3) - IOPS	        3,000 IOPS free and $0.0058/provisioned IOPS-month over 3,000
# General Purpose SSD (gp3) - Throughput	125 MB/s free and $0.0462/provisioned MB/s-month over 125
# General Purpose SSD (gp2) Volumes	        $0.1155 per GB-month of provisioned storage
# Provisioned IOPS SSD (io1) Volumes	    $0.1449 per GB-month of provisioned storage AND $0.0756 per provisioned IOPS-month
# Throughput Optimized HDD (st1) Volumes	$0.0525 per GB-month of provisioned storage
# Cold HDD (sc1) Volumes                    $0.01764 per GB-month of provisioned storage
MAX_VOLUME_IOPS = [
    16000,
    16000,
    64000,
    500,
    250,
]  # 16 KiB I/O for SSD(gp2,gp3,io1), 1MiB I/O for HDD(sc1,st1)
IO_FACTOR = [
    10 ** 6 / 2 ** 10 / 16,  # MB to KiB, then 1 I/O every 16
    10 ** 6 / 2 ** 10 / 16,  # MB to KiB, then 1 I/O every 16
    10 ** 6 / 2 ** 10 / 16,  # MB to KiB, then 1 I/O every 16
    10 ** 6 / 2 ** 20,  # MB to MiB, then 1 I/O every MB
    10 ** 6 / 2 ** 20,  # MB to MiB, then 1 I/O every MB
]
IO_FACTOR = dict(zip(volumes, IO_FACTOR))
MAX_VOLUME_IOPS = dict(zip(volumes, MAX_VOLUME_IOPS))
MAX_VOLUME_THROUGHPUT = [250, 1000, 1000, 500, 250]  # MiB/s
MAX_VOLUME_THROUGHPUT = dict(zip(volumes, MAX_VOLUME_THROUGHPUT))

# "c5.12xlarge",
# "c5.18xlarge",
# "c5.24xlarge",
# "c5.2xlarge",
# "c5.4xlarge",
# "c5.9xlarge",
# "c5.large",
# "c5.xlarge",
# "c5a.12xlarge",
# "c5a.16xlarge",
# "c5a.24xlarge",
# "c5a.2xlarge",
# "c5a.4xlarge",
# "c5a.8xlarge",
# "c5a.large",
# "c5a.xlarge",
# "c5d.12xlarge",
# "c5d.18xlarge",
# "c5d.24xlarge",
# "c5d.2xlarge",
# "c5d.4xlarge",
# "c5d.9xlarge",
# "c5d.large",
# "c5d.xlarge",
# "c5n.18xlarge",
# "c5n.2xlarge",
# "c5n.4xlarge",
# "c5n.9xlarge",
# "c5n.large",
# "c5n.xlarge",
# "c6g.12xlarge",
# "c6g.16xlarge",
# "c6g.2xlarge",
# "c6g.4xlarge",
# "c6g.8xlarge",
# "c6g.large",
# "c6g.medium",
# "c6g.xlarge",
# "c6gd.12xlarge",
# "c6gd.16xlarge",
# "c6gd.2xlarge",
# "c6gd.4xlarge",
# "c6gd.8xlarge",
# "c6gd.large",
# "c6gd.medium",
# "c6gd.xlarge",
# "c6gn.12xlarge",
# "c6gn.16xlarge",
# "c6gn.2xlarge",
# "c6gn.4xlarge",
# "c6gn.8xlarge",
# "c6gn.large",
# "c6gn.medium",
# "c6gn.xlarge",
# "c6i.12xlarge",
# "c6i.16xlarge",
# "c6i.24xlarge",
# "c6i.2xlarge",
# "c6i.32xlarge",
# "c6i.4xlarge",
# "c6i.8xlarge",
# "c6i.large",
# "c6i.xlarge",
# "d2.2xlarge",
# "d2.4xlarge",
# "d2.8xlarge",
# "d2.xlarge",
# "d3.2xlarge",
# "d3.4xlarge",
# "d3.8xlarge",
# "d3.xlarge",
# "i3.16xlarge",
# "i3.2xlarge",
# "i3.4xlarge",
# "i3.8xlarge",
# "i3.large",
# "i3.xlarge",
# "i3en.12xlarge",
# "i3en.24xlarge",
# "i3en.2xlarge",
# "i3en.3xlarge",
# "i3en.6xlarge",
# "i3en.large",
# "i3en.xlarge",
# "r4.16xlarge",
# "r4.2xlarge",
# "r4.4xlarge",
# "r4.8xlarge",
# "r4.large",
# "r4.xlarge",
# "r5.12xlarge",
# "r5.16xlarge",
# "r5.24xlarge",
# "r5.2xlarge",
# "r5.4xlarge",
# "r5.8xlarge",
# "r5.large",
# "r5.xlarge",
# "r5a.12xlarge",
# "r5a.16xlarge",
# "r5a.24xlarge",
# "r5a.2xlarge",
# "r5a.4xlarge",
# "r5a.8xlarge",
# "r5a.large",
# "r5a.xlarge",
# "r5ad.12xlarge",
# "r5ad.16xlarge",
# "r5ad.24xlarge",
# "r5ad.2xlarge",
# "r5ad.4xlarge",
# "r5ad.8xlarge",
# "r5ad.large",
# "r5ad.xlarge",
# "r5b.12xlarge",
# "r5b.16xlarge",
# "r5b.24xlarge",
# "r5b.2xlarge",
# "r5b.4xlarge",
# "r5b.8xlarge",
# "r5b.large",
# "r5b.xlarge",
# "r5d.12xlarge",
# "r5d.16xlarge",
# "r5d.24xlarge",
# "r5d.2xlarge",
# "r5d.4xlarge",
# "r5d.8xlarge",
# "r5d.large",
# "r5d.xlarge",
# "r5n.12xlarge",
# "r5n.16xlarge",
# "r5n.24xlarge",
# "r5n.2xlarge",
# "r5n.4xlarge",
# "r5n.8xlarge",
# "r5n.large",
# "r5n.xlarge",
# "r6g.12xlarge",
# "r6g.16xlarge",
# "r6g.2xlarge",
# "r6g.4xlarge",
# "r6g.8xlarge",
# "r6g.large",
# "r6g.medium",
# "r6g.xlarge",
# "r6i.12xlarge",
# "r6i.16xlarge",
# "r6i.24xlarge",
# "r6i.2xlarge",
# "r6i.32xlarge",
# "r6i.4xlarge",
# "r6i.8xlarge",
# "r6i.large",
# "r6i.xlarge",
# "x1.16xlarge",
# "x1.32xlarge",
# "x2idn.16xlarge",
# "x2idn.24xlarge",
# "x2idn.32xlarge",
# "x2iedn.16xlarge",
# "x2iedn.24xlarge",
# "x2iedn.2xlarge",
# "x2iedn.32xlarge",
# "x2iedn.4xlarge",
# "x2iedn.8xlarge",
# "x2iedn.xlarge",
# "z1d.12xlarge",
# "z1d.2xlarge",
# "z1d.3xlarge",
# "z1d.6xlarge",
# "z1d.large",
# "z1d.xlarge"
