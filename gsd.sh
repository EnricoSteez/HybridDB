#!/bin/sh
for ((max_tp = 200 ; max_tp < 20001 ; max_tp*=10));; do
    for ((items_size = 100 ; items_size < 1000001 ; items_size*=10));; do
    	python3 lp_solve_novmtype.py 1000 $(items_size) $(max_tp) zipfian 1 > "$(items_size)KB_$(max_tp)IOPS.txt"
	done
done
