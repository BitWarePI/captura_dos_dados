import psutil as ps
import pandas as pd
import platform as pf
import datetime as dt

system = pf.system;
datetime = dt.datetime.now()

cpu = ps.cpu_times(percpu=False)
mem = ps.virtual_memory()
disk = ps.disk_usage("/")
temp = ps.sensors_temperatures(fahrenheit=False)

dadosMaq = {
    "datetime": [datetime],
    "id": [],
    "operation_system": [system],
    "cpu_percent": [ps.cpu_percent(interval=0.1)],
    "ram_percent": [mem.percent],
    "disk_percent": [disk.percent]
}

dadosMaq["operation_system"].append(system)

dadosMaq = {
    "datetime": [datetime],
    "id": [],
    "operation_system": [],
    "cpu_percent": [],
    "ram_percent": []
}

dadosTemp = {
    "datetime": [],
    "core": [],
    "tempAtual": [],
    "tempAlta": [],
    "tempCritica": [],
}

for index, item in enumerate(temp["coretemp"]):
    dadosTemp["core"].append(temp["coretemp"][index].label)
    dadosTemp["tempAtual"].append(temp["coretemp"][index].high)
    dadosTemp["tempCritica"].append(temp["coretemp"][index].critical)