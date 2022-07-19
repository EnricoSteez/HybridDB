from openpyxl import Workbook

wb=Workbook()
filename = "../workloads.xlsx"
ws = wb.active
with open("../results/hybridWorkloads.txt","r") as file:
    for line in file.readlines():
        ws.append(line.split())
wb.save(filename=filename)
