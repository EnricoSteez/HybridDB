# import requests
import os

api_key = "5187998346:AAFPwXQsNR1EQi2e7osOswEsFHAjDxiTpMk"
chat_id = "907706827"
max_tp = 200
items_size = 0.1
skew = 1
while skew <= 4:
    while max_tp <= 2000:
        while items_size <= 1000:
            os.system(
                f"python3 ilp_solve.py 10000 ${items_size} ${max_tp} zipfian {skew} results/${items_size}MB_${max_tp}IOPS_{skew}.txt"
            )
            # text = f"Optimisation finished: 10000 items, sizes={items_size}MB, tot tp = {max_tp}IO/s"
            # requests.get(
            #     f"https://api.telegram.org/bot{api_key}/sendMessage?chat_id={chat_id}&text={text}"
            # )
            items_size *= 10
        max_tp *= 10
    skew += 1
