sizes = set()
with open("IBMObjectStoreTrace005Part3", "r") as file, open("sizes", "w") as output:
    for line in file:
        line = line.split()
        if len(line) >= 4:
            object_id = line[2]
            object_size = line[3]
            if not object_id in sizes:
                sizes.add(object_id)
                output.write(f"{object_size}\n")

    output.truncate(output.tell()-1)  # remove trailing newline
