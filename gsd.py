# import requests
import os
import sys
import requests
import urllib.parse
from time import time
from time import gmtime
from time import strftime

token = "5187998346:AAFPwXQsNR1EQi2e7osOswEsFHAjDxiTpMk"
chat_id = "907706827"
N = 1000
t0 = time()
for percent_read in [0.9, 0.95, 0.99]:
    for skew in [1, 2, 3, 4]:
        for tot_tp in [0.001, 0.01, 0.1, 1, 10, 100, 1000]:
            for items_size in [0.00001, 0.0001, 0.001, 0.01, 0.1, 1, 10, 100, 1000]:
                message = (
                    f"Starting optimisation: N={N}, items_size={items_size}, ",
                    f"tot_tp={tot_tp}, distribution: zipfian (skew={skew})",
                    f"reads: {percent_read:.1%}",
                )
                print(message)
                if (
                    os.system(
                        f"python3 ilp_find_best_cluster.py {N} {items_size} {tot_tp} zipfian {skew} {percent_read}"
                    )
                    != 0
                ):
                    sys.exit("Error, stopping")
tot_time = time() - t0
message = f"Tutto finito, it took {strftime('%H:%M:%S',gmtime(tot_time))}!"
requests.get(
    f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={urllib.parse.quote(message)}&disable_notification=True"
)
