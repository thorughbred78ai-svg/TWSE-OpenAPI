#!/usr/bin/env python3
"""
TWSE OpenAPI Dashboard Builder
上市個股及大盤統計資訊儀表板
"""

import json
import urllib.request
from pathlib import Path

# ===== 保留的6個核心端點 =====
ENDPOINTS = [
    {"id": "exchangeReport/MI_INDEX", "tab_id": "mi_index", "title": "大盤統計資訊", "category": "大盤"},
    {"id": "exchangeReport/STOCK_DAY_ALL", "tab_id": "stock_day", "title": "上市個股日成交資訊", "category": "個股成交"},
    {"id": "exchangeReport/BWIBBU_ALL", "tab_id": "bwibbu", "title": "上市個股本益比殖利率", "category": "本益比"},
    {"id": "opendata/t187ap05_L", "tab_id": "revenue", "title": "上市公司每月營業收入", "category": "營收"},
    {"id": "opendata/t187ap45_L", "tab_id": "dividend", "title": "上市公司股利分派情形", "category": "股利"},
    {"id": "opendata/t187ap03_L", "tab_id": "company", "title": "上市公司基本資料", "category": "公司資料"},
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
  --bg: #0f172a;
  --surface: #1e293b;
  --surface-2: #334155;
  --ink: #f8fafc;
  --muted: #94a3b8;
  --accent: #38bdf8;
  --accent-2: #818cf8;
  --success: #34d399;
  --danger: #f87171;
  --line: rgba(148,163,184,0.15);
  --radius: 10px;
  --shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
  --shadow-lg: 0 20px 25px -5px rgba(0,0,0,0.4);
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
  padding: 1.2rem 1.5rem;
  position: sticky;
  top: 0;
  z-index: 100;
}
.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}
.header-left h1 {
  font-size: clamp(1.2rem, 2.5vw, 1.7rem);
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.header-left p {
  color: var(--muted);
  font-size: 0.85rem;
  margin-top: 0.2rem;
}
.header-right {
  display: flex;
  gap: 1.2rem;
  flex-wrap: wrap;
}
.stat-item {
  text-align: center;
}
.stat-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--accent);
  font-family: "JetBrains Mono", monospace;
  display: block;
  line-height: 1.2;
}
.stat-label {
  font-size: 0.7rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.main-tabs {
  max-width: 1200px;
  margin: 1.5rem auto 0;
  padding: 0 1.5rem;
  display: flex;
  gap: 0.3rem;
  flex-wrap: wrap;
  border-bottom: 1px solid var(--line);
  padding-bottom: 0.5rem;
}
.main-tab-btn {
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
  font-family: inherit;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius) var(--radius) 0 0;
  color: var(--muted);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  top: 1px;
}
.main-tab-btn:hover { color: var(--ink); }
.main-tab-btn.active {
  background: var(--surface-2);
  color: var(--accent);
  border-bottom-color: var(--surface-2);
}
.main-tab-panel { display: none; }
.main-tab-panel.active { display: block; }
.main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 1.5rem 3rem;
}
.toolbar {
  display: flex;
  gap: 0.8rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  align-items: center;
}
.search-box {
  flex: 1;
  min-width: 200px;
  padding: 0.6rem 1rem;
  font-size: 0.9rem;
  font-family: inherit;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  color: var(--ink);
  outline: none;
}
.search-box:focus { border-color: var(--accent); }
.search-box::placeholder { color: var(--muted); }
.industry-select {
  padding: 0.6rem 1rem;
  font-size: 0.9rem;
  font-family: inherit;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  color: var(--ink);
  outline: none;
  cursor: pointer;
  min-width: 140px;
}
.industry-select:focus { border-color: var(--accent); }
.result-count {
  font-size: 0.8rem;
  color: var(--accent);
  font-weight: 500;
  margin-bottom: 0.8rem;
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
  font-size: 0.82rem;
}
.data-table th {
  background: var(--surface-2);
  padding: 0.6rem 0.7rem;
  text-align: left;
  font-weight: 500;
  color: var(--accent);
  white-space: nowrap;
  position: sticky;
  top: 0;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}
.data-table th:hover { background: #475569; }
.data-table th .sort-indicator {
  display: inline-block;
  margin-left: 0.3rem;
  color: var(--muted);
  font-size: 0.7rem;
  width: 1em;
}
.data-table th.sort-asc .sort-indicator::after { content: "▲"; color: var(--accent); }
.data-table th.sort-desc .sort-indicator::after { content: "▼"; color: var(--accent); }
.data-table td {
  padding: 0.5rem 0.7rem;
  border-bottom: 1px solid var(--line);
  color: var(--ink);
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.data-table tr:hover td { background: rgba(56,189,248,0.05); }
.data-table tr:last-child td { border-bottom: none; }
.no-data { text-align: center; padding: 3rem; color: var(--muted); }
.no-data-icon { font-size: 2.5rem; margin-bottom: 0.8rem; }
mark {
  background: rgba(56,189,248,0.3);
  color: var(--accent);
  border-radius: 3px;
  padding: 1px 3px;
}
.error-box {
  background: rgba(248,113,113,0.1);
  border: 1px solid rgba(248,113,113,0.3);
  border-radius: var(--radius);
  padding: 1.5rem;
  color: var(--danger);
}
.error-url { font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem; word-break: break-all; }
.footer {
  text-align: center;
  padding: 2rem;
  color: var(--muted);
  font-size: 0.8rem;
  border-top: 1px solid var(--line);
  margin-top: 2rem;
}
.footer a { color: var(--accent); text-decoration: none; }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--surface-2); border-radius: 4px; }
@media (max-width: 640px) {
  .header-inner { flex-direction: column; align-items: flex-start; }
  .header-right { width: 100%; justify-content: space-between; }
  .main-tabs { padding: 0 1rem; }
  .main { padding: 1rem 1rem 3rem; }
  .toolbar { flex-direction: column; align-items: stretch; }
  .search-box, .industry-select { width: 100%; }
}
</style>
</head>
<body>
<header class="header">
  <div class="header-inner">
    <div class="header-left">
      <h1>TWSE OpenAPI 資料儀表板</h1>
      <p>TWSE 上市個股及大盤統計資訊 · 每日自動更新</p>
    </div>
    <div class="header-right">
      <div class="stat-item"><span class="stat-value">{{TOTAL_ENDPOINTS}}</span><span class="stat-label">API 端點</span></div>
      <div class="stat-item"><span class="stat-value">{{TOTAL_RECORDS}}</span><span class="stat-label">總記錄數</span></div>
      <div class="stat-item"><span class="stat-value">{{CATEGORY_COUNT}}</span><span class="stat-label">資料類別</span></div>
      <div class="stat-item"><span class="stat-value" style="color:{{ERROR_COLOR}};">{{ERROR_COUNT}}</span><span class="stat-label">異常端點</span></div>
    </div>
  </div>
</header>
<div class="main-tabs" id="mainTabs"></div>
<main class="main" id="mainContent"></main>
<footer class="footer">
  <p>資料來源: <a href="https://openapi.twse.com.tw/" target="_blank">臺灣證券交易所 OpenAPI</a> · 本頁面由 GitHub Actions 自動生成</p>
</footer>
<script>
const API_DATA = {{DATA_JSON}};

const TAB_CONFIG = [
  { tab_id: "mi_index", title: "大盤統計資訊", hasIndustry: false },
  { tab_id: "stock_day", title: "上市個股日成交資訊", hasIndustry: false },
  { tab_id: "bwibbu", title: "上市個股本益比殖利率", hasIndustry: false },
  { tab_id: "revenue", title: "上市公司每月營業收入", hasIndustry: false },
  { tab_id: "dividend", title: "上市公司股利分派情形", hasIndustry: false },
  { tab_id: "company", title: "上市公司基本資料", hasIndustry: true },
];

let currentTab = "mi_index";
let searchText = "";
let sortState = {}; // { tab_id: { column, direction } }
let industryFilter = "all";

const mainTabs = document.getElementById("mainTabs");
const mainContent = document.getElementById("mainContent");

// ===== 初始化頁籤 =====
function initTabs() {
  TAB_CONFIG.forEach(cfg => {
    const btn = document.createElement("button");
    btn.className = "main-tab-btn";
    btn.textContent = cfg.title;
    btn.dataset.tab = cfg.tab_id;
    btn.addEventListener("click", () => switchTab(cfg.tab_id));
    mainTabs.appendChild(btn);
  });
}

function switchTab(tabId) {
  currentTab = tabId;
  searchText = "";
  industryFilter = "all";
  document.querySelectorAll(".main-tab-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.tab === tabId);
  });
  renderTab(tabId);
}

// ===== 數值解析（用於排序） =====
function parseNumeric(val) {
  if (val == null) return null;
  const s = String(val).replace(/,/g, "").trim();
  // 處理百分比如 "1.23%"
  if (s.endsWith("%")) {
    const n = parseFloat(s.slice(0, -1));
    return isNaN(n) ? null : n;
  }
  // 處理純數字
  const n = parseFloat(s);
  return isNaN(n) ? null : n;
}

// ===== 高亮文字 =====
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

// ===== 取得產業別列表 =====
function getIndustries(tabId) {
  const info = API_DATA[tabId];
  if (!info || !Array.isArray(info.data)) return [];
  const set = new Set();
  info.data.forEach(row => {
    if (row["產業別"]) set.add(row["產業別"]);
  });
  return Array.from(set).sort();
}

// ===== 排序資料 =====
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

// ===== 篩選資料 =====
function filterData(tabId) {
  const info = API_DATA[tabId];
  if (!info || !Array.isArray(info.data)) return [];
  let data = info.data;

  // 產業別篩選（僅 company 頁籤）
  if (tabId === "company" && industryFilter !== "all") {
    data = data.filter(row => row["產業別"] === industryFilter);
  }

  // 關鍵字搜尋
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

// ===== 渲染表格 =====
function renderTable(tabId, data) {
  const container = document.getElementById("table-" + tabId);
  const countEl = document.getElementById("count-" + tabId);
  const info = API_DATA[tabId];

  if (!container) return;

  if (info && info.has_error) {
    let html = '<div class="error-box"><div style="font-size:1.2rem;margin-bottom:0.5rem;">⚠️ 資料抓取失敗</div>';
    html += '<pre style="margin:0;white-space:pre-wrap;word-break:break-all;font-size:0.8rem;">' + escapeHtml(JSON.stringify(info.data, null, 2)) + '</pre>';
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
    let indicator = '<span class="sort-indicator"></span>';
    if (state && state.column === col) {
      sortClass = state.direction === "asc" ? "sort-asc" : "sort-desc";
    }
    html += '<th class="' + sortClass + '" data-col="' + escapeHtml(col) + '" onclick="handleSort(\\'' + tabId + '\\', \\' + escapeHtml(col) + '\\')">' + escapeHtml(col) + indicator + '</th>';
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
    html += '<tr><td colspan="' + columns.length + '" style="text-align:center;color:var(--muted);padding:1rem;">... 還有 ' + (data.length - 300) + ' 資料，請使用搜尋縮小範圍</td></tr>';
  }

  html += '</tbody></table></div>';
  container.innerHTML = html;
  if (countEl) {
    const total = info && Array.isArray(info.data) ? info.data.length : 0;
    countEl.textContent = '顯示 ' + data.length.toLocaleString() + ' / ' + total.toLocaleString() + ' 筆資料';
  }
}

// 用於 onclick 的輔助函數需要掛在 window 上
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

// ===== 渲染頁籤內容 =====
function renderTab(tabId) {
  const cfg = TAB_CONFIG.find(c => c.tab_id === tabId);
  if (!cfg) return;

  // 建立頁籤內容結構
  let html = '<div class="main-tab-panel active" id="panel-' + tabId + '">';
  html += '<div class="toolbar">';
  html += '<input type="text" class="search-box" id="search-' + tabId + '" placeholder="搜尋關鍵字... (如 2330、台積電)" value="' + escapeHtml(searchText) + '">';

  // 產業別下拉選單（僅 company 頁籤）
  if (cfg.hasIndustry) {
    const industries = getIndustries(tabId);
    html += '<select class="industry-select" id="industry-' + tabId + '">';
    html += '<option value="all">全部產業別</option>';
    industries.forEach(ind => {
      html += '<option value="' + escapeHtml(ind) + '">' + escapeHtml(ind) + '</option>';
    });
    html += '</select>';
  }

  html += '</div>';
  html += '<div class="result-count" id="count-' + tabId + '"></div>';
  html += '<div id="table-' + tabId + '"></div>';
  html += '</div>';
  mainContent.innerHTML = html;

  // 綁定搜尋事件
  const searchBox = document.getElementById("search-" + tabId);
  if (searchBox) {
    searchBox.addEventListener("input", (e) => {
      searchText = e.target.value;
      refreshCurrentTab();
    });
  }

  // 綁定產業別事件
  if (cfg.hasIndustry) {
    const industrySelect = document.getElementById("industry-" + tabId);
    if (industrySelect) {
      industrySelect.addEventListener("change", (e) => {
        industryFilter = e.target.value;
        refreshCurrentTab();
      });
    }
  }

  // 初始渲染
  refreshCurrentTab();
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// ===== 啟動 =====
initTabs();
switchTab("mi_index");
</script>
</body>
</html>"""


def generate_html(all_data):
    total_endpoints = len(all_data)
    total_records = sum(v["count"] for v in all_data.values())
    error_count = sum(1 for v in all_data.values() if v["has_error"])

    data_json = json.dumps(all_data, ensure_ascii=False, default=str)

    html = HTML_TEMPLATE
    html = html.replace("{{TOTAL_ENDPOINTS}}", str(total_endpoints))
    html = html.replace("{{TOTAL_RECORDS}}", f"{total_records:,}")
    html = html.replace("{{CATEGORY_COUNT}}", str(len(set(v["category"] for v in all_data.values()))))
    html = html.replace("{{ERROR_COUNT}}", str(error_count))
    html = html.replace("{{ERROR_COLOR}}", 'var(--danger)' if error_count > 0 else 'var(--success)')
    html = html.replace("{{DATA_JSON}}", data_json)
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
