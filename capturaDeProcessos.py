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

s3 = boto3.resource('s3')
for bucket in s3.buckets.all():
        print(bucket.name)

system = pf.system();
while True:
    datetime = dt.datetime.now().replace(microsecond=0)
    mac = get_mac_address()

    cpu = ps.cpu_times(percpu=False)
    mem = ps.virtual_memory()
    disk = ps.disk_usage("/")
    processos = list(ps.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']))
    
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
        
    dfProcesso = pd.DataFrame(lista_processos)    
        
    dfProcesso.to_csv('captura_dados/processos.csv', mode='a', index=False, header=True)
  
    if(os.path.exists('captura_dados/leituras.csv')):
        df.to_csv("captura_dados/leituras.csv", mode="a", encoding="utf-8", index=False, sep=";", header=False)
    else:
        df.to_csv("captura_dados/leituras.csv", mode="a", encoding="utf-8", index=False, sep=";")
        firstTime = False

# Enviando para Bucket Raw 
    with open('captura_dados/leituras.csv', 'rb') as data:
        s3.Bucket('s3-raw-bitwarepi').put_object(Key='dados/leituras.csv', Body=data)

    with open('captura_dados/processos.csv', 'rb') as data:
        s3.Bucket('s3-raw-bitwarepi').put_object(Key='dados/processos.csv', Body=data)
    time.sleep(2)