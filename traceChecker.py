items = set()
count_lines = 0
with open("IBMObjectStoreTrace000Part0", "r") as file:
    for line in file:
        count_lines += 1
        line = line.split()
        item = int(line[0])
        items.add(item)

print(f"Tot lines: {count_lines}, tot items: {len(items)}")
