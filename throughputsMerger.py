with open("readStats.txt", "r") as readsFile, open(
    "writeStats.txt", "r"
) as writesFile, open("sizes.txt", "r") as sizesFile, open(
    "sizes.txt", "r"
) as sizesFile, open(
    "throughputs.txt", "w"
) as file1, open(
    "throughputsJava.txt", "w"
) as file2:
    i = 0
    while i < 1e6:
        line = readsFile.readline()
        key = line.split()[0]
        tp_r = line.split()[1]
        tp_w = writesFile.readline().split()[1]
        size = sizesFile.readline().split()[0]
        to_write = f"{key} {size} {tp_r} {tp_w}\n"
        file1.write(to_write)
        file2.write(to_write)
        i += 1
    file1.truncate(file1.tell() - 1)
    file2.truncate(file2.tell() - 1)
