import requests
import os

api_key = "5187998346:AAFPwXQsNR1EQi2e7osOswEsFHAjDxiTpMk"
chat_id = "907706827"
max_tp = 200
items_size = 0.1
while max_tp < 2001:
    while items_size < 1001:
        os.system(
            "python3 lp_solve_novmtype.py 1000 ${items_size} ${max_tp} zipfian 1 results/${items_size}KB_${max_tp}IOPS.txt"
        )
        text = f"Optimisation finished: 1000 items, sizes={items_size}MB, tot tp = {max_tp}IO/s"
        requests.get(
            f"https://api.telegram.org/bot{api_key}/sendMessage?chat_id={chat_id}&text={text}"
        )
        items_size *= 10
    max_tp *= 10
