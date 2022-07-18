from openpyxl import Workbook

wb=Workbook()
filename = "../workloads.xlsx"
ws = wb.active
with open("hybridWorkloads.txt","r") as file:
    for line in file.readlines():
        ws.append(line)
wb.save(filename=filename)
