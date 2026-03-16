"""
Extrator Google Business Profile API
Gera CSVs em Dados/Google_Business/ com metricas de cada shopping

Metricas extraidas:
  - Acoes: rotas, ligacoes, cliques no site, reservas, mensagens
  - Impressoes: Maps (desktop/mobile) e Search (desktop/mobile)
  - Buscas: keywords de busca e impressoes mensais
  - Fotos: visualizacoes de fotos

Requer:
  - google-api-python-client>=2.100.0
  - google-auth>=2.0.0
  - OAuth2 credentials (GBP nao suporta Service Account)
  - GOOGLE_BUSINESS_ACCOUNT_ID (account ID)
  - GOOGLE_ADS_CLIENT_ID, GOOGLE_ADS_CLIENT_SECRET (OAuth app)
  - GOOGLE_BUSINESS_REFRESH_TOKEN (refresh token com escopo business.manage)

Uso:
  python scripts/extrair_google_business.py [--dias 90]
"""

import os
import sys
import json
import base64
import argparse
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

try:
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
except ImportError:
    print("[ERRO] google-api-python-client nao instalado.")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "Dados" / "Google_Business"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _get_credentials():
    """Cria credenciais OAuth2 para Google Business Profile."""
    return Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_BUSINESS_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_ADS_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )


def get_service():
    """Cria servico Google Business Profile (Business Information)."""
    return build('mybusinessbusinessinformation', 'v1', credentials=_get_credentials())


def get_performance_service():
    """Cria servico de Performance (metricas)."""
    return build('businessprofileperformance', 'v1', credentials=_get_credentials())


def listar_locations(service, account_id):
    """Lista todas as locations (shoppings) da conta."""
    locations = []
    try:
        response = service.accounts().locations().list(
            parent=f"accounts/{account_id}",
            readMask="name,title,storefrontAddress",
            pageSize=100,
        ).execute()
        locations = response.get('locations', [])
    except Exception as e:
        print(f"  [GBP] Erro ao listar locations: {e}")
    return locations


def extrair_metricas_diarias(perf_service, location_name, data_inicio, data_fim):
    """Extrai metricas diarias de uma location via Performance API."""
    try:
        # dailyMetricTimeSeries endpoint
        response = perf_service.locations().fetchMultiDailyMetricsTimeSeries(
            location=location_name,
            body={
                "dailyMetrics": [
                    "BUSINESS_DIRECTION_REQUESTS",
                    "CALL_CLICKS",
                    "WEBSITE_CLICKS",
                    "BUSINESS_BOOKINGS",
                    "BUSINESS_CONVERSATIONS",
                    "BUSINESS_FOOD_ORDERS",
                    "BUSINESS_IMPRESSIONS_DESKTOP_MAPS",
                    "BUSINESS_IMPRESSIONS_MOBILE_MAPS",
                    "BUSINESS_IMPRESSIONS_DESKTOP_SEARCH",
                    "BUSINESS_IMPRESSIONS_MOBILE_SEARCH",
                ],
                "timeRange": {
                    "startDate": {
                        "year": int(data_inicio[:4]),
                        "month": int(data_inicio[5:7]),
                        "day": int(data_inicio[8:10]),
                    },
                    "endDate": {
                        "year": int(data_fim[:4]),
                        "month": int(data_fim[5:7]),
                        "day": int(data_fim[8:10]),
                    },
                },
            },
        ).execute()
        return response.get('multiDailyMetricTimeSeries', [])
    except Exception as e:
        print(f"  [GBP] Erro metricas diarias {location_name}: {e}")
        return []


def extrair_search_insights(perf_service, location_name, data_inicio, data_fim):
    """Extrai insights de busca de uma location."""
    try:
        response = perf_service.locations().searchkeywords().impressions().monthly().list(
            parent=location_name,
            monthlyRange_startMonth_year=int(data_inicio[:4]),
            monthlyRange_startMonth_month=int(data_inicio[5:7]),
            monthlyRange_endMonth_year=int(data_fim[:4]),
            monthlyRange_endMonth_month=int(data_fim[5:7]),
            pageSize=300,
        ).execute()
        return response.get('searchKeywordsCounts', [])
    except Exception as e:
        print(f"  [GBP] Erro search insights {location_name}: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description="Extrator Google Business Profile")
    parser.add_argument("--dias", type=int, default=90, help="Dias para extrair (default 90)")
    args = parser.parse_args()

    data_fim = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    data_inicio = (datetime.now() - timedelta(days=args.dias)).strftime('%Y-%m-%d')

    account_id = os.environ.get("GOOGLE_BUSINESS_ACCOUNT_ID", "")
    if not account_id:
        print("[GBP] GOOGLE_BUSINESS_ACCOUNT_ID nao configurado. Pulando.")
        sys.exit(0)

    print(f"[GBP] Extraindo de {data_inicio} a {data_fim}...")

    service = get_service()
    perf_service = get_performance_service()

    # Listar locations
    locations = listar_locations(service, account_id)
    print(f"  [GBP] {len(locations)} locations encontradas")

    if not locations:
        print("[GBP] Nenhuma location encontrada. Verifique account_id e permissoes.")
        sys.exit(0)

    # Extrair metricas diarias por location
    all_metrics = []
    all_searches = []

    for loc in locations:
        loc_name = loc.get('name', '')
        loc_title = loc.get('title', '')
        address = loc.get('storefrontAddress', {})
        cidade = address.get('locality', '')

        print(f"  [GBP] {loc_title} ({cidade})...")

        # Metricas diarias (rotas, ligacoes, cliques)
        series_list = extrair_metricas_diarias(perf_service, loc_name, data_inicio, data_fim)
        for series in series_list:
            metric_name = series.get('dailyMetric', '')
            time_series = series.get('timeSeries', {})
            daily_values = time_series.get('datedValues', [])
            for dv in daily_values:
                date_obj = dv.get('date', {})
                data_str = f"{date_obj.get('year', 0)}-{date_obj.get('month', 0):02d}-{date_obj.get('day', 0):02d}"
                all_metrics.append({
                    'location': loc_title,
                    'location_id': loc_name,
                    'cidade': cidade,
                    'data': data_str,
                    'metrica': metric_name,
                    'valor': dv.get('value', 0),
                })

        # Search keywords
        keywords = extrair_search_insights(perf_service, loc_name, data_inicio, data_fim)
        for kw in keywords:
            keyword_info = kw.get('searchKeyword', {})
            all_searches.append({
                'location': loc_title,
                'keyword': keyword_info.get('keyword', ''),
                'tipo_busca': keyword_info.get('type', ''),
                'impressoes': kw.get('insightsValue', {}).get('value', 0),
            })

    # Salvar metricas diarias
    df_metrics = pd.DataFrame(all_metrics)
    if not df_metrics.empty:
        # Pivotar: uma coluna por metrica
        df_pivot = df_metrics.pivot_table(
            index=['location', 'location_id', 'cidade', 'data'],
            columns='metrica',
            values='valor',
            aggfunc='sum',
        ).reset_index()
        df_pivot.columns.name = None
        # Renomear colunas para portugues
        rename_map = {
            'BUSINESS_DIRECTION_REQUESTS': 'rotas',
            'CALL_CLICKS': 'ligacoes',
            'WEBSITE_CLICKS': 'cliques_site',
            'BUSINESS_BOOKINGS': 'reservas',
            'BUSINESS_CONVERSATIONS': 'mensagens',
            'BUSINESS_FOOD_ORDERS': 'pedidos_comida',
            'BUSINESS_IMPRESSIONS_DESKTOP_MAPS': 'impressoes_maps_desktop',
            'BUSINESS_IMPRESSIONS_MOBILE_MAPS': 'impressoes_maps_mobile',
            'BUSINESS_IMPRESSIONS_DESKTOP_SEARCH': 'impressoes_search_desktop',
            'BUSINESS_IMPRESSIONS_MOBILE_SEARCH': 'impressoes_search_mobile',
        }
        df_pivot = df_pivot.rename(columns=rename_map)
        df_pivot.to_csv(OUTPUT_DIR / "metricas_diarias.csv", index=False, encoding='utf-8-sig')
        print(f"  [GBP] metricas_diarias.csv: {len(df_pivot)} linhas")
    else:
        print("  [GBP] metricas_diarias.csv: sem dados")

    # Salvar search keywords
    df_searches = pd.DataFrame(all_searches)
    if not df_searches.empty:
        df_searches.to_csv(OUTPUT_DIR / "search_keywords.csv", index=False, encoding='utf-8-sig')
        print(f"  [GBP] search_keywords.csv: {len(df_searches)} linhas")
    else:
        print("  [GBP] search_keywords.csv: sem dados")

    # Resumo por location (agregado)
    if not df_metrics.empty:
        df_resumo = df_metrics.groupby(['location', 'cidade', 'metrica'])['valor'].sum().reset_index()
        df_resumo_pivot = df_resumo.pivot_table(
            index=['location', 'cidade'],
            columns='metrica',
            values='valor',
            aggfunc='sum',
        ).reset_index()
        df_resumo_pivot.columns.name = None
        df_resumo_pivot = df_resumo_pivot.rename(columns=rename_map)
        df_resumo_pivot.to_csv(OUTPUT_DIR / "resumo_locations.csv", index=False, encoding='utf-8-sig')
        print(f"  [GBP] resumo_locations.csv: {len(df_resumo_pivot)} linhas")

    print("[GBP] Extracao concluida!")


if __name__ == "__main__":
    main()
