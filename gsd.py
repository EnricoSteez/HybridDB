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
    while max_tp <= 2000:
        while items_size <= 1000:
            print(
                f"Starting optimisation with N={N}, size={int(items_size) if items_size >= 1 else prettyprint}, max_tp={max_tp}, distribution: zipfian (skew={skew})"
            )
            os.system(
                f"python3 ilp_solve.py {N} {items_size:.1f} {max_tp} zipfian {skew} results/{skew}/{N}_{items_size}MB_{max_tp}IOPS.txt"
            )
            # text = f"Optimisation finished: 10000 items, sizes={items_size}MB, tot tp = {max_tp}IO/s"
            # requests.get(
            #     f"https://api.telegram.org/bot{api_key}/sendMessage?chat_id={chat_id}&text={text}"
            # )
            items_size *= 10
        max_tp *= 10
    skew += 1
