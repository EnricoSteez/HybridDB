import os
import sys
import requests
import urllib.parse
from time import time
from time import gmtime
from time import strftime

token = "5187998346:AAFPwXQsNR1EQi2e7osOswEsFHAjDxiTpMk"
chat_id = "907706827"

if os.path.exists("../results/*"):
    os.remove("../results/*")
if os.path.exists("../placements/*"):
    os.remove("../placements/*")
if os.path.exists("../workloads.txt"):
    os.remove("../workloads.txt")
if os.path.exists("../hybridFiles.xlsx"):
    os.remove("../hybridFiles.xlsx")

t0 = time()
N = 1000
count = 0
skew = 2
for percent_read1 in [0.5, 0.95]:
    for tot_tp1 in [0.1, 100]:
        for items_size1 in [0.0001, 1]:
            for percent_read2 in [0.5, 0.95]:
                for tot_tp2 in [0.1, 100]:
                    for items_size2 in [0.0001, 1]:
                        count += 1
                        if (
                            os.system(
                                f"python3 ilp_no_dynamo_two_zipfians.py "
                                f"{N} {items_size1} {tot_tp1} {skew} {percent_read1} "
                                f"{N} {items_size2} {tot_tp2} {skew} {percent_read2} "
                            )
                            != 0
                        ):
                            sys.exit("Error, stopping")
tot_time = time() - t0
message = f"Tutto finito! Did {count} optimisations, it took me {strftime('%H:%M:%S',gmtime(tot_time))}!"
requests.get(
    f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={urllib.parse.quote(message)}&disable_notification=True"
)
