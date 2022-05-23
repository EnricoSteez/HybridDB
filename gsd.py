# import requests
import os

api_key = "5187998346:AAFPwXQsNR1EQi2e7osOswEsFHAjDxiTpMk"
chat_id = "907706827"
N = 10000
max_tp = 200
items_size = 0.1
prettyprint = "01"
skew = 1
while skew <= 4:
    max_tp = 200
    while max_tp <= 2000:
        items_size = 0.1
        while items_size <= 1000:
            print(
                f"Starting optimisation with N={N}, size={int(items_size) if items_size >= 1 else prettyprint}, max_tp={max_tp}, distribution: zipfian (skew={skew})"
            )
            os.system(
                f"python3 ilp_solve_clustersize.py {N} {items_size:.1f} {max_tp} zipfian {skew} results/{skew}/{N}_{int(items_size) if items_size >= 1 else prettyprint}MB_{max_tp}IOPS.txt"
            )
            items_size *= 10
        max_tp *= 10
    skew += 1
