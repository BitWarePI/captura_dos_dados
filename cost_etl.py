import boto3
import csv
import datetime
from botocore.exceptions import ClientError
import os

# Configurações
BUCKET_NAME = 's3-client-bitwarepi'
FILE_KEY = '1/cost_data_daily.csv'
REGION = 'us-east-1' 

def get_date_ranges():
    """Gera os intervalos de data para histórico (1 ano atrás) e previsão (30 dias frente)."""
    today = datetime.date.today()
    
    # Histórico: Últimos 365 dias até ontem
    start_date_hist = today - datetime.timedelta(days=365)
    end_date_hist = today 
    
    # Previsão: Amanhã até 30 dias à frente
    start_date_forecast = today + datetime.timedelta(days=1)
    end_date_forecast = today + datetime.timedelta(days=31)
    
    return {
        'hist_start': start_date_hist.strftime('%Y-%m-%d'),
        'hist_end': end_date_hist.strftime('%Y-%m-%d'),
        'fore_start': start_date_forecast.strftime('%Y-%m-%d'),
        'fore_end': end_date_forecast.strftime('%Y-%m-%d')
    }

def fetch_historical_costs(ce_client, start, end):
    """Busca custos diários agrupados por Serviço."""
    results = []
    token = None
    
    while True:
        kwargs = {
            'TimePeriod': {'Start': start, 'End': end},
            'Granularity': 'DAILY',
            'Metrics': ['UnblendedCost'],
            'GroupBy': [{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        }
        if token:
            kwargs['NextPageToken'] = token
            
        response = ce_client.get_cost_and_usage(**kwargs)
        results.extend(response['ResultsByTime'])
        
        token = response.get('NextPageToken')
        if not token:
            break
            
    # Processar dados para formato plano
    flattened_data = []
    for day in results:
        date = day['TimePeriod']['Start']
        for group in day['Groups']:
            service_name = group['Keys'][0]
            amount = float(group['Metrics']['UnblendedCost']['Amount'])
            if amount > 0: 
                flattened_data.append({
                    'Date': date,
                    'Service': service_name,
                    'Cost': amount,
                    'Type': 'Historical'
                })
    return flattened_data

def fetch_forecast(ce_client, start, end):
    """Busca previsão de gastos totais para o próximo mês."""
    try:
        response = ce_client.get_cost_forecast(
            TimePeriod={'Start': start, 'End': end},
            Metric='UNBLENDED_COST',
            Granularity='DAILY'
        )
        
        forecast_data = []
        if 'ForecastResultsByTime' in response:
            for day in response['ForecastResultsByTime']:
                date = day['TimePeriod']['Start']
                amount = float(day['MeanValue'])
                forecast_data.append({
                    'Date': date,
                    'Service': 'Forecast Total',
                    'Cost': amount,
                    'Type': 'Forecast'
                })
        return forecast_data
    except ClientError as e:
        print(f"Aviso: Não foi possível obter previsão (pode haver dados insuficientes): {e}")
        return []

def upload_to_s3(data, bucket, key):
    """Escreve dados em CSV e faz upload para o S3."""
    filename = '/tmp/cost_data_daily.csv'
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Date', 'Service', 'Cost', 'Type']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in data:
            writer.writerow(row)
            
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(filename, bucket, key)
        print(f"Sucesso: Arquivo enviado para s3://{bucket}/{key}")
    except Exception as e:
        print(f"Erro ao enviar para o S3: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

def main():
    ce = boto3.client('ce', region_name=REGION)
    
    dates = get_date_ranges()
    print(f"Buscando dados históricos de {dates['hist_start']} a {dates['hist_end']}...")
    historical_data = fetch_historical_costs(ce, dates['hist_start'], dates['hist_end'])
    
    print(f"Buscando previsão de {dates['fore_start']} a {dates['fore_end']}...")
    forecast_data = fetch_forecast(ce, dates['fore_start'], dates['fore_end'])
    
    all_data = historical_data + forecast_data
    
    print(f"Total de registros processados: {len(all_data)}")
    upload_to_s3(all_data, BUCKET_NAME, FILE_KEY)

if __name__ == '__main__':
    main()