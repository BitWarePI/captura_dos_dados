import psutil as ps
import pandas as pd
import datetime as dt
import os
import time
from getmac import get_mac_address
import random
import boto3

s3 = boto3.resource('s3')
for bucket in s3.buckets.all():
    print(bucket.name)

while True:
    datetime_atual = dt.datetime.now().replace(microsecond=0)
    mac = get_mac_address()
    cpu_percent = ps.cpu_percent(interval=1)

    temperatura_CPU = 30 + (cpu_percent * 0.6) + random.uniform(-2, 2)
    temperatura_CPU = max(30, min(90, temperatura_CPU))

    gpu_percent = cpu_percent + random.uniform(-15, 15)
    gpu_percent = max(0, min(100, gpu_percent))

    temperatura_GPU = 35 + (gpu_percent * 0.55) + random.uniform(-3, 3)
    temperatura_GPU = max(35, min(95, temperatura_GPU))

    dadosMaq = {
        "id_empresa": [1],
        "datetime": [datetime_atual],
        "cpu_percent": [round(cpu_percent, 2)],
        "gpu_percent": [round(gpu_percent, 2)],
        "cpu_temperature": [round(temperatura_CPU, 2)],
        "gpu_temperature": [round(temperatura_GPU, 2)],
        "mac_address": [mac]
    }

    df = pd.DataFrame(dadosMaq)

    lista_processos = []

    processos = list(ps.process_iter(['name', 'cpu_percent']))
    time.sleep(1)

    for processo in processos:
      try:
        cpu_proc = processo.cpu_percent(interval=None)
        lista_processos.append({
          'id_empresa': 1,
          'datetime': datetime_atual,
          'processo': processo.name(),
          'uso_de_cpu': round(cpu_proc, 2),
          'uso de gpu': round(gpu_percent, 2),
          'mac_address': mac
        })
      except (ps.NoSuchProcess, ps.AccessDenied, ps.ZombieProcess):
        # Ignora processos que sumiram ou não podem ser acessados
        continue        

    dfProcesso = pd.DataFrame(lista_processos)

    dfProcesso.to_csv('captura_dos_dados/processos.csv', mode='a', index=False, header=True)

    if os.path.exists('captura_dos_dados/leituras.csv'):
        df.to_csv("captura_dos_dados/leituras.csv", mode="a", encoding="utf-8", index=False, sep=";", header=False)
    else:
        df.to_csv("captura_dos_dados/leituras.csv", mode="a", encoding="utf-8", index=False, sep=";")

    # Envia para S3 (RAW)
    with open('captura_dos_dados/leituras.csv', 'rb') as data:
        s3.Bucket('s3-raw-bitwarepi').put_object(Key='dados/leituras.csv', Body=data)

    with open('captura_dos_dados/processos.csv', 'rb') as data:
        s3.Bucket('s3-raw-bitwarepi').put_object(Key='dados/processos.csv', Body=data)

    time.sleep(2)
