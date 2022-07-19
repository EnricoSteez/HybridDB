from openpyxl import Workbook
import os

wb=Workbook()
filename = "../results/workloads.xlsx"
os.system(f"rm {filename}")
ws = wb.active
headlines = ["Item ID", "Size [MB]", "Popularity [IOPS]", "Bandwidth Required [MB/s]", "Placement"]
with open("../results/workloads.txt","r") as file:
    for line in file.readlines():
        ws.append(line.split())
wb.save(filename=filename)
