import psutil as ps
import pandas as pd
import platform as pf
import datetime as dt
import os
import time
from getmac import get_mac_address
from datetime import datetime
import random
import boto3

system = pf.system();
while True:
    datetime = dt.datetime.now().replace(microsecond=0)
    mac = get_mac_address()

    cpu = ps.cpu_times(percpu=False)
    mem = ps.virtual_memory()
    disk = ps.disk_usage("/")
    #temp = ps.sensors_temperatures(fahrenheit=False)
    processos = list(ps.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']))

    # componentes_nomes = ["CPU", "GPU", "RAM"]

    # dadosTemp = {
    # "datetime": [],
    # "core": [],
    # "tempAtual": [],
    # "tempAlta": [],
    # "tempCritica": [],
    # }

    # if not temp:
    #     print("Não achou nenhum sensor de temperatura")
    # else:
    #     indice = 0;
    #     temperatura_CPU = 0;
    #     temperatura_GPU = 0;

    #     for sensor_name, entries in temp.items():
    #         for entry in entries:
    #             dadosTemp["datetime"].append(datetime.now())
    #             #dadosTemp["core"].append(entry.label or sensor_name)
    #             print(entry.label or sensor_name)
    #             dadosTemp["core"].append(componentes_nomes[indice])
    #             if(indice == 1):
    #                 temperatura_CPU = entry.current                        
    #             else:
    #                 temperatura_GPU = entry.current

    #             dadosTemp["tempAtual"].append(entry.current)
    #             dadosTemp["tempAlta"].append(entry.high if entry.high is not None else "N/A")
    #             dadosTemp["tempCritica"].append(entry.critical if entry.critical is not None else "N/A")
            
    #         if(indice == 2):
    #             indice = 0;
    #         else:
    #             indice += 1;
    
    cpu_percent = ps.cpu_percent(interval=1);
    temperatura_CPU = 30 + (cpu_percent * 0.6) + random.uniform(-2, 2)

    temperatura_CPU = max(30, min(90, temperatura_CPU))
    gpu_percent = cpu_percent + random.uniform(-10, 10)
    gpu_percent = max(0, min(100, gpu_percent))
    
    temperatura_GPU = 35 + (gpu_percent * 0.55) + random.uniform(-3, 3)
    temperatura_GPU = max(35, min(95, temperatura_GPU))

    dadosMaq = {
    "datetime": [datetime],
    "operation_system": [system],
    "cpu_percent": [cpu_percent],
    "gpu_percent": [round(gpu_percent,2)],
    "ram_percent": [mem.percent],
    "disk_percent": [disk.percent],
    "cpu_temperature": [round(temperatura_CPU,2)],
    "gpu_temperature": [round(temperatura_GPU, 2)],
    "mac_address": [mac],
    }

    #dadosMaq["operation_system"].append(system)

    df = pd.DataFrame(dadosMaq)

    lista_processos = []

    for processo in processos:
        lista_processos.append({
        'timestamp': datetime,
        'id': processo.info['pid'],
        'processo': processo.info['name'],
        'uso de cpu': f'{processo.info["cpu_percent"]:.2f}',
        'uso de memoria': f'{processo.info["memory_info"].rss / 1024**2:.2f}',
        'mac_address': mac
    })
        
    # df_temp = pd.DataFrame(dadosTemp)
    dfProcesso = pd.DataFrame(lista_processos)

    s3 = boto3.resource('s3')
    for bucket in s3.buckets.all():
        print(bucket.name)

    dfProcesso.to_csv('processos.csv', mode='a', index=False, header=False)
    if(os.path.exists('leituras.csv')):
        #df_temp.to_csv("leituras_temp.csv", mode="a", encoding="utf-8", index=False, sep=";", header=False)
        df.to_csv("leituras.csv", mode="a", encoding="utf-8", index=False, sep=";", header=False)
    else:
        #df_temp.to_csv("leituras_temp.csv", encoding="utf-8", index=False, sep=";")
        df.to_csv("leituras.csv", mode="a", encoding="utf-8", index=False, sep=";")
        firstTime = False

    with open('leituras.csv', 'rb') as data:
        s3.Bucket('bucket-raw-script-python-bitware').put_object(Key='leituras.csv', Body=data)

    with open('processos.csv', 'rb') as data:
        s3.Bucket('bucket-raw-script-python-bitware').put_object(Key='processos.csv', Body=data)
    time.sleep(9)