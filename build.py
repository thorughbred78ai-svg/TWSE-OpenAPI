
#!/usr/bin/env python3
"""
TWSE OpenAPI Dashboard Builder
抓取台灣證券交易所與櫃買中心 OpenAPI 資料並生成靜態搜尋網站
"""

import json
import urllib.request
from pathlib import Path

# ===== TWSE 上市資料端點（openapi.twse.com.tw/v1）=====
TWSE_ENDPOINTS = {
    "公司治理": [
        {"id": "opendata/t187ap03_L", "name": "上市公司基本資料", "desc": "公司全名、產業別、統一編號、資本額、成立日期、董監事"},
        {"id": "opendata/t187ap04_L", "name": "上市公司董事監察人資料", "desc": "董監事姓名、職稱、選任時持股、持有股份"},
        {"id": "opendata/t187ap05_L", "name": "上市公司每月營業收入", "desc": "當月營收、上月營收、去年同月、增減百分比"},
        {"id": "opendata/t187ap45_L", "name": "上市公司股利分派情形", "desc": "現金股利、股票股利、除權息日期、股東會日期"},
        {"id": "opendata/t187ap46_L_1", "name": "ESG資訊揭露-公司概況", "desc": "員工人數、營運據點、產品與服務等"},
        {"id": "opendata/t187ap46_L_2", "name": "ESG資訊揭露-環境", "desc": "溫室氣體排放、能源使用、水資源管理等"},
        {"id": "opendata/t187ap46_L_3", "name": "ESG資訊揭露-社會", "desc": "員工福利、培訓時數、職業安全衛生等"},
        {"id": "opendata/t187ap46_L_4", "name": "ESG資訊揭露-治理", "desc": "董事會運作、內控機制、資訊透明等"},
        {"id": "opendata/t187ap46_L_18", "name": "ESG資訊揭露-持股及控制力", "desc": "持股結構、控制力相關資訊"},
        {"id": "opendata/t187ap46_L_19", "name": "ESG資訊揭露-風險管理政策", "desc": "風險管理政策與關鍵材料風險"},
        {"id": "opendata/t187ap46_L_20", "name": "ESG資訊揭露-反競爭行為法律訴訟", "desc": "反競爭行為相關法律訴訟金額"},
        {"id": "opendata/t187ap46_L_21", "name": "ESG資訊揭露-職業安全衛生", "desc": "職業災害、火災件數與死傷人數"},
    ],
    "證券交易": [
        {"id": "exchangeReport/STOCK_DAY_ALL", "name": "上市個股日成交資訊（全市場）", "desc": "全部上市股票當日開高低收、成交量、成交金額、成交筆數"},
        {"id": "exchangeReport/BWIBBU_ALL", "name": "上市個股日本益比殖利率", "desc": "本益比、殖利率、股價淨值比（全市場）"},
        {"id": "exchangeReport/MI_INDEX", "name": "大盤統計資訊", "desc": "每日大盤成交統計、漲跌家數"},
    ],
    "權證": [
        {"id": "opendata/t187ap11_L", "name": "上市權證基本資料", "desc": "權證標的、履約價、到期日、發行人"},
        {"id": "opendata/t187ap12_L", "name": "上市權證交易資料", "desc": "權證每日交易行情、成交量、收盤價"},
    ],
    "券商資料": [
        {"id": "opendata/t187ap30_L", "name": "上市券商分公司成交資訊", "desc": "各券商分公司每日成交金額與成交量"},
        {"id": "opendata/t187ap31_L", "name": "上市券商總公司成交資訊", "desc": "各券商總公司每日成交金額與成交量"},
    ],
}

# ===== TPEx 上櫃資料端點（www.tpex.org.tw/openapi/v1）=====
TPEX_ENDPOINTS = {
    "上櫃公司資料": [
        {"id": "mopsfin_t187ap03_O", "name": "上櫃公司基本資料", "desc": "上櫃公司基本資料（欄位英文命名）"},
    ],
    "上櫃股票行情": [
        {"id": "tpex_mainboard_daily_close_quotes", "name": "上櫃股票行情", "desc": "上櫃股票每日開高低收、成交量、成交金額"},
        {"id": "tpex_mainboard_quotes", "name": "上櫃股票收盤行情", "desc": "上櫃股票收盤行情資料"},
        {"id": "tpex_mainborad_highlight", "name": "上櫃股票市場現況", "desc": "上櫃市場整體現況統計"},
    ],
    "上櫃本益比殖利率": [
        {"id": "tpex_mainboard_peratio_analysis", "name": "上櫃個股本益比殖利率", "desc": "上櫃股票本益比、殖利率、股價淨值比"},
    ],
    "上櫃融資融券": [
        {"id": "tpex_mainboard_margin_balance", "name": "上櫃融資融券餘額", "desc": "上櫃股票融資餘額、融券餘額"},
        {"id": "tpex_margin_sbl", "name": "上櫃融券借券賣出餘額", "desc": "上櫃股票融券借券賣出餘額"},
    ],
    "上櫃除權除息": [
        {"id": "tpex_exright_daily", "name": "上櫃除權除息計算結果", "desc": "上櫃股票除權除息計算結果表"},
        {"id": "tpex_exright_prepost", "name": "上櫃除權除息預告", "desc": "上櫃股票除權除息預告表"},
    ],
    "上櫃其他": [
        {"id": "tpex_odd_stock", "name": "上櫃零股交易資訊", "desc": "上櫃股票零股交易行情"},
        {"id": "tpex_off_market", "name": "上櫃盤後定價行情", "desc": "上櫃股票盤後定價交易行情"},
        {"id": "tpex_cmode", "name": "上櫃變更交易資訊", "desc": "變更交易、分盤交易、管理股票與停止交易資訊"},
        {"id": "tpex_index", "name": "櫃買指數歷史資料", "desc": "櫃買指數歷史收盤資料"},
        {"id": "tpex50_index", "name": "富櫃50指數", "desc": "富櫃50指數歷史收盤指數"},
    ],
}

BASE_URL_TWSE = "https://openapi.twse.com.tw/v1"
BASE_URL_TPEX = "https://www.tpex.org.tw/openapi/v1"


def fetch_data(endpoint_id, base_url):
    """抓取單一端點資料"""
    url = f"{base_url}/{endpoint_id}"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "TWSE-Dashboard/1.0 (GitHub-Action)"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8")
            if not content.strip():
                return {"error": "API 回傳空內容", "endpoint": endpoint_id, "url": url}
            return json.loads(content)
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "endpoint": endpoint_id, "url": url}
    except urllib.error.URLError as e:
        return {"error": f"URL Error: {e.reason}", "endpoint": endpoint_id, "url": url}
    except json.JSONDecodeError as e:
        preview = content[:200] if 'content' in dir() else "(無法取得內容)"
        return {"error": f"JSON 解析失敗: {str(e)}", "endpoint": endpoint_id, "url": url, "preview": preview}
    except Exception as e:
        return {"error": str(e), "endpoint": endpoint_id, "url": url}


def fetch_all_data():
    """抓取所有端點資料"""
    all_data = {}

    print("[TWSE] 開始抓取上市資料...")
    for category, endpoints in TWSE_ENDPOINTS.items():
        all_data[category] = []
        for ep in endpoints:
            print(f"  抓取: {ep['id']}")
            data = fetch_data(ep["id"], BASE_URL_TWSE)
            all_data[category].append({
                **ep,
                "data": data,
                "count": len(data) if isinstance(data, list) else 0,
                "has_error": isinstance(data, dict) and "error" in data
            })

    print("[TPEx] 開始抓取上櫃資料...")
    for category, endpoints in TPEX_ENDPOINTS.items():
        if category not in all_data:
            all_data[category] = []
        for ep in endpoints:
            print(f"  抓取: {ep['id']}")
            data = fetch_data(ep["id"], BASE_URL_TPEX)
            all_data[category].append({
                **ep,
                "data": data,
                "count": len(data) if isinstance(data, list) else 0,
                "has_error": isinstance(data, dict) and "error" in data
            })

    return all_data


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TWSE OpenAPI 資料儀表板</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #0f172a;
  --surface: #1e293b;
  --surface-2: #334155;
  --ink: #f8fafc;
  --muted: #94a3b8;
  --accent: #38bdf8;
  --accent-2: #818cf8;
  --success: #34d399;
  --warning: #fbbf24;
  --danger: #f87171;
  --line: rgba(148,163,184,0.15);
  --radius: 12px;
  --shadow: 0 4px 6px -1px rgba(0,0,0,0.3), 0 2px 4px -2px rgba(0,0,0,0.3);
  --shadow-lg: 0 20px 25px -5px rgba(0,0,0,0.4), 0 8px 10px -6px rgba(0,0,0,0.4);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", sans-serif;
  background: var(--bg);
  color: var(--ink);
  line-height: 1.6;
  min-height: 100vh;
}
.header {
  background: linear-gradient(135deg, var(--surface) 0%, #0f172a 100%);
  border-bottom: 1px solid var(--line);
  padding: 2rem 1.5rem;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
}
.header-inner { max-width: 1200px; margin: 0 auto; }
.header h1 {
  font-size: clamp(1.5rem, 3vw, 2.2rem);
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.5rem;
}
.header p { color: var(--muted); font-size: 0.95rem; }
.stats-bar {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
  max-width: 1200px;
  margin: 1.5rem auto;
  padding: 0 1.5rem;
}
.stat-card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 1.2rem;
  text-align: center;
  transition: transform 0.2s, box-shadow 0.2s;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }
.stat-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--accent);
  font-family: "JetBrains Mono", monospace;
}
.stat-label {
  font-size: 0.8rem;
  color: var(--muted);
  margin-top: 0.3rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.search-section { max-width: 1200px; margin: 0 auto 1.5rem; padding: 0 1.5rem; }
.search-box {
  width: 100%;
  padding: 1rem 1.2rem;
  font-size: 1rem;
  font-family: inherit;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  color: var(--ink);
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.search-box:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(56,189,248,0.15); }
.search-box::placeholder { color: var(--muted); }
.filter-bar {
  max-width: 1200px;
  margin: 0 auto 1rem;
  padding: 0 1.5rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.filter-btn {
  padding: 0.4rem 0.9rem;
  font-size: 0.85rem;
  font-family: inherit;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 20px;
  color: var(--muted);
  cursor: pointer;
  transition: all 0.2s;
}
.filter-btn:hover, .filter-btn.active {
  background: var(--accent);
  color: var(--bg);
  border-color: var(--accent);
}
.main { max-width: 1200px; margin: 0 auto; padding: 0 1.5rem 3rem; }
.category-section { margin-bottom: 2rem; }
.category-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--accent-2);
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--line);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.category-title .count {
  font-size: 0.75rem;
  background: var(--surface-2);
  padding: 0.15rem 0.5rem;
  border-radius: 10px;
  color: var(--muted);
  font-weight: 400;
}
.endpoint-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1rem;
}
.endpoint-card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 1.2rem;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}
.endpoint-card::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  opacity: 0;
  transition: opacity 0.2s;
}
.endpoint-card:hover::before { opacity: 1; }
.endpoint-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  border-color: var(--surface-2);
}
.endpoint-card.hidden { display: none; }
.endpoint-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
}
.endpoint-name { font-weight: 600; font-size: 1rem; color: var(--ink); }
.endpoint-badge {
  font-size: 0.7rem;
  padding: 0.15rem 0.5rem;
  border-radius: 10px;
  font-weight: 500;
  font-family: "JetBrains Mono", monospace;
}
.badge-success { background: rgba(52,211,153,0.15); color: var(--success); }
.badge-error { background: rgba(248,113,113,0.15); color: var(--danger); }
.endpoint-desc { color: var(--muted); font-size: 0.9rem; margin-bottom: 0.8rem; }
.endpoint-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
  color: var(--muted);
}
.endpoint-id {
  font-family: "JetBrains Mono", monospace;
  background: var(--surface-2);
  padding: 0.2rem 0.5rem;
  border-radius: 6px;
  font-size: 0.75rem;
}
.record-count { font-family: "JetBrains Mono", monospace; }
.modal-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  z-index: 200;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}
.modal-overlay.active { display: flex; }
.modal {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  width: 100%;
  max-width: 950px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
}
.modal-header {
  padding: 1.2rem;
  border-bottom: 1px solid var(--line);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal-title { font-size: 1.1rem; font-weight: 600; }
.modal-close {
  background: none;
  border: none;
  color: var(--muted);
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.2rem 0.5rem;
  line-height: 1;
  border-radius: 6px;
  transition: all 0.2s;
}
.modal-close:hover { background: var(--surface-2); color: var(--ink); }
.modal-body { padding: 1.2rem; overflow-y: auto; flex: 1; }
.data-table-wrap {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid var(--line);
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}
.data-table th {
  background: var(--surface-2);
  padding: 0.7rem 0.8rem;
  text-align: left;
  font-weight: 500;
  color: var(--accent);
  white-space: nowrap;
  position: sticky;
  top: 0;
}
.data-table td {
  padding: 0.6rem 0.8rem;
  border-bottom: 1px solid var(--line);
  color: var(--ink);
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.data-table tr:hover td { background: rgba(56,189,248,0.05); }
.data-table tr:last-child td { border-bottom: none; }
.no-data { text-align: center; padding: 3rem; color: var(--muted); }
.no-data-icon { font-size: 3rem; margin-bottom: 1rem; }
.json-preview {
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 1rem;
  font-family: "JetBrains Mono", monospace;
  font-size: 0.8rem;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--muted);
  max-height: 400px;
  overflow-y: auto;
}
.tabs {
  display: flex;
  gap: 0.3rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid var(--line);
  padding-bottom: 0.5rem;
}
.tab-btn {
  padding: 0.4rem 0.9rem;
  font-size: 0.85rem;
  font-family: inherit;
  background: none;
  border: none;
  border-radius: 6px;
  color: var(--muted);
  cursor: pointer;
  transition: all 0.2s;
}
.tab-btn:hover { color: var(--ink); }
.tab-btn.active { background: var(--surface-2); color: var(--accent); }
.tab-panel { display: none; }
.tab-panel.active { display: block; }
.data-search-box {
  width: 100%;
  padding: 0.6rem 1rem;
  font-size: 0.9rem;
  font-family: inherit;
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: 8px;
  color: var(--ink);
  outline: none;
  margin-bottom: 0.5rem;
}
.data-search-box:focus { border-color: var(--accent); }
.data-search-box::placeholder { color: var(--muted); }
.search-hint {
  font-size: 0.8rem;
  color: var(--muted);
  margin-bottom: 0.8rem;
}
.result-count {
  font-size: 0.8rem;
  color: var(--accent);
  margin-bottom: 0.5rem;
  font-weight: 500;
}
.error-url {
  font-size: 0.75rem;
  color: var(--muted);
  margin-top: 0.5rem;
  word-break: break-all;
}
.footer {
  text-align: center;
  padding: 2rem;
  color: var(--muted);
  font-size: 0.85rem;
  border-top: 1px solid var(--line);
  margin-top: 2rem;
}
.footer a { color: var(--accent); text-decoration: none; }
.footer a:hover { text-decoration: underline; }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--surface-2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }
@media (max-width: 640px) {
  .endpoint-grid { grid-template-columns: 1fr; }
  .stats-bar { grid-template-columns: repeat(2, 1fr); }
  .header { padding: 1.2rem 1rem; }
  .main, .search-section, .filter-bar { padding-left: 1rem; padding-right: 1rem; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
</head>
<body>
<header class="header">
  <div class="header-inner">
    <h1>TWSE OpenAPI 資料儀表板</h1>
    <p>台灣證券交易所與櫃買中心免費開放資料 API 瀏覽與查詢工具 · 每日自動更新</p>
  </div>
</header>
<div class="stats-bar">
  <div class="stat-card">
    <div class="stat-value">{{TOTAL_ENDPOINTS}}</div>
    <div class="stat-label">API 端點</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{{TOTAL_RECORDS}}</div>
    <div class="stat-label">總記錄數</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{{CATEGORY_COUNT}}</div>
    <div class="stat-label">資料類別</div>
  </div>
  <div class="stat-card">
    <div class="stat-value" style="color: {{ERROR_COLOR}};">{{ERROR_COUNT}}</div>
    <div class="stat-label">異常端點</div>
  </div>
</div>
<div class="search-section">
  <input type="text" class="search-box" id="searchBox" placeholder="搜尋端點名稱、代號或描述... (例如: 股利、ETF、融資)">
</div>
<div class="filter-bar" id="filterBar">
  <button class="filter-btn active" data-category="all">全部</button>
</div>
<main class="main" id="mainContent"></main>
<div class="modal-overlay" id="modalOverlay">
  <div class="modal">
    <div class="modal-header">
      <div class="modal-title" id="modalTitle">端點詳情</div>
      <button class="modal-close" id="modalClose">&times;</button>
    </div>
    <div class="modal-body">
      <div class="tabs">
        <button class="tab-btn active" data-tab="table">資料表格</button>
        <button class="tab-btn" data-tab="json">JSON 原始資料</button>
      </div>
      <div class="tab-panel active" id="tab-table"></div>
      <div class="tab-panel" id="tab-json"></div>
    </div>
  </div>
</div>
<footer class="footer">
  <p>資料來源: <a href="https://openapi.twse.com.tw/" target="_blank">臺灣證券交易所 OpenAPI</a> ·
     <a href="https://www.tpex.org.tw/openapi/" target="_blank">櫃買中心 OpenAPI</a> ·
     本頁面由 GitHub Actions 自動生成</p>
</footer>
<script>
const API_DATA = {{DATA_JSON}};
const ENDPOINTS_META = {{ENDPOINTS_JSON}};
const searchBox = document.getElementById('searchBox');
const filterBar = document.getElementById('filterBar');
const mainContent = document.getElementById('mainContent');
const modalOverlay = document.getElementById('modalOverlay');
const modalTitle = document.getElementById('modalTitle');
const modalClose = document.getElementById('modalClose');
const tabTable = document.getElementById('tab-table');
const tabJson = document.getElementById('tab-json');
let currentCategory = 'all';
let currentSearch = '';
let currentEndpointData = null;
let currentFilteredRows = null;
let currentDataSearch = '';

function initFilters() {
  Object.keys(ENDPOINTS_META).forEach(cat => {
    const btn = document.createElement('button');
    btn.className = 'filter-btn';
    btn.textContent = cat;
    btn.dataset.category = cat;
    btn.addEventListener('click', () => setCategory(cat));
    filterBar.appendChild(btn);
  });
}
function setCategory(cat) {
  currentCategory = cat;
  document.querySelectorAll('.filter-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.category === cat);
  });
  render();
}
function render() {
  mainContent.innerHTML = '';
  const categories = currentCategory === 'all' ? Object.keys(API_DATA) : [currentCategory];
  let hasResults = false;
  categories.forEach(category => {
    const endpoints = API_DATA[category].filter(ep => {
      const q = currentSearch.toLowerCase();
      return !q || ep.name.toLowerCase().includes(q) || ep.id.toLowerCase().includes(q) || ep.desc.toLowerCase().includes(q);
    });
    if (endpoints.length === 0) return;
    hasResults = true;
    const section = document.createElement('div');
    section.className = 'category-section';
    section.innerHTML = '<h2 class="category-title">' + category + '<span class="count">' + endpoints.length + ' 個端點</span></h2><div class="endpoint-grid"></div>';
    const grid = section.querySelector('.endpoint-grid');
    endpoints.forEach(ep => {
      const card = document.createElement('div');
      card.className = 'endpoint-card';
      const badgeClass = ep.has_error ? 'badge-error' : 'badge-success';
      const badgeText = ep.has_error ? '異常' : '正常';
      card.innerHTML = '<div class="endpoint-header"><div class="endpoint-name">' + ep.name + '</div><span class="endpoint-badge ' + badgeClass + '">' + badgeText + '</span></div><div class="endpoint-desc">' + ep.desc + '</div><div class="endpoint-meta"><span class="endpoint-id">' + ep.id + '</span><span class="record-count">' + ep.count.toLocaleString() + ' 筆</span></div>';
      card.addEventListener('click', () => openModal(ep, category));
      grid.appendChild(card);
    });
    mainContent.appendChild(section);
  });
  if (!hasResults) {
    mainContent.innerHTML = '<div class="no-data"><div class="no-data-icon">🔍</div><p>沒有符合「<strong>' + escapeHtml(currentSearch) + '</strong>」的結果</p></div>';
  }
}

function filterDataTable(searchText) {
  currentDataSearch = searchText;
  if (!currentEndpointData || !Array.isArray(currentEndpointData)) return;
  const q = searchText.toLowerCase().trim();
  if (!q) {
    currentFilteredRows = currentEndpointData;
  } else {
    currentFilteredRows = currentEndpointData.filter(row => {
      return Object.values(row).some(val => {
        if (val === null || val === undefined) return false;
        return String(val).toLowerCase().includes(q);
      });
    });
  }
  renderDataTable(currentFilteredRows, q);
  updateResultCount(currentFilteredRows.length, currentEndpointData.length);
}

function updateResultCount(filtered, total) {
  const countEl = document.getElementById('resultCount');
  if (countEl) {
    if (currentDataSearch && currentDataSearch.trim()) {
      countEl.textContent = '顯示 ' + filtered.toLocaleString() + ' / ' + total.toLocaleString() + ' 筆資料';
    } else {
      countEl.textContent = '共 ' + total.toLocaleString() + ' 筆資料';
    }
  }
}

function renderDataTable(rows, highlightText) {
  const tableContainer = document.getElementById('tableContainer');
  if (!tableContainer) return;

  if (!rows || rows.length === 0) {
    tableContainer.innerHTML = '<div class="no-data"><div class="no-data-icon">🔍</div><p>沒有符合搜尋條件的資料</p></div>';
    return;
  }
  const columns = Object.keys(rows[0]);
  let tableHtml = '<div class="data-table-wrap"><table class="data-table"><thead><tr>';
  columns.forEach(col => { tableHtml += '<th>' + escapeHtml(col) + '</th>'; });
  tableHtml += '</tr></thead><tbody>';
  rows.slice(0, 200).forEach(row => {
    tableHtml += '<tr>';
    columns.forEach(col => {
      const val = row[col];
      const display = val === null || val === undefined ? '' : String(val);
      let cellHtml = escapeHtml(display);
      if (highlightText && highlightText.trim()) {
        const regex = new RegExp('(' + escapeRegExp(highlightText) + ')', 'gi');
        cellHtml = cellHtml.replace(regex, '<mark style="background:rgba(56,189,248,0.3);color:var(--accent);border-radius:3px;padding:1px 3px;">$1</mark>');
      }
      tableHtml += '<td title="' + escapeHtml(display) + '">' + cellHtml + '</td>';
    });
    tableHtml += '</tr>';
  });
  if (rows.length > 200) {
    tableHtml += '<tr><td colspan="' + columns.length + '" style="text-align:center;color:var(--muted);">... 還有 ' + (rows.length - 200) + ' 筆資料，請使用搜尋縮小範圍或切換 JSON 分頁</td></tr>';
  }
  tableHtml += '</tbody></table></div>';
  tableContainer.innerHTML = tableHtml;
}

function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function openModal(ep, category) {
  modalTitle.textContent = ep.name + ' (' + ep.id + ')';
  const jsonStr = JSON.stringify(ep.data, null, 2);
  tabJson.innerHTML = '<pre class="json-preview">' + escapeHtml(jsonStr) + '</pre>';

  if (Array.isArray(ep.data) && ep.data.length > 0) {
    currentEndpointData = ep.data;
    currentFilteredRows = ep.data;
    currentDataSearch = '';

    tabTable.innerHTML =
      '<input type="text" class="data-search-box" id="dataSearchBox" placeholder="在資料中搜尋... 支援「公司代號」「公司名稱」等關鍵字">' +
      '<div class="search-hint">💡 提示：輸入股票代號（如 2330）或公司名稱（如 台積電）即可篩選資料</div>' +
      '<div class="result-count" id="resultCount">共 ' + ep.data.length.toLocaleString() + ' 筆資料</div>' +
      '<div id="tableContainer"></div>';

    const dataSearchBox = document.getElementById('dataSearchBox');
    dataSearchBox.addEventListener('input', function(e) {
      filterDataTable(e.target.value);
    });

    renderDataTable(currentFilteredRows, '');
  } else if (ep.has_error) {
    let errorHtml = '<div class="no-data"><div class="no-data-icon">⚠️</div><p>資料抓取失敗</p><pre class="json-preview">' + escapeHtml(JSON.stringify(ep.data, null, 2)) + '</pre>';
    if (ep.data && ep.data.url) {
      errorHtml += '<div class="error-url">請求 URL: ' + escapeHtml(ep.data.url) + '</div>';
    }
    errorHtml += '</div>';
    tabTable.innerHTML = errorHtml;
  } else {
    tabTable.innerHTML = '<div class="no-data"><div class="no-data-icon">📭</div><p>此端點暫無資料</p></div>';
  }
  document.querySelectorAll('.tab-btn').forEach((b, i) => b.classList.toggle('active', i === 0));
  document.querySelectorAll('.tab-panel').forEach((p, i) => p.classList.toggle('active', i === 0));
  modalOverlay.classList.add('active');
  document.body.style.overflow = 'hidden';
}
function closeModal() {
  modalOverlay.classList.remove('active');
  document.body.style.overflow = '';
  currentEndpointData = null;
  currentFilteredRows = null;
  currentDataSearch = '';
}
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
searchBox.addEventListener('input', (e) => { currentSearch = e.target.value; render(); });
modalClose.addEventListener('click', closeModal);
modalOverlay.addEventListener('click', (e) => { if (e.target === modalOverlay) closeModal(); });
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.dataset.tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + tab).classList.add('active');
  });
});
initFilters();
render();
</script>
</body>
</html>"""


def generate_html(all_data):
    """生成靜態 HTML 網站"""
    total_endpoints = sum(len(eps) for eps in all_data.values())
    total_records = sum(ep["count"] for cat in all_data.values() for ep in cat)
    error_count = sum(1 for cat in all_data.values() for ep in cat if ep["has_error"])

    data_json = json.dumps(all_data, ensure_ascii=False, default=str)
    endpoints_json = json.dumps({k: [e["id"] for e in v] for k, v in all_data.items()}, ensure_ascii=False)

    html = HTML_TEMPLATE
    html = html.replace("{{TOTAL_ENDPOINTS}}", str(total_endpoints))
    html = html.replace("{{TOTAL_RECORDS}}", f"{total_records:,}")
    html = html.replace("{{CATEGORY_COUNT}}", str(len(all_data)))
    html = html.replace("{{ERROR_COUNT}}", str(error_count))
    html = html.replace("{{ERROR_COLOR}}", 'var(--danger)' if error_count > 0 else 'var(--success)')
    html = html.replace("{{DATA_JSON}}", data_json)
    html = html.replace("{{ENDPOINTS_JSON}}", endpoints_json)
    return html


def main():
    public_dir = Path("public")
    public_dir.mkdir(exist_ok=True)
    print("開始抓取 TWSE / TPEx OpenAPI 資料...")
    all_data = fetch_all_data()
    print("生成靜態網站...")
    html = generate_html(all_data)
    index_path = public_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    data_path = public_dir / "data.json"
    data_path.write_text(json.dumps(all_data, ensure_ascii=False, indent=2), encoding="utf-8")
    total_records = sum(ep["count"] for cat in all_data.values() for ep in cat)
    error_count = sum(1 for cat in all_data.values() for ep in cat if ep["has_error"])
    print(f"完成！總記錄數: {total_records:,}，異常端點: {error_count}")


if __name__ == "__main__":
    main()
