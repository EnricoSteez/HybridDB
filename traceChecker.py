from cmath import inf


items = set()
count_lines = 0
up = 0
down = inf
with open("sizes.txt", "r") as file:
    for line in file:
        count_lines += 1
        line = line.split()
        item = int(line[0])
        items.add(item)
        if item > up:
            up = item
        if item < down:
            down = item

    print(f"Max = {up}, Min = {down}")

    values_range = up - down
    file.seek(0)
    up_second_phase = 0
    down_second_phase = inf
    for line in file:
        item = int(line.split()[0])
        item = (item - down) / values_range * 400
        if item > up_second_phase:
            up_second_phase = item
        if item < down_second_phase:
            down_second_phase = item

    print(f"After normalization: Max = {up_second_phase}, Min = {down_second_phase}")
