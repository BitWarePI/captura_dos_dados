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

while True:
    datetime = dt.datetime.now().replace(microsecond=0)
    mac = get_mac_address()

    cpu = ps.cpu_times(percpu=False)
    processos = list(ps.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']))

 
    
    cpu_percent = ps.cpu_percent(interval=1);
    temperatura_CPU = 30 + (cpu_percent * 0.6) + random.uniform(-2, 2)

    temperatura_CPU = max(30, min(90, temperatura_CPU))
    gpu_percent = cpu_percent + random.uniform(-10, 10)
    gpu_percent = max(0, min(100, gpu_percent))
    temperatura_GPU = 35 + (gpu_percent * 0.55) + random.uniform(-3, 3)
    temperatura_GPU = max(35, min(95, temperatura_GPU))

    dadosMaq = {
    "id_empresa":[1],
    "datetime": [datetime],
    "cpu_percent": [cpu_percent],
    "gpu_percent": [round(gpu_percent,2)],
    "cpu_temperature": [round(temperatura_CPU,2)],
    "gpu_temperature": [round(temperatura_GPU, 2)],
    "mac_address": [mac]
    }


    df = pd.DataFrame(dadosMaq)

    lista_processos = []

    for processo in processos:
        lista_processos.append({
        "id_empresa": 1,
        'timestamp': datetime,
        'processo': processo.info['name'],
        'uso de cpu': cpu_percent,
        'uso de gpu': round(gpu_percent,2),
        'mac_address': mac
    })
        
    dfProcesso = pd.DataFrame(lista_processos)

    # --- Garante que a pasta existe ---
    os.makedirs('captura_dos_dados', exist_ok=True)

# Salva os processos
    dfProcesso.to_csv('captura_dos_dados/processos.csv', mode='a', index=False, header=True)

# Salva leituras
    if(os.path.exists('captura_dos_dados/leituras.csv')):
        df.to_csv("captura_dos_dados/leituras.csv", mode="a", encoding="utf-8", index=False, sep=";", header=False)
    else:
        df.to_csv("captura_dos_dados/leituras.csv", mode="a", encoding="utf-8", index=False, sep=";")
        firstTime = False


    with open('captura_dos_dados/leituras.csv', 'rb') as data:
        s3.Bucket('s3-raw-bitwarepi').put_object(Key='dados/leituras.csv', Body=data)

    with open('captura_dos_dados/processos.csv', 'rb') as data:
        s3.Bucket('s3-raw-bitwarepi').put_object(Key='dados/processos.csv', Body=data)