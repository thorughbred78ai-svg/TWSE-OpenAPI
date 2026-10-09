#!/usr/bin/env python3
"""
TWSE 上市個股及大盤統計資訊儀表板 (圖示化版)
"""

import json
import urllib.request
from pathlib import Path

ENDPOINTS = [
    {"id": "exchangeReport/MI_INDEX", "tab_id": "mi_index", "title": "大盤統計資訊", "icon": "📊", "color": "#38bdf8", "desc": "每日大盤成交統計、漲跌家數"},
    {"id": "exchangeReport/STOCK_DAY_ALL", "tab_id": "stock_day", "title": "上市個股日成交資訊", "icon": "📈", "color": "#34d399", "desc": "全部上市股票當日開高低收、成交量、成交金額"},
    {"id": "exchangeReport/BWIBBU_ALL", "tab_id": "bwibbu", "title": "上市個股本益比殖利率", "icon": "💰", "color": "#fbbf24", "desc": "本益比、殖利率、股價淨值比"},
    {"id": "opendata/t187ap05_L", "tab_id": "revenue", "title": "上市公司每月營業收入", "icon": "📋", "color": "#a78bfa", "desc": "當月營收、上月營收、去年同月、增減百分比"},
    {"id": "opendata/t187ap45_L", "tab_id": "dividend", "title": "上市公司股利分派情形", "icon": "🎁", "color": "#f472b6", "desc": "現金股利、股票股利、除權息日期"},
    {"id": "opendata/t187ap03_L", "tab_id": "company", "title": "上市公司基本資料", "icon": "🏢", "color": "#fb923c", "desc": "公司全名、產業別、資本額、成立日期"},
]

BASE_URL = "https://openapi.twse.com.tw/v1"


def fetch_data(endpoint_id):
    url = f"{BASE_URL}/{endpoint_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TWSE-Dashboard/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8")
            if not content.strip():
                return {"error": "API 回傳空內容", "url": url}
            return json.loads(content)
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "url": url}
    except urllib.error.URLError as e:
        return {"error": f"URL Error: {e.reason}", "url": url}
    except json.JSONDecodeError as e:
        return {"error": f"JSON 解析失敗: {str(e)}", "url": url}
    except Exception as e:
        return {"error": str(e), "url": url}


def fetch_all():
    result = {}
    for ep in ENDPOINTS:
        print(f"  抓取: {ep['id']}")
        data = fetch_data(ep["id"])
        result[ep["tab_id"]] = {
            **ep,
            "data": data,
            "count": len(data) if isinstance(data, list) else 0,
            "has_error": isinstance(data, dict) and "error" in data,
        }
    return result


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TWSE 上市個股及大盤統計資訊</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #0b1121;
  --surface: #151e32;
  --surface-2: #1e293b;
  --surface-3: #334155;
  --ink: #f1f5f9;
  --muted: #94a3b8;
  --accent: #38bdf8;
  --accent-2: #818cf8;
  --success: #34d399;
  --warning: #fbbf24;
  --danger: #f87171;
  --line: rgba(148,163,184,0.12);
  --radius: 14px;
  --shadow: 0 4px 6px -1px rgba(0,0,0,0.4);
  --shadow-lg: 0 20px 25px -5px rgba(0,0,0,0.5);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", sans-serif;
  background: var(--bg);
  color: var(--ink);
  line-height: 1.6;
  min-height: 100vh;
}

/* ===== Header ===== */
.header {
  background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
  border-bottom: 1px solid var(--line);
  padding: 1.5rem;
}
.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1.5rem;
}
.header-left .badge {
  display: inline-block;
  background: rgba(56,189,248,0.15);
  color: var(--accent);
  font-size: 0.7rem;
  padding: 0.25rem 0.7rem;
  border-radius: 20px;
  margin-bottom: 0.5rem;
  font-weight: 500;
  letter-spacing: 0.05em;
}
.header-left h1 {
  font-size: clamp(1.3rem, 2.5vw, 1.8rem);
  font-weight: 700;
  background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.3rem;
}
.header-left p {
  color: var(--muted);
  font-size: 0.85rem;
}
.header-right {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
}
.stat-item {
  text-align: center;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 0.8rem 1.2rem;
  min-width: 90px;
}
.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--accent);
  font-family: "JetBrains Mono", monospace;
  display: block;
  line-height: 1.2;
}
.stat-label {
  font-size: 0.65rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-top: 0.2rem;
}

/* ===== Tab Cards ===== */
.tab-section {
  max-width: 1200px;
  margin: 2rem auto 1.5rem;
  padding: 0 1.5rem;
}
.tab-section-title {
  font-size: 0.75rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.tab-section-title::before {
  content: "";
  display: inline-block;
  width: 4px;
  height: 16px;
  background: linear-gradient(180deg, var(--accent), var(--accent-2));
  border-radius: 2px;
}
.tab-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 1rem;
}
.tab-card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 1.2rem 1rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}
.tab-card::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: var(--card-color);
  opacity: 0;
  transition: opacity 0.25s;
}
.tab-card:hover::before,
.tab-card.active::before { opacity: 1; }
.tab-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
  border-color: var(--card-color);
}
.tab-card.active {
  background: var(--surface-2);
  border-color: var(--card-color);
  box-shadow: 0 0 20px rgba(0,0,0,0.3), 0 0 0 1px var(--card-color);
}
.tab-icon {
  font-size: 2.2rem;
  margin-bottom: 0.6rem;
  display: block;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
}
.tab-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 0.3rem;
}
.tab-desc {
  font-size: 0.7rem;
  color: var(--muted);
  line-height: 1.4;
}
.tab-count {
  position: absolute;
  top: 0.6rem;
  right: 0.6rem;
  font-size: 0.65rem;
  font-family: "JetBrains Mono", monospace;
  background: var(--surface-3);
  color: var(--muted);
  padding: 0.15rem 0.4rem;
  border-radius: 8px;
}
.tab-card.active .tab-count {
  background: var(--card-color);
  color: var(--bg);
}

/* ===== Content Panel ===== */
.content-panel {
  display: none;
}
.content-panel.active {
  display: block;
}
.main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem 3rem;
}
.panel-header {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-bottom: 1.2rem;
  padding-bottom: 0.8rem;
  border-bottom: 1px solid var(--line);
}
.panel-icon {
  font-size: 1.5rem;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 12px;
}
.panel-title {
  font-size: 1.1rem;
  font-weight: 600;
}
.panel-subtitle {
  font-size: 0.8rem;
  color: var(--muted);
}

/* ===== Toolbar ===== */
.toolbar {
  display: flex;
  gap: 0.8rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  align-items: center;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 0.8rem 1rem;
}
.search-box {
  flex: 1;
  min-width: 200px;
  padding: 0.6rem 1rem;
  font-size: 0.9rem;
  font-family: inherit;
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: 10px;
  color: var(--ink);
  outline: none;
  transition: border-color 0.2s;
}
.search-box:focus { border-color: var(--accent); }
.search-box::placeholder { color: var(--muted); }
.industry-select {
  padding: 0.6rem 1rem;
  font-size: 0.9rem;
  font-family: inherit;
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: 10px;
  color: var(--ink);
  outline: none;
  cursor: pointer;
  min-width: 150px;
}
.industry-select:focus { border-color: var(--accent); }
.result-count {
  font-size: 0.8rem;
  color: var(--accent);
  font-weight: 500;
  margin-bottom: 0.8rem;
  min-height: 1.2em;
}

/* ===== Table ===== */
.data-table-wrap {
  overflow-x: auto;
  border-radius: var(--radius);
  border: 1px solid var(--line);
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}
.data-table th {
  background: var(--surface-2);
  padding: 0.65rem 0.75rem;
  text-align: left;
  font-weight: 500;
  color: var(--accent);
  white-space: nowrap;
  position: sticky;
  top: 0;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
  border-bottom: 2px solid var(--line);
}
.data-table th:hover { background: var(--surface-3); }
.data-table th .sort-indicator {
  display: inline-block;
  margin-left: 0.3rem;
  color: var(--muted);
  font-size: 0.65rem;
  width: 1em;
}
.data-table th.sort-asc .sort-indicator::after { content: "▲"; color: var(--accent); }
.data-table th.sort-desc .sort-indicator::after { content: "▼"; color: var(--accent); }
.data-table td {
  padding: 0.55rem 0.75rem;
  border-bottom: 1px solid var(--line);
  color: var(--ink);
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.data-table tbody tr { transition: background 0.15s; }
.data-table tbody tr:hover td { background: rgba(56,189,248,0.06); }
.data-table tbody tr:last-child td { border-bottom: none; }
.no-data { text-align: center; padding: 4rem 2rem; color: var(--muted); }
.no-data-icon { font-size: 3rem; margin-bottom: 1rem; opacity: 0.6; }
mark {
  background: rgba(56,189,248,0.25);
  color: #7dd3fc;
  border-radius: 3px;
  padding: 1px 3px;
}
.error-box {
  background: rgba(248,113,113,0.08);
  border: 1px solid rgba(248,113,113,0.25);
  border-radius: var(--radius);
  padding: 2rem;
}
.error-url { font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem; word-break: break-all; }

/* ===== Footer ===== */
.footer {
  text-align: center;
  padding: 2rem;
  color: var(--muted);
  font-size: 0.8rem;
  border-top: 1px solid var(--line);
  margin-top: 2rem;
}
.footer a { color: var(--accent); text-decoration: none; }
.footer a:hover { text-decoration: underline; }

/* ===== Scrollbar ===== */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--surface-3); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .header-inner { flex-direction: column; align-items: flex-start; }
  .header-right { width: 100%; justify-content: space-between; }
  .tab-grid { grid-template-columns: repeat(2, 1fr); }
  .main { padding: 0 1rem 3rem; }
  .tab-section { padding: 0 1rem; }
  .toolbar { flex-direction: column; align-items: stretch; }
  .search-box, .industry-select { width: 100%; }
  .panel-header { flex-wrap: wrap; }
}
@media (max-width: 400px) {
  .tab-grid { grid-template-columns: 1fr; }
  .stat-item { min-width: 70px; padding: 0.6rem 0.8rem; }
  .stat-value { font-size: 1.2rem; }
}
</style>
</head>
<body>

<!-- Header -->
<header class="header">
  <div class="header-inner">
    <div class="header-left">
      <div class="badge">TWSE OPENAPI</div>
      <h1>上市個股及大盤統計資訊</h1>
      <p>臺灣證券交易所免費開放資料 · 每日自動更新</p>
    </div>
    <div class="header-right">
      <div class="stat-item">
        <span class="stat-value">{{TOTAL_ENDPOINTS}}</span>
        <div class="stat-label">API 端點</div>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{TOTAL_RECORDS}}</span>
        <div class="stat-label">總記錄數</div>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{CATEGORY_COUNT}}</span>
        <div class="stat-label">資料類別</div>
      </div>
      <div class="stat-item">
        <span class="stat-value" style="color:{{ERROR_COLOR}};">{{ERROR_COUNT}}</span>
        <div class="stat-label">異常端點</div>
      </div>
    </div>
  </div>
</header>

<!-- Tab Cards -->
<div class="tab-section">
  <div class="tab-section-title">資料類別</div>
  <div class="tab-grid" id="tabGrid"></div>
</div>

<!-- Content Panels -->
<main class="main" id="mainContent"></main>

<!-- Footer -->
<footer class="footer">
  <p>資料來源: <a href="https://openapi.twse.com.tw/" target="_blank">臺灣證券交易所 OpenAPI</a> · 本頁面由 GitHub Actions 自動生成</p>
</footer>

<script>
const API_DATA = {{DATA_JSON}};
const TAB_META = {{TAB_META_JSON}};

let currentTab = "mi_index";
let searchText = "";
let sortState = {};
let industryFilter = "all";

const tabGrid = document.getElementById("tabGrid");
const mainContent = document.getElementById("mainContent");

// ===== Helpers =====
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function parseNumeric(val) {
  if (val == null) return null;
  const s = String(val).replace(/,/g, "").trim();
  if (s.endsWith("%")) {
    const n = parseFloat(s.slice(0, -1));
    return isNaN(n) ? null : n;
  }
  const n = parseFloat(s);
  return isNaN(n) ? null : n;
}

function highlightText(text, query) {
  if (!query) return escapeHtml(text);
  const str = String(text);
  const lowerStr = str.toLowerCase();
  const lowerQuery = query.toLowerCase();
  let result = "";
  let lastIndex = 0;
  let idx = lowerStr.indexOf(lowerQuery);
  while (idx !== -1) {
    result += escapeHtml(str.slice(lastIndex, idx));
    result += "<mark>" + escapeHtml(str.slice(idx, idx + query.length)) + "</mark>";
    lastIndex = idx + query.length;
    idx = lowerStr.indexOf(lowerQuery, lastIndex);
  }
  result += escapeHtml(str.slice(lastIndex));
  return result;
}

// ===== Render Tab Cards =====
function renderTabCards() {
  tabGrid.innerHTML = "";
  TAB_META.forEach(meta => {
    const info = API_DATA[meta.tab_id];
    const count = info ? info.count : 0;
    const isActive = meta.tab_id === currentTab;
    const card = document.createElement("div");
    card.className = "tab-card" + (isActive ? " active" : "");
    card.style.setProperty("--card-color", meta.color);
    card.innerHTML =
      '<span class="tab-count">' + count.toLocaleString() + '</span>' +
      '<span class="tab-icon">' + meta.icon + '</span>' +
      '<div class="tab-title">' + escapeHtml(meta.title) + '</div>' +
      '<div class="tab-desc">' + escapeHtml(meta.desc) + '</div>';
    card.addEventListener("click", () => switchTab(meta.tab_id));
    tabGrid.appendChild(card);
  });
}

// ===== Switch Tab =====
function switchTab(tabId) {
  currentTab = tabId;
  searchText = "";
  industryFilter = "all";
  renderTabCards();
  renderContentPanel(tabId);
}

// ===== Get Industries =====
function getIndustries(tabId) {
  const info = API_DATA[tabId];
  if (!info || !Array.isArray(info.data)) return [];
  const set = new Set();
  info.data.forEach(row => { if (row["產業別"]) set.add(row["產業別"]); });
  return Array.from(set).sort();
}

// ===== Sort Data =====
function sortData(tabId, data) {
  const state = sortState[tabId];
  if (!state || !state.direction) return data;
  const col = state.column;
  const dir = state.direction;
  return [...data].sort((a, b) => {
    const na = parseNumeric(a[col]);
    const nb = parseNumeric(b[col]);
    if (na !== null && nb !== null) {
      return dir === "asc" ? na - nb : nb - na;
    }
    const sa = String(a[col] == null ? "" : a[col]).toLowerCase();
    const sb = String(b[col] == null ? "" : b[col]).toLowerCase();
    if (sa < sb) return dir === "asc" ? -1 : 1;
    if (sa > sb) return dir === "asc" ? 1 : -1;
    return 0;
  });
}

// ===== Filter Data =====
function filterData(tabId) {
  const info = API_DATA[tabId];
  if (!info || !Array.isArray(info.data)) return [];
  let data = info.data;
  if (tabId === "company" && industryFilter !== "all") {
    data = data.filter(row => row["產業別"] === industryFilter);
  }
  if (searchText.trim()) {
    const q = searchText.toLowerCase().trim();
    data = data.filter(row => {
      return Object.values(row).some(val => {
        if (val == null) return false;
        return String(val).toLowerCase().includes(q);
      });
    });
  }
  return data;
}

// ===== Render Table =====
function renderTable(tabId, data) {
  const container = document.getElementById("table-" + tabId);
  const countEl = document.getElementById("count-" + tabId);
  const info = API_DATA[tabId];

  if (!container) return;

  if (info && info.has_error) {
    let html = '<div class="error-box">' +
      '<div style="font-size:1.3rem;margin-bottom:0.5rem;">⚠️ 資料抓取失敗</div>' +
      '<pre style="margin:0;white-space:pre-wrap;word-break:break-all;font-size:0.8rem;color:var(--muted);">' + escapeHtml(JSON.stringify(info.data, null, 2)) + '</pre>';
    if (info.data && info.data.url) {
      html += '<div class="error-url">請求 URL: ' + escapeHtml(info.data.url) + '</div>';
    }
    html += '</div>';
    container.innerHTML = html;
    if (countEl) countEl.textContent = "";
    return;
  }

  if (!data || data.length === 0) {
    container.innerHTML = '<div class="no-data"><div class="no-data-icon">🔍</div><p>沒有符合條件的資料</p></div>';
    if (countEl) countEl.textContent = "0 筆資料";
    return;
  }

  const columns = Object.keys(data[0]);
  const state = sortState[tabId];
  let html = '<div class="data-table-wrap"><table class="data-table"><thead><tr>';
  columns.forEach(col => {
    let sortClass = "";
    if (state && state.column === col) {
      sortClass = state.direction === "asc" ? "sort-asc" : "sort-desc";
    }
    html += '<th class="' + sortClass + '">' +
      '<span onclick="handleSort(\\'' + tabId + '\\', \\' + escapeHtml(col) + '\\')" style="cursor:pointer;">' +
      escapeHtml(col) + '<span class="sort-indicator"></span></span></th>';
  });
  html += '</tr></thead><tbody>';

  data.slice(0, 300).forEach(row => {
    html += '<tr>';
    columns.forEach(col => {
      const val = row[col];
      const display = val == null ? "" : String(val);
      const cell = highlightText(display, searchText);
      html += '<td title="' + escapeHtml(display) + '">' + cell + '</td>';
    });
    html += '</tr>';
  });

  if (data.length > 300) {
    html += '<tr><td colspan="' + columns.length + '" style="text-align:center;color:var(--muted);padding:1rem;">... 還有 ' + (data.length - 300).toLocaleString() + ' 筆資料，請使用搜尋縮小範圍</td></tr>';
  }
  html += '</tbody></table></div>';
  container.innerHTML = html;

  if (countEl) {
    const total = info && Array.isArray(info.data) ? info.data.length : 0;
    countEl.textContent = '顯示 ' + data.length.toLocaleString() + ' / ' + total.toLocaleString() + ' 筆資料';
  }
}

// ===== Sort Handler =====
window.handleSort = function(tabId, column) {
  const state = sortState[tabId] || { column: null, direction: null };
  let direction = "asc";
  if (state.column === column) {
    if (state.direction === "asc") direction = "desc";
    else if (state.direction === "desc") direction = null;
    else direction = "asc";
  }
  if (direction) {
    sortState[tabId] = { column, direction };
  } else {
    delete sortState[tabId];
  }
  refreshCurrentTab();
};

function refreshCurrentTab() {
  let data = filterData(currentTab);
  data = sortData(currentTab, data);
  renderTable(currentTab, data);
}

// ===== Render Content Panel =====
function renderContentPanel(tabId) {
  const meta = TAB_META.find(c => c.tab_id === tabId);
  if (!meta) return;

  const industries = meta.tab_id === "company" ? getIndustries(tabId) : [];

  let html = '';
  TAB_META.forEach(m => {
    const isActive = m.tab_id === tabId;
    const info = API_DATA[m.tab_id];
    html += '<div class="content-panel' + (isActive ? ' active' : '') + '" id="panel-' + m.tab_id + '">';

    // Panel header
    html += '<div class="panel-header">' +
      '<div class="panel-icon" style="border-color:' + m.color + '30;">' + m.icon + '</div>' +
      '<div><div class="panel-title">' + escapeHtml(m.title) + '</div>' +
      '<div class="panel-subtitle">' + escapeHtml(m.desc) + '</div></div>' +
      '</div>';

    // Toolbar
    html += '<div class="toolbar">' +
      '<input type="text" class="search-box" id="search-' + m.tab_id + '" placeholder="搜尋關鍵字... (如 2330、台積電)" value="">';

    if (m.tab_id === "company" && industries.length > 0) {
      html += '<select class="industry-select" id="industry-' + m.tab_id + '">' +
        '<option value="all">全部產業別</option>';
      industries.forEach(ind => {
        html += '<option value="' + escapeHtml(ind) + '">' + escapeHtml(ind) + '</option>';
      });
      html += '</select>';
    }

    html += '</div>';
    html += '<div class="result-count" id="count-' + m.tab_id + '"></div>';
    html += '<div id="table-' + m.tab_id + '"></div>';
    html += '</div>';
  });

  mainContent.innerHTML = html;

  // Bind events for active tab only (others are hidden)
  const activeSearch = document.getElementById("search-" + tabId);
  if (activeSearch) {
    activeSearch.addEventListener("input", (e) => {
      searchText = e.target.value;
      refreshCurrentTab();
    });
  }

  if (tabId === "company") {
    const industrySelect = document.getElementById("industry-" + tabId);
    if (industrySelect) {
      industrySelect.addEventListener("change", (e) => {
        industryFilter = e.target.value;
        refreshCurrentTab();
      });
    }
  }

  refreshCurrentTab();
}

// ===== Init =====
renderTabCards();
renderContentPanel("mi_index");
</script>
</body>
</html>"""


def generate_html(all_data):
    total_endpoints = len(all_data)
    total_records = sum(v["count"] for v in all_data.values())
    error_count = sum(1 for v in all_data.values() if v["has_error"])

    data_json = json.dumps(all_data, ensure_ascii=False, default=str)
    tab_meta_json = json.dumps([{k: v for k, v in ep.items() if k in ("tab_id", "title", "icon", "color", "desc")} for ep in ENDPOINTS], ensure_ascii=False)

    html = HTML_TEMPLATE
    html = html.replace("{{TOTAL_ENDPOINTS}}", str(total_endpoints))
    html = html.replace("{{TOTAL_RECORDS}}", f"{total_records:,}")
    html = html.replace("{{CATEGORY_COUNT}}", str(len(set(v["category"] for v in all_data.values()))))
    html = html.replace("{{ERROR_COUNT}}", str(error_count))
    html = html.replace("{{ERROR_COLOR}}", 'var(--danger)' if error_count > 0 else 'var(--success)')
    html = html.replace("{{DATA_JSON}}", data_json)
    html = html.replace("{{TAB_META_JSON}}", tab_meta_json)
    return html


def main():
    public_dir = Path("public")
    public_dir.mkdir(exist_ok=True)
    print("開始抓取 TWSE OpenAPI 資料...")
    all_data = fetch_all()
    print("生成靜態網站...")
    html = generate_html(all_data)
    index_path = public_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    data_path = public_dir / "data.json"
    data_path.write_text(json.dumps(all_data, ensure_ascii=False, indent=2), encoding="utf-8")
    total_records = sum(v["count"] for v in all_data.values())
    error_count = sum(1 for v in all_data.values() if v["has_error"])
    print(f"完成！總記錄數: {total_records:,}，異常端點: {error_count}")
    print(f"index.html 大小: {len(html) / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
