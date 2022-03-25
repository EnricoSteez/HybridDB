from cmath import inf


objects = dict()  # key: object_id -> value: (size, tp_read, tp_write)
min_ts = inf
max_ts = 0
with open("IBMObjectStoreTrace000Part0", "r") as file, open(
    "traces.txt", "w"
) as output:
    for line in file:
        line = line.split()
        ts = int(line[0])
        op = line[1].split(".")[1]  # REST.GET.OBJECT -> GET
        object_id = line[2]
        object_size = line[3]

        if object_id in objects:
            value = objects[object_id]
            if op == "GET" or op == "HEAD":  # READ
                new_value = (value[0], value[1] + 1, value[2])
            else:  # WRITE
                new_value = (value[0], value[1], value[2] + 1)

            objects[object_id] = new_value

        else:
            if op == "GET" or op == "HEAD":  # READ
                objects[object_id] = (object_size, 1, 0)
            else:
                objects[object_id] = (object_size, 0, 1)

        if ts > max_ts:
            max_ts = ts
        if ts < min_ts:
            min_ts = ts

    for size, tp_r, tp_w in objects.values():
        output.write(f"{size} {tp_r} {tp_w}\n")

    output.truncate(output.tell() - 1)  # remove trailing newline
