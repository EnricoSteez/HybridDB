from asyncore import read
import os
import re

statsdir = "stats/"
readStats = dict()
writeStats = dict()

# goodLine = re.compile("user[0-9]+ [0-9]+(\r?\n|\r)")
goodKey = re.compile("user[0-9]+")

for filename in os.listdir(statsdir):
    if not filename.startswith("."):
        with open(os.path.join(statsdir, filename), mode="r") as file:
            print(f"Analysing file {filename}")
            data = file.readlines()
            print(f"Contains {len(data)} lines")
            for line in data:
                # if re.match( goodLine, line ):  # eliminate garbage resulting from concurrency
                kv = line.split()
                k = kv[0]
                if not re.match(goodKey, k) or len(kv) != 2:
                    continue
                try:
                    v = int(kv[1])
                except ValueError:
                    continue

                if filename.startswith("r"):
                    if k in readStats:
                        readStats[k] += v
                    else:
                        readStats[k] = v
                else:
                    if k in writeStats:
                        writeStats[k] += v
                    else:
                        writeStats[k] = v
                        if not k in readStats:
                            readStats[k] = 0
                        # items that have been inserted (write) but never read

# sort by throughput value
readStats = dict(sorted(readStats.items(), key=lambda kv: kv[1], reverse=True))
writeStats = dict(sorted(writeStats.items(), key=lambda kv: kv[1], reverse=True))

with open("readStats.txt", mode="w") as file:
    for k, v in readStats.items():
        file.write(f"{k} {v}\n")
    file.truncate(file.tell()-1)

with open("writeStats.txt", mode="w") as file:
    for k, v in writeStats.items():
        file.write(f"{k} {v}\n")
    file.truncate(file.tell()-1)

print("DONE!")
