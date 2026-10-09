#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TWSE 上市個股及大盤統計資訊儀表板
修正版：修正 JavaScript 排序事件、產生 SVG 網站圖示。
"""

import json
import urllib.request
import urllib.error
from pathlib import Path


# ============================================================
# TWSE OpenAPI 端點設定
# ============================================================

ENDPOINTS = [
    {
        "id": "exchangeReport/MI_INDEX",
        "tab_id": "mi_index",
        "title": "大盤統計資訊",
        "icon": "📊",
        "color": "#38bdf8",
        "desc": "每日大盤成交統計、漲跌家數",
        "category": "大盤",
    },
    {
        "id": "exchangeReport/STOCK_DAY_ALL",
        "tab_id": "stock_day",
        "title": "上市個股日成交資訊",
        "icon": "📈",
        "color": "#34d399",
        "desc": "全部上市股票當日開高低收、成交量、成交金額",
        "category": "成交",
    },
    {
        "id": "exchangeReport/BWIBBU_ALL",
        "tab_id": "bwibbu",
        "title": "上市個股本益比殖利率",
        "icon": "💰",
        "color": "#fbbf24",
        "desc": "本益比、殖利率、股價淨值比",
        "category": "估值",
    },
    {
        "id": "opendata/t187ap05_L",
        "tab_id": "revenue",
        "title": "上市公司每月營業收入",
        "icon": "📋",
        "color": "#a78bfa",
        "desc": "當月營收、上月營收、去年同月、增減百分比",
        "category": "財務",
    },
    {
        "id": "opendata/t187ap45_L",
        "tab_id": "dividend",
        "title": "上市公司股利分派情形",
        "icon": "🎁",
        "color": "#f472b6",
        "desc": "現金股利、股票股利、除權息日期",
        "category": "股利",
    },
    {
        "id": "opendata/t187ap03_L",
        "tab_id": "company",
        "title": "上市公司基本資料",
        "icon": "🏢",
        "color": "#fb923c",
        "desc": "公司全名、產業別、資本額、成立日期",
        "category": "公司資料",
    },
]

BASE_URL = "https://openapi.twse.com.tw/v1"


# ============================================================
# 抓取 API 資料
# ============================================================

def fetch_data(endpoint_id):
    """取得指定 TWSE API 資料，並處理常見錯誤。"""
    url = f"{BASE_URL}/{endpoint_id}"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "TWSE-Dashboard/1.0"},
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8")

        if not content.strip():
            return {
                "error": "API 回傳空內容",
                "url": url,
            }

        return json.loads(content)

    except urllib.error.HTTPError as exc:
        return {
            "error": f"HTTP {exc.code}: {exc.reason}",
            "url": url,
        }

    except urllib.error.URLError as exc:
        return {
            "error": f"URL Error: {exc.reason}",
            "url": url,
        }

    except json.JSONDecodeError as exc:
        return {
            "error": f"JSON 解析失敗: {exc}",
            "url": url,
        }

    except Exception as exc:
        return {
            "error": str(exc),
            "url": url,
        }


def fetch_all():
    """抓取所有端點並整理結果。"""
    result = {}

    for endpoint in ENDPOINTS:
        print(f"  抓取: {endpoint['id']}")

        data = fetch_data(endpoint["id"])

        result[endpoint["tab_id"]] = {
            **endpoint,
            "data": data,
            "count": len(data) if isinstance(data, list) else 0,
            "has_error": (
                isinstance(data, dict) and "error" in data
            ),
        }

    return result


# ============================================================
# HTML、CSS、JavaScript
# ============================================================

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TWSE 上市個股及大盤統計資訊</title>
<link rel="icon" href="./favicon.svg" type="image/svg+xml">
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
  --line: rgba(148,163,184,.12);
  --radius: 14px;
  --shadow: 0 4px 6px -1px rgba(0,0,0,.4);
  --shadow-lg: 0 20px 25px -5px rgba(0,0,0,.5);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: "Noto Sans TC", "PingFang TC",
    "Microsoft JhengHei", sans-serif;
  background: var(--bg);
  color: var(--ink);
  line-height: 1.6;
  min-height: 100vh;
}

.header {
  background: linear-gradient(
    135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%
  );
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
  background: rgba(56,189,248,.15);
  color: var(--accent);
  font-size: .7rem;
  padding: .25rem .7rem;
  border-radius: 20px;
  margin-bottom: .5rem;
  font-weight: 500;
  letter-spacing: .05em;
}

.header-left h1 {
  font-size: clamp(1.3rem, 2.5vw, 1.8rem);
  font-weight: 700;
  background: linear-gradient(
    135deg, #38bdf8, #818cf8, #c084fc
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: .3rem;
}

.header-left p {
  color: var(--muted);
  font-size: .85rem;
}

.header-right {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.stat-item {
  text-align: center;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: .8rem 1.2rem;
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
  font-size: .65rem;
  color: var(--muted);
  letter-spacing: .08em;
  margin-top: .2rem;
}

.tab-section {
  max-width: 1200px;
  margin: 2rem auto 1.5rem;
  padding: 0 1.5rem;
}

.tab-section-title {
  font-size: .75rem;
  color: var(--muted);
  letter-spacing: .1em;
  margin-bottom: 1rem;
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
  transition: all .25s;
  position: relative;
  overflow: hidden;
}

.tab-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--card-color);
  opacity: 0;
}

.tab-card:hover,
.tab-card.active {
  border-color: var(--card-color);
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.tab-card:hover::before,
.tab-card.active::before {
  opacity: 1;
}

.tab-card.active {
  background: var(--surface-2);
}

.tab-icon {
  font-size: 2.2rem;
  margin-bottom: .6rem;
  display: block;
}

.tab-title {
  font-size: .85rem;
  font-weight: 600;
  margin-bottom: .3rem;
}

.tab-desc {
  font-size: .7rem;
  color: var(--muted);
  line-height: 1.4;
}

.tab-count {
  position: absolute;
  top: .6rem;
  right: .6rem;
  font-size: .65rem;
  font-family: "JetBrains Mono", monospace;
  background: var(--surface-3);
  color: var(--muted);
  padding: .15rem .4rem;
  border-radius: 8px;
}

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
  gap: .8rem;
  margin-bottom: 1.2rem;
  padding-bottom: .8rem;
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
  font-size: .8rem;
  color: var(--muted);
}

.toolbar {
  display: flex;
  gap: .8rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  align-items: center;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: .8rem 1rem;
}

.search-box,
.industry-select {
  padding: .6rem 1rem;
  font-size: .9rem;
  font-family: inherit;
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: 10px;
  color: var(--ink);
  outline: none;
}

.search-box {
  flex: 1;
  min-width: 200px;
}

.search-box:focus,
.industry-select:focus {
  border-color: var(--accent);
}

.search-box::placeholder {
  color: var(--muted);
}

.industry-select {
  min-width: 150px;
  cursor: pointer;
}

.result-count {
  font-size: .8rem;
  color: var(--accent);
  margin-bottom: .8rem;
  min-height: 1.2em;
}

.data-table-wrap {
  overflow-x: auto;
  border-radius: var(--radius);
  border: 1px solid var(--line);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: .82rem;
}

.data-table th {
  background: var(--surface-2);
  padding: .65rem .75rem;
  text-align: left;
  font-weight: 500;
  color: var(--accent);
  white-space: nowrap;
  position: sticky;
  top: 0;
  cursor: pointer;
  user-select: none;
  border-bottom: 2px solid var(--line);
}

.data-table th:hover {
  background: var(--surface-3);
}

.data-table th .sort-indicator {
  display: inline-block;
  margin-left: .3rem;
  color: var(--muted);
  font-size: .65rem;
  width: 1em;
}

.data-table th.sort-asc .sort-indicator::after {
  content: "▲";
  color: var(--accent);
}

.data-table th.sort-desc .sort-indicator::after {
  content: "▼";
  color: var(--accent);
}

.data-table td {
  padding: .55rem .75rem;
  border-bottom: 1px solid var(--line);
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.data-table tbody tr:hover td {
  background: rgba(56,189,248,.06);
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.no-data {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--muted);
}

.no-data-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

mark {
  background: rgba(56,189,248,.25);
  color: #7dd3fc;
  border-radius: 3px;
  padding: 1px 3px;
}

.error-box {
  background: rgba(248,113,113,.08);
  border: 1px solid rgba(248,113,113,.25);
  border-radius: var(--radius);
  padding: 2rem;
}

.error-url {
  font-size: .75rem;
  color: var(--muted);
  margin-top: .5rem;
  word-break: break-all;
}

.footer {
  text-align: center;
  padding: 2rem;
  color: var(--muted);
  font-size: .8rem;
  border-top: 1px solid var(--line);
  margin-top: 2rem;
}

.footer a {
  color: var(--accent);
  text-decoration: none;
}

.footer a:hover {
  text-decoration: underline;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg);
}

::-webkit-scrollbar-thumb {
  background: var(--surface-3);
  border-radius: 4px;
}

@media (max-width: 768px) {
  .header-inner {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-right {
    width: 100%;
    justify-content: space-between;
  }

  .tab-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .main {
    padding: 0 1rem 3rem;
  }

  .tab-section {
    padding: 0 1rem;
  }

  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-box,
  .industry-select {
    width: 100%;
  }
}

@media (max-width: 400px) {
  .tab-grid {
    grid-template-columns: 1fr;
  }

  .stat-item {
    min-width: 70px;
    padding: .6rem .8rem;
  }

  .stat-value {
    font-size: 1.2rem;
  }
}
</style>
</head>

<body>

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
        <span class="stat-value" style="color:{{ERROR_COLOR}};">
          {{ERROR_COUNT}}
        </span>
        <div class="stat-label">異常端點</div>
      </div>
    </div>
  </div>
</header>

<div class="tab-section">
  <div class="tab-section-title">資料類別</div>
  <div class="tab-grid" id="tabGrid"></div>
</div>

<main class="main" id="mainContent"></main>

<footer class="footer">
  <p>
    資料來源：
    <a href="https://openapi.twse.com.tw/" target="_blank"
       rel="noopener noreferrer">臺灣證券交易所 OpenAPI</a>
    · 本頁面由 GitHub Actions 自動生成
  </p>
</footer>

<script>
"use strict";

const API_DATA = {{DATA_JSON}};
const TAB_META = {{TAB_META_JSON}};

let currentTab = "mi_index";
let searchText = "";
let sortState = {};
let industryFilter = "all";

const tabGrid = document.getElementById("tabGrid");
const mainContent = document.getElementById("mainContent");


// ============================================================
// 通用輔助函式
// ============================================================

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value == null ? "" : String(value);
  return div.innerHTML;
}


function parseNumeric(value) {
  if (value == null) return null;

  const s = String(value).replace(/,/g, "").trim();

  if (!s) return null;

  const normalized = s.endsWith("%")
    ? s.slice(0, -1)
    : s;

  const number = Number(normalized);

  return Number.isFinite(number) ? number : null;
}


function highlightText(text, query) {
  const str = String(text == null ? "" : text);

  if (!query) {
    return escapeHtml(str);
  }

  const lowerStr = str.toLowerCase();
  const lowerQuery = query.toLowerCase();

  let result = "";
  let lastIndex = 0;
  let index = lowerStr.indexOf(lowerQuery);

  while (index !== -1) {
    result += escapeHtml(str.slice(lastIndex, index));

    result += "<mark>" +
      escapeHtml(str.slice(index, index + query.length)) +
      "</mark>";

    lastIndex = index + query.length;

    index = lowerStr.indexOf(lowerQuery, lastIndex);
  }

  result += escapeHtml(str.slice(lastIndex));

  return result;
}


// ============================================================
// 分類卡片
// ============================================================

function renderTabCards() {
  tabGrid.innerHTML = "";

  TAB_META.forEach(meta => {
    const info = API_DATA[meta.tab_id];
    const count = info ? info.count : 0;
    const isActive = meta.tab_id === currentTab;

    const card = document.createElement("div");

    card.className =
      "tab-card" + (isActive ? " active" : "");

    card.style.setProperty("--card-color", meta.color);

    card.innerHTML =
      '<span class="tab-count">' +
      count.toLocaleString() +
      '</span>' +

      '<span class="tab-icon">' +
      escapeHtml(meta.icon) +
      '</span>' +

      '<div class="tab-title">' +
      escapeHtml(meta.title) +
      '</div>' +

      '<div class="tab-desc">' +
      escapeHtml(meta.desc) +
      '</div>';

    card.addEventListener("click", () => {
      switchTab(meta.tab_id);
    });

    tabGrid.appendChild(card);
  });
}


// ============================================================
// 切換分類
// ============================================================

function switchTab(tabId) {
  currentTab = tabId;
  searchText = "";
  industryFilter = "all";

  renderTabCards();
  renderContentPanel(tabId);
}


// ============================================================
// 取得產業分類
// ============================================================

function getIndustries(tabId) {
  const info = API_DATA[tabId];

  if (!info || !Array.isArray(info.data)) {
    return [];
  }

  const industries = new Set();

  info.data.forEach(row => {
    if (row["產業別"]) {
      industries.add(row["產業別"]);
    }
  });

  return Array.from(industries).sort();
}


// 將各 API 的股票代號欄位統一化，並建立上市公司代號→產業別對照。
function getStockCode(row) {
  if (!row || typeof row !== "object") return "";
  const keys = ["公司代號", "證券代號", "有價證券代號", "股票代號", "Code", "code"];
  for (const key of keys) {
    if (row[key] != null && String(row[key]).trim()) {
      return String(row[key]).trim().replace(/\.0$/, "");
    }
  }
  return "";
}

function getCompanyIndustryMap() {
  const info = API_DATA.company;
  const map = new Map();
  if (!info || !Array.isArray(info.data)) return map;
  info.data.forEach(row => {
    const code = getStockCode(row);
    if (code && row["產業別"]) map.set(code, row["產業別"]);
  });
  return map;
}

function getIndustryForRow(row, tabId) {
  // 若資料本身已帶產業別，優先採用；否則依股票代號對照基本資料。
  if (row && row["產業別"]) return row["產業別"];
  const code = getStockCode(row);
  return code ? getCompanyIndustryMap().get(code) || "" : "";
}


// ============================================================
// 資料排序
// ============================================================

function sortData(tabId, data) {
  const state = sortState[tabId];

  if (!state || !state.direction) {
    return data;
  }

  const column = state.column;
  const direction = state.direction;

  return [...data].sort((a, b) => {
    const numberA = parseNumeric(a[column]);
    const numberB = parseNumeric(b[column]);

    if (numberA !== null && numberB !== null) {
      return direction === "asc"
        ? numberA - numberB
        : numberB - numberA;
    }

    const valueA = String(
      a[column] == null ? "" : a[column]
    ).toLowerCase();

    const valueB = String(
      b[column] == null ? "" : b[column]
    ).toLowerCase();

    if (valueA < valueB) {
      return direction === "asc" ? -1 : 1;
    }

    if (valueA > valueB) {
      return direction === "asc" ? 1 : -1;
    }

    return 0;
  });
}


// ============================================================
// 搜尋與篩選
// ============================================================

function filterData(tabId) {
  const info = API_DATA[tabId];

  if (!info || !Array.isArray(info.data)) {
    return [];
  }

  let data = info.data;

  // 產業別篩選：基本資料直接比對產業別；其他個股資料
  // 透過上市公司基本資料中的公司代號對應產業別。
  if (industryFilter !== "all") {
    if (tabId === "company") {
      data = data.filter(row => row["產業別"] === industryFilter);
    } else if (["stock_day", "bwibbu", "revenue", "dividend"].includes(tabId)) {
      data = data.filter(row => getIndustryForRow(row, tabId) === industryFilter);
    }
  }

  if (searchText.trim()) {
    const query = searchText.toLowerCase().trim();

    data = data.filter(row => {
      return Object.values(row).some(value => {
        if (value == null) return false;

        return String(value)
          .toLowerCase()
          .includes(query);
      });
    });
  }

  return data;
}


// ============================================================
// 渲染表格
// ============================================================

function renderTable(tabId, data) {
  const container = document.getElementById(
    "table-" + tabId
  );

  const countEl = document.getElementById(
    "count-" + tabId
  );

  const info = API_DATA[tabId];

  if (!container) return;

  // API 錯誤
  if (info && info.has_error) {
    let html =
      '<div class="error-box">' +
      '<div style="font-size:1.3rem;margin-bottom:.5rem;">' +
      '⚠️ 資料抓取失敗' +
      '</div>' +

      '<pre style="margin:0;white-space:pre-wrap;' +
      'word-break:break-all;font-size:.8rem;' +
      'color:var(--muted);">' +

      escapeHtml(
        JSON.stringify(info.data, null, 2)
      ) +

      '</pre>';

    if (info.data && info.data.url) {
      html +=
        '<div class="error-url">請求 URL: ' +
        escapeHtml(info.data.url) +
        '</div>';
    }

    html += '</div>';

    container.innerHTML = html;

    if (countEl) {
      countEl.textContent = "";
    }

    return;
  }

  // 沒有資料
  if (!data || data.length === 0) {
    container.innerHTML =
      '<div class="no-data">' +
      '<div class="no-data-icon">🔍</div>' +
      '<p>沒有符合條件的資料</p>' +
      '</div>';

    if (countEl) {
      countEl.textContent = "0 筆資料";
    }

    return;
  }

  const columns = Object.keys(data[0]);
  const state = sortState[tabId];

  let html =
    '<div class="data-table-wrap">' +
    '<table class="data-table">' +
    '<thead><tr>';

  columns.forEach(column => {
    let sortClass = "";

    if (state && state.column === column) {
      sortClass =
        state.direction === "asc"
          ? "sort-asc"
          : "sort-desc";
    }

    // 修正：不再於 onclick 中拼接多層跳脫引號。
    // 排序事件會在表格建立後使用 addEventListener 綁定。
    html +=
      '<th class="' + sortClass + '">' +
      '<span style="cursor:pointer;">' +
      escapeHtml(column) +
      '<span class="sort-indicator"></span>' +
      '</span></th>';
  });

  html += '</tr></thead><tbody>';

  // 最多顯示 300 筆，避免大量資料影響效能。
  data.slice(0, 300).forEach(row => {
    html += '<tr>';

    columns.forEach(column => {
      const value = row[column];
      const display = value == null ? "" : String(value);
      const cell = highlightText(display, searchText);

      html +=
        '<td title="' + escapeHtml(display) + '">' +
        cell +
        '</td>';
    });

    html += '</tr>';
  });

  if (data.length > 300) {
    html +=
      '<tr><td colspan="' + columns.length + '"' +
      ' style="text-align:center;color:var(--muted);' +
      'padding:1rem;">' +
      '... 還有 ' +
      (data.length - 300).toLocaleString() +
      ' 筆資料，請使用搜尋縮小範圍' +
      '</td></tr>';
  }

  html += '</tbody></table></div>';

  container.innerHTML = html;

  // 修正重點：以 DOM 事件處理排序，避免無效跳脫字元。
  container.querySelectorAll("thead th").forEach(
    (th, index) => {
      th.addEventListener("click", () => {
        window.handleSort(tabId, columns[index]);
      });
    }
  );

  if (countEl) {
    const total =
      info && Array.isArray(info.data)
        ? info.data.length
        : 0;

    countEl.textContent =
      "顯示 " +
      data.length.toLocaleString() +
      " / " +
      total.toLocaleString() +
      " 筆資料";
  }
}


// ============================================================
// 排序事件處理
// ============================================================

window.handleSort = function(tabId, column) {
  const state = sortState[tabId] || {
    column: null,
    direction: null,
  };

  let direction = "asc";

  if (state.column === column) {
    if (state.direction === "asc") {
      direction = "desc";
    } else if (state.direction === "desc") {
      direction = null;
    } else {
      direction = "asc";
    }
  }

  if (direction) {
    sortState[tabId] = {
      column,
      direction,
    };
  } else {
    delete sortState[tabId];
  }

  refreshCurrentTab();
};


// ============================================================
// 更新目前分類
// ============================================================

function refreshCurrentTab() {
  let data = filterData(currentTab);

  data = sortData(currentTab, data);

  renderTable(currentTab, data);
}


// ============================================================
// 渲染內容面板
// ============================================================

function renderContentPanel(tabId) {
  const meta = TAB_META.find(
    item => item.tab_id === tabId
  );

  if (!meta) return;

  const industries =
    meta.tab_id === "company"
      ? getIndustries(tabId)
      : [];

  let html = "";

  TAB_META.forEach(item => {
    const isActive = item.tab_id === tabId;

    html +=
      '<div class="content-panel' +
      (isActive ? " active" : "") +
      '" id="panel-' + item.tab_id + '">';

    // 標題
    html +=
      '<div class="panel-header">' +

      '<div class="panel-icon" style="border-color:' +
      item.color + '30;">' +
      escapeHtml(item.icon) +
      '</div>' +

      '<div>' +
      '<div class="panel-title">' +
      escapeHtml(item.title) +
      '</div>' +

      '<div class="panel-subtitle">' +
      escapeHtml(item.desc) +
      '</div>' +

      '</div></div>';

    // 搜尋工具列
    html +=
      '<div class="toolbar">' +

      '<input type="text" class="search-box" ' +
      'id="search-' + item.tab_id + '" ' +
      'placeholder="搜尋關鍵字... (如 2330、台積電)" ' +
      'value="">';

    // 產業篩選：公司基本資料及四種個股資訊共用同一份產業清單。
    if (
      ["company", "stock_day", "bwibbu", "revenue", "dividend"].includes(item.tab_id) &&
      getIndustries("company").length > 0
    ) {
      html +=
        '<select class="industry-select" ' +
        'id="industry-' + item.tab_id + '">' +

        '<option value="all">全部產業別</option>';

      getIndustries("company").forEach(industry => {
        html +=
          '<option value="' + escapeHtml(industry) + '">' +
          escapeHtml(industry) +
          '</option>';
      });

      html += '</select>';
    }

    html += '</div>';

    html +=
      '<div class="result-count" id="count-' +
      item.tab_id + '"></div>';

    html +=
      '<div id="table-' + item.tab_id + '"></div>';

    html += '</div>';
  });

  mainContent.innerHTML = html;

  // 綁定目前分類的搜尋事件
  const activeSearch = document.getElementById(
    "search-" + tabId
  );

  if (activeSearch) {
    activeSearch.addEventListener("input", event => {
      searchText = event.target.value;
      refreshCurrentTab();
    });
  }

  // 綁定產業篩選事件
  if (["company", "stock_day", "bwibbu", "revenue", "dividend"].includes(tabId)) {
    const industrySelect = document.getElementById(
      "industry-" + tabId
    );

    if (industrySelect) {
      industrySelect.addEventListener("change", event => {
        industryFilter = event.target.value;
        refreshCurrentTab();
      });
    }
  }

  refreshCurrentTab();
}


// ============================================================
// 初始化
// ============================================================

renderTabCards();
renderContentPanel("mi_index");

</script>
</body>
</html>
"""


# ============================================================
# 產生 HTML
# ============================================================

def generate_html(all_data):
    total_endpoints = len(all_data)

    total_records = sum(
        item["count"] for item in all_data.values()
    )

    error_count = sum(
        1
        for item in all_data.values()
        if item["has_error"]
    )

    data_json = json.dumps(
        all_data,
        ensure_ascii=False,
        default=str,
    )

    tab_meta_json = json.dumps(
        [
            {
                key: value
                for key, value in endpoint.items()
                if key in (
                    "tab_id",
                    "title",
                    "icon",
                    "color",
                    "desc",
                )
            }
            for endpoint in ENDPOINTS
        ],
        ensure_ascii=False,
    )

    html = HTML_TEMPLATE

    replacements = {
        "{{TOTAL_ENDPOINTS}}": str(total_endpoints),
        "{{TOTAL_RECORDS}}": f"{total_records:,}",
        "{{CATEGORY_COUNT}}": str(
            len({
                item["category"]
                for item in all_data.values()
            })
        ),
        "{{ERROR_COUNT}}": str(error_count),
        "{{ERROR_COLOR}}": (
            "var(--danger)"
            if error_count > 0
            else "var(--success)"
        ),
        "{{DATA_JSON}}": data_json,
        "{{TAB_META_JSON}}": tab_meta_json,
    }

    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    return html


# ============================================================
# 產生 SVG 網站圖示
# ============================================================

FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg"
viewBox="0 0 64 64">
<rect width="64" height="64" rx="14" fill="#0b1121"/>
<path d="M10 46h44" stroke="#334155" stroke-width="3"
stroke-linecap="round"/>
<path d="M14 39l12-12 9 7 15-19" fill="none"
stroke="#38bdf8" stroke-width="5"
stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="50" cy="15" r="4" fill="#34d399"/>
</svg>
"""


# ============================================================
# 主程式
# ============================================================

def main():
    public_dir = Path("public")
    public_dir.mkdir(parents=True, exist_ok=True)

    print("開始抓取 TWSE OpenAPI 資料...")

    all_data = fetch_all()

    print("生成靜態網站...")

    html = generate_html(all_data)

    index_path = public_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")

    data_path = public_dir / "data.json"
    data_path.write_text(
        json.dumps(
            all_data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    favicon_path = public_dir / "favicon.svg"
    favicon_path.write_text(
        FAVICON_SVG,
        encoding="utf-8",
    )

    total_records = sum(
        item["count"] for item in all_data.values()
    )

    error_count = sum(
        1
        for item in all_data.values()
        if item["has_error"]
    )

    print()
    print("完成！")
    print(f"總記錄數：{total_records:,}")
    print(f"異常端點：{error_count}")
    print(f"HTML 大小：{len(html) / 1024 / 1024:.2f} MB")
    print(f"HTML 路徑：{index_path}")
    print(f"JSON 路徑：{data_path}")
    print(f"圖示路徑：{favicon_path}")


if __name__ == "__main__":
    main()
