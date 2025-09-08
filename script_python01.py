import psutil as ps
import pandas as pd
import platform as pf
import datetime as dt
import os
import time
from getmac import get_mac_address

system = pf.system();
while True:
    datetime = dt.datetime.now()

    cpu = ps.cpu_times(percpu=False)
    mem = ps.virtual_memory()
    disk = ps.disk_usage("/")
    temp = ps.sensors_temperatures(fahrenheit=False)

    dadosMaq = {
    "datetime": [datetime],
    "operation_system": [system],
    "cpu_percent": [ps.cpu_percent(interval=1)],
    "ram_percent": [mem.percent],
    "disk_percent": [disk.percent],
    "mac_address": [get_mac_address()]
    }

    #dadosMaq["operation_system"].append(system)

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

    print(dadosMaq)
    df = pd.DataFrame(dadosMaq)
    if(os.path.exists('leituras.csv')):
        df.to_csv("leituras.csv", mode="a", encoding="utf-8", index=False, sep=";", header=False)
    else:
        df.to_csv("leituras.csv", mode="a", encoding="utf-8", index=False, sep=";")
        firstTime = False
    time.sleep(9)