# Dashboard Media Monitoring — Almeida Junior

## Visao Geral
Painel unificado de performance de midia digital que consolida dados de Google Ads, Meta Ads (Facebook/Instagram), TikTok Ads, GA4 e Google Search Console.

## Repositorio
- **GitHub:** https://github.com/carlosgravi/dashboard-media-monitoring
- **Deploy:** https://dashboard-media-monitoring.streamlit.app

## Estrutura
```
Dashboard_Media/
├── app.py                  # Dashboard principal (12 paginas, 5 grupos)
├── insights_midia.py       # Semaforos, insights, recomendacoes, anomalias
├── requirements.txt
├── AJ.jpg                  # Logo
├── .streamlit/config.toml  # Tema AJ
├── .github/workflows/      # Pipeline diario (7h BRT)
├── scripts/
│   ├── extrair_google_ads.py
│   ├── extrair_meta_ads.py
│   ├── extrair_tiktok_ads.py
│   ├── extrair_ga4.py
│   ├── extrair_search_console.py
│   ├── consolidar_cross_platform.py
│   ├── gerar_recomendacoes.py
│   └── notificar_whatsapp.py
└── Dados/
    ├── Google_Ads/     (6 CSVs)
    ├── Meta_Ads/       (7 CSVs)
    ├── TikTok_Ads/     (5 CSVs)
    ├── GA4/            (4 CSVs)
    ├── Search_Console/ (3 CSVs)
    └── Consolidado/    (7 CSVs)
```

## Paginas (12)
### Grupo 1: Visao Geral
1. Resumo Executivo - KPIs, semaforos, distribuicao verba, treemap campanhas
2. Tendencias - Evolucao ROAS/CPA mensal, area empilhada, dia da semana

### Grupo 2: Por Plataforma
3. Google Ads - 5 tabs (Campanhas, Keywords, Demo, Geo, Dispositivos)
4. Meta Ads - 5 tabs (Campanhas, Plataformas, Posicionamento, Video, Demo)
5. TikTok Ads - 3 tabs (Campanhas, Video Engagement, Demo)
6. GA4 / Search Console - 3 tabs (Fontes, Landing Pages, Consultas)

### Grupo 3: Cross-Platform
7. Comparativo - CPA/ROAS lado a lado, radar 5 dimensoes, ranking
8. Funil Integrado - Impressoes → Cliques → LPV → Sessoes → Conversoes
9. Audiencia - Demografico cruzado, heatmap CPA por segmento

### Grupo 4: Otimizacao
10. Onde Investir - Distribuicao atual vs recomendada, simulador cenarios
11. Alertas e Anomalias - Deteccao automatica (media movel 7d, 2 std)

### Grupo 5: Ferramentas
12. Documentacao - Glossario, metodologia, referencia de dados

## Autenticacao
- bcrypt (mesmo padrao dos outros dashboards)
- secrets.toml com usuarios e roles
- Suporte a `paginas` para restringir acesso

## Pipeline
- Diario as 7h BRT via GitHub Actions
- 5 extratores independentes (continue-on-error)
- Consolidacao cross-platform + recomendacoes
- Notificacao WhatsApp (self-hosted runner)

## Credenciais Necessarias (GitHub Secrets)
- Google Ads: developer_token, client_id/secret, refresh_token, login_customer_id, customer_id
- Meta Ads: access_token, ad_account_id, app_id/secret
- TikTok Ads: access_token, advertiser_id
- GA4: property_id, service_account_json (base64)
- Search Console: site_url (usa mesma SA do GA4)

## Sessoes de Trabalho
- Sessao 1 (03-04/03/2026): Implementacao completa do projeto - estrutura, 7 scripts de extracao, insights_midia.py, app.py com 12 paginas, GitHub Actions workflow, notificacao WhatsApp
- Sessao 1 (cont.): Criacao repo GitHub (carlosgravi/dashboard-media-monitoring), push inicial
- Sessao 1 (cont.): Adaptacao multi-shopping: TikTok (tokens separados por BC) e Google Ads (customer IDs por MCC)
- Sessao 1 (cont.): Configuracao de credenciais - GA4 + Search Console (3 secrets OK), TikTok (app pendente aprovacao), Meta (app criado, token pendente)

## Status Credenciais (GitHub Secrets)
| Plataforma | Status | Secrets |
|-----------|--------|---------|
| GA4 + Search Console | ✅ OK | GA4_PROPERTY_ID, GA4_SERVICE_ACCOUNT_JSON, SEARCH_CONSOLE_SITE_URL |
| Meta Ads | ✅ OK (4 secrets) | META_ADS_APP_ID, META_ADS_APP_SECRET, META_ADS_ACCESS_TOKEN, META_ADS_CONFIG |
| Google Ads | ✅ OK (5 secrets) | GOOGLE_ADS_DEVELOPER_TOKEN, CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, LOGIN_CUSTOMER_ID, CUSTOMER_ID |
| TikTok Ads | ⏳ PENDENTE | App resubmetido (site almeidajunior.com.br), aguardando aprovacao |

## Self-Hosted Runner
- **Runner:** `media-runner` em `C:\actions-runner-media\`
- **Servico Windows:** `actions.runner.media` (auto-start)
- **Funcao:** executa job `notificar-whatsapp` (acesso localhost:3001)

## Sessoes de Trabalho
- Sessao 1 (03-04/03/2026): Implementacao completa do projeto - estrutura, 7 scripts de extracao, insights_midia.py, app.py com 12 paginas, GitHub Actions workflow, notificacao WhatsApp
- Sessao 1 (cont.): Criacao repo GitHub (carlosgravi/dashboard-media-monitoring), push inicial
- Sessao 1 (cont.): Adaptacao multi-shopping: TikTok (tokens separados por BC) e Google Ads (customer IDs por MCC)
- Sessao 1 (cont.): Configuracao de credenciais - GA4 + Search Console (3 secrets OK), TikTok (app pendente aprovacao), Meta (app criado, token pendente)
- Sessao 2 (06/03/2026): Configuracao completa de credenciais Meta Ads (multi-conta 8 ad accounts) e Google Ads (MCC + OAuth2)
- Sessao 2 (cont.): TikTok rejeitado (site invalido), resubmetido com almeidajunior.com.br
- Sessao 2 (cont.): Instalacao gh CLI, criacao runner media-runner, servico Windows
- Sessao 2 (cont.): Fix workflow (nomes secrets Meta, setup-python no job whatsapp)
- Sessao 2 (cont.): Pipeline testado com sucesso - extracao OK + notificacao WhatsApp OK

## Proximos Passos (ao retomar)
1. **TikTok Ads:** Verificar aprovacao do app, configurar secrets
2. **Investigar erros extratores:** Google Ads e Meta Ads retornaram erro no pipeline (credenciais podem precisar ajuste)
3. **secrets.toml:** Criar usuarios para login no dashboard
4. **Deploy Streamlit Cloud**

## Notas Tecnicas
- TikTok: cada shopping tem BC separado → TIKTOK_ADS_CONFIG (JSON) com token+advertiser_id por shopping
- Google Ads: conta unica (242-948-0394) sob MCC AJ Digital (672-994-0117) → GOOGLE_ADS_CUSTOMER_ID
- Meta Ads: 8 contas (6 shoppings + AJ Realty + CS Residences) → META_ADS_CONFIG (JSON)
- GA4: 7 sites (1 principal + 1 por shopping) - por enquanto extrai so o principal
- Service Account: projeto "dashboard-almeida-junior" no Google Cloud
- Self-hosted runners: normas-runner (C:\actions-runner-normas) + media-runner (C:\actions-runner-media)
