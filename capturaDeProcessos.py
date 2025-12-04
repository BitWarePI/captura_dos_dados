import psutil as ps
import pandas as pd
import datetime as dt
import os
import time
from getmac import get_mac_address
import random
import boto3
import platform
import io
import requests
import subprocess

print("--- Iniciando Bitware Monitor ---")

def get_public_ip():
    try:
        ip = requests.get("https://api.ipify.org", timeout=3).text
        if ip:
            return ip
    except:
        pass

    try:
        result = subprocess.run(
            ["curl", "-s", "https://api.ipify.org"],
            capture_output=True,
            text=True
        )
        ip = result.stdout.strip()
        if ip:
            return ip
    except:
        pass

    return None


# --- Variáveis Estáticas ---
current_mac = get_mac_address()
macs_existentes = set()
ip_publico = get_public_ip()

# Configuração S3
try:
    s3 = boto3.resource('s3')
    bucket = s3.Bucket("s3-raw-bitwarepi")
    print("Conexão S3 configurada.")
except Exception as e:
    print(f"Erro ao configurar S3: {e}")

# --- Função de Download e Pré-Verificação ---
def baixar_ou_criar(nome_arquivo):
    caminho_local = nome_arquivo
    caminho_s3 = f"dados/{nome_arquivo}"
    
    global macs_existentes
    
    try:
        with io.BytesIO() as data:
            bucket.download_fileobj(caminho_s3, data)
            data.seek(0)
            
            if nome_arquivo == "hardware.csv":
                try:
                    df_hardware = pd.read_csv(data, sep=';', usecols=['macAddress'])
                    macs_existentes.update(df_hardware['macAddress'].unique())
                    print(f"Hardware.csv baixado. MACs já registrados: {len(macs_existentes)}")
                except Exception as read_error:
                    print(f"Aviso: Não foi possível ler MACs do hardware.csv. {read_error}")

        bucket.download_file(caminho_s3, caminho_local)
        print(f"Arquivo {nome_arquivo} baixado do S3.")

    except Exception:
        if not os.path.exists(caminho_local):
            open(caminho_local, "w").close()
            print(f"Arquivo {nome_arquivo} criado localmente (vazio).")
        else:
            print(f"Arquivo {nome_arquivo} já existe localmente.")

# Preparar arquivos
baixar_ou_criar("leituras.csv")
baixar_ou_criar("processos.csv")
baixar_ou_criar("hardware.csv")

# --- Função Hardware ---
def get_real_hardware_info():
    print("Lendo informações de Hardware...")

    # --- WINDOWS ---
    if platform.system() == "Windows":
        try:
            import wmi
            c = wmi.WMI()

            total_ram_bytes = sum(int(stick.Capacity) for stick in c.Win32_PhysicalMemory())
            ram_gb = round(total_ram_bytes / (1024**3), 2)

            gpu_vram_gb = 0.0
            for gpu in c.Win32_VideoController():
                try:
                    vram_raw = int(gpu.AdapterRAM)
                    if vram_raw < 0:
                        vram_raw = vram_raw & 0xFFFFFFFF
                    vram_calc = round(vram_raw / (1024**3), 2)
                    gpu_vram_gb = max(gpu_vram_gb, vram_calc)
                except:
                    pass

            return ram_gb, gpu_vram_gb

        except Exception as e:
            print(f"Erro ao ler via WMI ({e}). Usando padrão.")
            return 8.0, 2.0

    # --- LINUX ---
    else:
        print("Linux detectado → usando psutil para RAM e padrão para GPU.")

        ram_gb = round(ps.virtual_memory().total / (1024**3), 2)

        # GPU não tem API universal em Linux
        gpu_vram_gb = 0.0  

        return ram_gb, gpu_vram_gb

qtd_ram_gb, qtd_gpu_vram = get_real_hardware_info()
os_version = platform.platform()
cpu_cores = ps.cpu_count(logical=True)

try:
    if platform.system() == "Windows":
        disk_capacity_bytes = ps.disk_usage('C:\\').total
    else:
        disk_capacity_bytes = ps.disk_usage('/').total

    disk_capacity_gb = round(disk_capacity_bytes / (1024**3), 2)
except:
    disk_capacity_gb = 0.0


print(f"Hardware detectado -> RAM: {qtd_ram_gb}GB | GPU: {qtd_gpu_vram}GB | DISCO: {disk_capacity_gb}GB | OS: {os_version} | IP: {ip_publico}")

# --- Loop Principal ---
while True:
    try:
        print("\nColetando métricas...")
        datetime_atual = dt.datetime.now().replace(microsecond=0)
        mac = current_mac 
        
        cpu_percent = ps.cpu_percent(interval=1)
        temperatura_CPU = max(30, min(90, 30 + (cpu_percent * 0.6) + random.uniform(-2, 2)))
        
        gpu_percent = max(0, min(100, cpu_percent + random.uniform(-15, 15)))
        temperatura_GPU = max(35, min(95, 35 + (gpu_percent * 0.55) + random.uniform(-3, 3)))

        dadosMaq = {
            "datetime": [datetime_atual],
            "cpu_percent": [round(cpu_percent, 2)],
            "gpu_percent": [round(gpu_percent, 2)],
            "cpu_temperature": [round(temperatura_CPU, 2)],
            "gpu_temperature": [round(temperatura_GPU, 2)],
            "mac_address": [mac]
        }
        df = pd.DataFrame(dadosMaq)

        dadosHardware = {
            "datetime": [datetime_atual],
            "macAddress": [mac],
            "so": [os_version],
            "qtdRam": [qtd_ram_gb],
            "cpuCor": [cpu_cores],
            "qtdGpu": [qtd_gpu_vram],
            "qtdDisco": [disk_capacity_gb],
            "ipPublico": [ip_publico]
        }
        dfHardware = pd.DataFrame(dadosHardware)

        lista_processos = []
        processos = list(ps.process_iter(['name', 'cpu_percent']))
        
        for processo in processos:
            try:
                cpu_proc = processo.cpu_percent(interval=None)
                lista_processos.append({
                    'datetime': datetime_atual,
                    'pid': processo.pid,
                    'processo': processo.name(),
                    'uso_de_cpu': round(cpu_proc, 2),
                    'uso_de_gpu': round(gpu_percent, 2),
                    'mac_address': mac
                })
            except:
                pass

        dfProcesso = pd.DataFrame(lista_processos)

        arquivos = [
            ("leituras.csv", df),
            ("processos.csv", dfProcesso),
            ("hardware.csv", dfHardware)
        ]

        for nome_arquivo, dataframe in arquivos:

            if nome_arquivo == "hardware.csv":
                if mac in macs_existentes:
                    print(f"INFO: MAC {mac} já registrado. Pulando hardware.csv.")
                    continue
                macs_existentes.add(mac)
                print(f"INFO: Registrando novo hardware para {mac}.")

            try:
                existe = os.path.exists(nome_arquivo) and os.path.getsize(nome_arquivo) > 0
                dataframe.to_csv(
                    nome_arquivo,
                    mode="a",
                    index=False,
                    sep=";",
                    header=not existe
                )
            except Exception as e:
                print(f"Erro ao salvar {nome_arquivo}: {e}")
                continue

            try:
                with open(nome_arquivo, "rb") as data:
                    bucket.put_object(Key=f"dados/{nome_arquivo}", Body=data)
            except Exception as e:
                print(f"Erro de conexão S3 ao enviar {nome_arquivo}: {e}")

        print(f"Dados salvos em {datetime_atual}\n")
        time.sleep(2)

    except KeyboardInterrupt:
        print("Parando execução...")
        break
    except Exception as e:
        print(f"Erro no loop principal: {e}")
        time.sleep(5)
