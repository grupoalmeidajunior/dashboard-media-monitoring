"""
Extrator TikTok Ads Marketing API — Multi-Shopping
Gera 11 CSVs em Dados/TikTok_Ads/ (todos com coluna 'shopping')

Requer:
  - requests
  - TIKTOK_ADS_CONFIG (JSON): {"BS": {"token": "x", "advertiser_id": "y"}, ...}

Uso:
  python scripts/extrair_tiktok_ads.py [--dias 90]
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "Dados" / "TikTok_Ads"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

API_BASE = "https://business-api.tiktok.com/open_api/v1.3"

SHOPPING_NOMES = {
    "CS": "Continente Shopping",
    "BS": "Balneario Shopping",
    "NK": "Neumarkt Shopping",
    "NR": "Norte Shopping",
    "GS": "Garten Shopping",
    "NS": "Nacoes Shopping",
}

# Colunas que nao devem ser convertidas para numerico
COLS_NAO_NUMERICAS = [
    'campaign_name', 'campaign_id', 'adgroup_name', 'adgroup_id',
    'stat_time_day', 'stat_time_hour', 'gender', 'age',
    'country_code', 'province_id', 'ac', 'platform',
    'interest_category', 'interest_category_v2',
    'shopping', 'shopping_sigla', 'objective_type', 'status',
]


def get_config():
    """Carrega configuracao multi-shopping do env."""
    config_json = os.environ.get("TIKTOK_ADS_CONFIG", "")
    if not config_json:
        # Fallback: token + advertiser_id unicos (retrocompativel)
        token = os.environ.get("TIKTOK_ACCESS_TOKEN", "")
        adv_id = os.environ.get("TIKTOK_ADVERTISER_ID", "")
        if token and adv_id:
            return {"GERAL": {"token": token, "advertiser_id": adv_id}}
        print("[ERRO] TIKTOK_ADS_CONFIG ou TIKTOK_ACCESS_TOKEN nao configurados")
        sys.exit(1)
    return json.loads(config_json)


def fetch_report(token, advertiser_id, data_inicio, data_fim, dimensions, metrics, shopping_sigla, data_level="AUCTION_CAMPAIGN", report_type="BASIC"):
    """Busca relatorio via TikTok Reporting API para 1 conta."""
    url = f"{API_BASE}/report/integrated/get/"
    headers = {"Access-Token": token}

    all_rows = []
    page = 1
    page_size = 1000

    while True:
        params = {
            "advertiser_id": advertiser_id,
            "report_type": report_type,
            "data_level": data_level,
            "dimensions": json.dumps(dimensions),
            "metrics": json.dumps(metrics),
            "start_date": data_inicio,
            "end_date": data_fim,
            "page": page,
            "page_size": page_size,
            "lifetime": False,
        }

        resp = requests.get(url, headers=headers, params=params, timeout=60)
        data = resp.json()

        if data.get("code") != 0:
            print(f"  [TikTok/{shopping_sigla}] Erro: {data.get('message', 'Desconhecido')}")
            break

        rows = data.get("data", {}).get("list", [])
        if not rows:
            break

        for row in rows:
            dims = row.get("dimensions", {})
            mets = row.get("metrics", {})
            registro = {**dims, **mets}
            registro['shopping'] = SHOPPING_NOMES.get(shopping_sigla, shopping_sigla)
            registro['shopping_sigla'] = shopping_sigla
            all_rows.append(registro)

        page_info = data.get("data", {}).get("page_info", {})
        total = page_info.get("total_number", 0)
        if page * page_size >= total:
            break
        page += 1

    df = pd.DataFrame(all_rows)

    # Converter colunas numericas
    for col in df.columns:
        if col not in COLS_NAO_NUMERICAS:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            except (ValueError, TypeError):
                pass

    return df


def fetch_campaigns(token, advertiser_id, shopping_sigla):
    """Busca metadados de campanhas (nome, objetivo, status) via Campaign Management API."""
    url = f"{API_BASE}/campaign/get/"
    headers = {"Access-Token": token}

    all_campaigns = []
    page = 1
    page_size = 1000

    while True:
        params = {
            "advertiser_id": advertiser_id,
            "page": page,
            "page_size": page_size,
        }

        resp = requests.get(url, headers=headers, params=params, timeout=60)
        data = resp.json()

        if data.get("code") != 0:
            print(f"  [TikTok/{shopping_sigla}] Erro campanhas: {data.get('message', 'Desconhecido')}")
            break

        campaigns = data.get("data", {}).get("list", [])
        if not campaigns:
            break

        for c in campaigns:
            all_campaigns.append({
                'campaign_id': str(c.get('campaign_id', '')),
                'campaign_name': c.get('campaign_name', ''),
                'objective_type': c.get('objective_type', ''),
                'status': c.get('operation_status', c.get('status', '')),
                'budget': c.get('budget', 0),
                'shopping': SHOPPING_NOMES.get(shopping_sigla, shopping_sigla),
                'shopping_sigla': shopping_sigla,
            })

        page_info = data.get("data", {}).get("page_info", {})
        total = page_info.get("total_number", 0)
        if page * page_size >= total:
            break
        page += 1

    return pd.DataFrame(all_campaigns)


def fetch_adgroups(token, advertiser_id, shopping_sigla):
    """Busca metadados de ad groups (nome, targeting) via AdGroup Management API."""
    url = f"{API_BASE}/adgroup/get/"
    headers = {"Access-Token": token}

    all_adgroups = []
    page = 1
    page_size = 1000

    while True:
        params = {
            "advertiser_id": advertiser_id,
            "page": page,
            "page_size": page_size,
        }

        resp = requests.get(url, headers=headers, params=params, timeout=60)
        data = resp.json()

        if data.get("code") != 0:
            print(f"  [TikTok/{shopping_sigla}] Erro adgroups: {data.get('message', 'Desconhecido')}")
            break

        adgroups = data.get("data", {}).get("list", [])
        if not adgroups:
            break

        for ag in adgroups:
            all_adgroups.append({
                'adgroup_id': str(ag.get('adgroup_id', '')),
                'adgroup_name': ag.get('adgroup_name', ''),
                'campaign_id': str(ag.get('campaign_id', '')),
                'status': ag.get('operation_status', ag.get('status', '')),
                'budget': ag.get('budget', 0),
                'placement_type': ag.get('placement_type', ''),
                'optimization_goal': ag.get('optimization_goal', ''),
                'bid_type': ag.get('bid_type', ''),
                'shopping': SHOPPING_NOMES.get(shopping_sigla, shopping_sigla),
                'shopping_sigla': shopping_sigla,
            })

        page_info = data.get("data", {}).get("page_info", {})
        total = page_info.get("total_number", 0)
        if page * page_size >= total:
            break
        page += 1

    return pd.DataFrame(all_adgroups)


def fetch_hourly_report(token, advertiser_id, data_inicio, data_fim, metrics, shopping_sigla):
    """Busca relatorio por hora, iterando dia a dia (API limita stat_time_hour a 1 dia)."""
    all_dfs = []
    start = datetime.strptime(data_inicio, '%Y-%m-%d')
    end = datetime.strptime(data_fim, '%Y-%m-%d')
    current = start

    while current <= end:
        day_str = current.strftime('%Y-%m-%d')
        df = fetch_report(
            token, advertiser_id, day_str, day_str,
            ["stat_time_hour"], metrics, shopping_sigla,
            "AUCTION_CAMPAIGN", "BASIC"
        )
        if not df.empty:
            all_dfs.append(df)
        current += timedelta(days=1)

    return pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()


def main():
    parser = argparse.ArgumentParser(description="Extrator TikTok Ads (Multi-Shopping)")
    parser.add_argument("--dias", type=int, default=90, help="Dias para extrair (default 90)")
    args = parser.parse_args()

    data_fim = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    data_inicio = (datetime.now() - timedelta(days=args.dias)).strftime('%Y-%m-%d')

    config = get_config()
    print(f"[TikTok Ads] Extraindo de {data_inicio} a {data_fim} para {len(config)} conta(s)...")

    # --- Metricas ---
    metrics_base = [
        "spend", "impressions", "clicks", "ctr", "cpc", "cpm",
        "conversion", "cost_per_conversion", "conversion_rate",
        "total_complete_payment_rate",
    ]
    metrics_audience = [
        "spend", "impressions", "clicks", "ctr", "cpc", "cpm",
        "conversion", "cost_per_conversion", "conversion_rate",
    ]
    metrics_audience_reach = [
        "spend", "impressions", "clicks", "ctr", "cpc", "cpm",
        "conversion", "cost_per_conversion", "conversion_rate",
        "reach", "frequency",
    ]
    metrics_video = [
        "video_play_actions", "video_watched_2s", "video_watched_6s",
        "average_video_play", "average_video_play_per_user",
        "video_views_p25", "video_views_p50", "video_views_p75", "video_views_p100",
        "engaged_view", "engaged_view_15s",
    ]
    metrics_engagement = [
        "likes", "comments", "shares", "follows",
        "clicks_on_music_disc", "profile_visits",
    ]

    # --- Relatorios: (nome, dimensions, metrics, data_level, report_type) ---
    relatorios = [
        # Existentes
        ("campanhas", ["campaign_id", "stat_time_day"], metrics_base + metrics_engagement, "AUCTION_CAMPAIGN", "BASIC"),
        ("video_engagement", ["campaign_id", "stat_time_day"], metrics_base + metrics_video, "AUCTION_CAMPAIGN", "BASIC"),
        ("demografico_idade", ["stat_time_day", "age"], metrics_audience, "AUCTION_ADVERTISER", "AUDIENCE"),
        ("demografico_genero", ["stat_time_day", "gender"], metrics_audience, "AUCTION_ADVERTISER", "AUDIENCE"),
        ("diario", ["stat_time_day"], metrics_base + metrics_video + metrics_engagement, "AUCTION_CAMPAIGN", "BASIC"),
        # Novos
        ("geografico", ["country_code"], metrics_audience, "AUCTION_ADVERTISER", "AUDIENCE"),
        ("plataforma", ["stat_time_day", "platform"], metrics_audience, "AUCTION_ADVERTISER", "AUDIENCE"),
        ("adgroup_diario", ["adgroup_id", "stat_time_day"], metrics_base + metrics_engagement, "AUCTION_ADGROUP", "BASIC"),
    ]

    # --- Extrair relatorios ---
    for nome_arquivo, dimensions, metrics, data_level, report_type in relatorios:
        dfs = []
        for sigla, creds in config.items():
            token = creds["token"]
            adv_id = creds["advertiser_id"]
            print(f"  [TikTok/{sigla}] Extraindo {nome_arquivo}...")
            df = fetch_report(token, adv_id, data_inicio, data_fim, dimensions, metrics, sigla, data_level, report_type)
            if not df.empty:
                dfs.append(df)

        if dfs:
            df_final = pd.concat(dfs, ignore_index=True)
        else:
            df_final = pd.DataFrame()

        df_final.to_csv(OUTPUT_DIR / f"{nome_arquivo}.csv", index=False, encoding='utf-8-sig')
        print(f"  [TikTok] {nome_arquivo}.csv: {len(df_final)} linhas ({len(config)} shoppings)")

    # --- Hora do Dia (stat_time_hour exige range 1 dia — iterar dia a dia) ---
    print("  [TikTok] Extraindo hora_dia (dia a dia)...")
    dfs_hora = []
    for sigla, creds in config.items():
        token = creds["token"]
        adv_id = creds["advertiser_id"]
        print(f"  [TikTok/{sigla}] Extraindo hora_dia...")
        df = fetch_hourly_report(token, adv_id, data_inicio, data_fim, metrics_base + metrics_engagement, sigla)
        if not df.empty:
            dfs_hora.append(df)
    df_hora = pd.concat(dfs_hora, ignore_index=True) if dfs_hora else pd.DataFrame()
    # Agregar por hora (somar todas os dias)
    if not df_hora.empty and 'stat_time_hour' in df_hora.columns:
        # Extrair apenas a hora (0-23) do timestamp
        df_hora['hora'] = pd.to_datetime(df_hora['stat_time_hour']).dt.hour
        num_cols = [c for c in df_hora.columns if c not in COLS_NAO_NUMERICAS and c != 'hora']
        df_hora_agg = df_hora.groupby(['hora', 'shopping', 'shopping_sigla'], as_index=False)[num_cols].sum()
        df_hora_agg.to_csv(OUTPUT_DIR / "hora_dia.csv", index=False, encoding='utf-8-sig')
        print(f"  [TikTok] hora_dia.csv: {len(df_hora_agg)} linhas")
    else:
        pd.DataFrame().to_csv(OUTPUT_DIR / "hora_dia.csv", index=False, encoding='utf-8-sig')
        print(f"  [TikTok] hora_dia.csv: 0 linhas")

    # --- Alcance e Frequencia (reach/frequency sem dimensao temporal) ---
    print("  [TikTok] Extraindo alcance_frequencia...")
    dfs_reach = []
    for sigla, creds in config.items():
        token = creds["token"]
        adv_id = creds["advertiser_id"]
        print(f"  [TikTok/{sigla}] Extraindo alcance_frequencia...")
        df = fetch_report(token, adv_id, data_inicio, data_fim,
                          ["campaign_id"], metrics_audience_reach, sigla,
                          "AUCTION_CAMPAIGN", "BASIC")
        if not df.empty:
            dfs_reach.append(df)
    df_reach = pd.concat(dfs_reach, ignore_index=True) if dfs_reach else pd.DataFrame()
    df_reach.to_csv(OUTPUT_DIR / "alcance_frequencia.csv", index=False, encoding='utf-8-sig')
    print(f"  [TikTok] alcance_frequencia.csv: {len(df_reach)} linhas ({len(config)} shoppings)")

    # --- Metadados: campanhas e ad groups ---
    print("  [TikTok] Extraindo metadados de campanhas...")
    dfs_camp_meta = []
    dfs_ag_meta = []
    for sigla, creds in config.items():
        token = creds["token"]
        adv_id = creds["advertiser_id"]
        print(f"  [TikTok/{sigla}] Extraindo metadados campanhas + adgroups...")
        df_c = fetch_campaigns(token, adv_id, sigla)
        if not df_c.empty:
            dfs_camp_meta.append(df_c)
        df_ag = fetch_adgroups(token, adv_id, sigla)
        if not df_ag.empty:
            dfs_ag_meta.append(df_ag)

    df_camp_meta = pd.concat(dfs_camp_meta, ignore_index=True) if dfs_camp_meta else pd.DataFrame()
    df_camp_meta.to_csv(OUTPUT_DIR / "campanhas_metadata.csv", index=False, encoding='utf-8-sig')
    print(f"  [TikTok] campanhas_metadata.csv: {len(df_camp_meta)} linhas")

    df_ag_meta = pd.concat(dfs_ag_meta, ignore_index=True) if dfs_ag_meta else pd.DataFrame()
    df_ag_meta.to_csv(OUTPUT_DIR / "adgroups_metadata.csv", index=False, encoding='utf-8-sig')
    print(f"  [TikTok] adgroups_metadata.csv: {len(df_ag_meta)} linhas")

    # --- Enriquecer campanhas.csv com nomes ---
    if not df_camp_meta.empty:
        campanhas_path = OUTPUT_DIR / "campanhas.csv"
        df_campanhas = pd.read_csv(campanhas_path, dtype={'campaign_id': str})
        meta_cols = df_camp_meta[['campaign_id', 'campaign_name', 'objective_type']].drop_duplicates()
        df_campanhas['campaign_id'] = df_campanhas['campaign_id'].astype(str)
        df_campanhas = df_campanhas.merge(meta_cols, on='campaign_id', how='left')
        df_campanhas.to_csv(campanhas_path, index=False, encoding='utf-8-sig')
        print(f"  [TikTok] campanhas.csv enriquecido com nomes ({len(meta_cols)} campanhas)")

        # Enriquecer video_engagement.csv tambem
        video_path = OUTPUT_DIR / "video_engagement.csv"
        df_video = pd.read_csv(video_path, dtype={'campaign_id': str})
        df_video['campaign_id'] = df_video['campaign_id'].astype(str)
        df_video = df_video.merge(meta_cols, on='campaign_id', how='left')
        df_video.to_csv(video_path, index=False, encoding='utf-8-sig')
        print(f"  [TikTok] video_engagement.csv enriquecido com nomes")

    # --- Enriquecer adgroup_diario.csv com nomes ---
    if not df_ag_meta.empty:
        ag_path = OUTPUT_DIR / "adgroup_diario.csv"
        if ag_path.exists():
            df_ag_data = pd.read_csv(ag_path, dtype={'adgroup_id': str})
            ag_cols = df_ag_meta[['adgroup_id', 'adgroup_name', 'campaign_id', 'optimization_goal']].drop_duplicates()
            df_ag_data['adgroup_id'] = df_ag_data['adgroup_id'].astype(str)
            df_ag_data = df_ag_data.merge(ag_cols, on='adgroup_id', how='left')
            # Adicionar nome da campanha tambem
            if not df_camp_meta.empty:
                camp_names = df_camp_meta[['campaign_id', 'campaign_name']].drop_duplicates()
                df_ag_data = df_ag_data.merge(camp_names, on='campaign_id', how='left')
            df_ag_data.to_csv(ag_path, index=False, encoding='utf-8-sig')
            print(f"  [TikTok] adgroup_diario.csv enriquecido com nomes")

    print("[TikTok Ads] Extracao concluida!")


if __name__ == "__main__":
    main()
