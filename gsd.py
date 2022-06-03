# import requests
import os

token = "5187998346:AAFPwXQsNR1EQi2e7osOswEsFHAjDxiTpMk"
chat_id = "907706827"
N = 10000
tot_tp = 200
items_size = 0.1
prettyprint = "01"
skew = 1
while skew <= 4:
    tot_tp = 0.001
    while tot_tp <= 1000:
        items_size = 0.00001
        while items_size <= 1000:
            message = (
                f"Starting optimisation with N={N}, ",
                f"size={int(items_size) if items_size >= 1 else prettyprint}, ",
                f"max_tp={tot_tp}, distribution: zipfian (skew={skew})",
            )
            os.system(
                f"python3 ilp_find_best_cluster.py {N} {items_size} {tot_tp} zipfian {skew}"
            )
            url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}&disable_notification=True"
            os.system(f"curl {url}")
            items_size *= 10
        tot_tp *= 10
    skew += 1
