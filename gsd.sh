#!/bin/sh
API_KEY="5187998346:AAFPwXQsNR1EQi2e7osOswEsFHAjDxiTpMk"
CHAT_ID="907706827"
for ((max_tp = 200 ; max_tp < 20001 ; max_tp*=10)); do
    for ((items_size = 100 ; items_size < 1000001 ; items_size*=10)); do
        python3 lp_solve_novmtype.py 1000 ${items_size} ${max_tp} zipfian 1 > "${items_size}KB_${max_tp}IOPS.txt"
        text="Optimisation finished: 1000 items, sizes=${items_size}KB, max tp = ${max_tp}"
        curl -s "https://api.telegram.org/bot${API_KEY}/sendMessage?chat_id=${CHAT_ID}&text=${text}"
    done
done