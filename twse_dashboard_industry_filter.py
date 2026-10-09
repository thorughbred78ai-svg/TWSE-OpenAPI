#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TWSE 上市個股及大盤統計資訊儀表板
修正版：修正 JavaScript 排序事件、產生 SVG 網站圖示。
"""

import json
import calendar
import datetime
from html.parser import HTMLParser
import urllib.parse
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
# 近 12 個月歷史趨勢資料
# ============================================================

class _TableParser(HTMLParser):
    """以標準函式庫擷取 MOPS 月營收歷史頁的表格，不增加第三方依賴。"""
    def __init__(self):
        super().__init__()
        self.tables=[]; self.table=None; self.row=None; self.cell=None
    def handle_starttag(self, tag, attrs):
        if tag == "table": self.table=[]
        elif tag == "tr" and self.table is not None: self.row=[]
        elif tag in ("td", "th") and self.row is not None: self.cell=[]
    def handle_data(self, data):
        if self.cell is not None: self.cell.append(data.strip())
    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(" ".join(x for x in self.cell if x)); self.cell=None
        elif tag == "tr" and self.row is not None and self.table is not None:
            if self.row: self.table.append(self.row)
            self.row=None
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table); self.table=None


def _read_url(url, data=None, timeout=12):
    headers={"User-Agent":"Mozilla/5.0 (compatible; TWSE-Dashboard/1.0)","Accept":"application/json,text/html,*/*"}
    req=urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw=resp.read()
    for enc in ("utf-8", "big5", "cp950"):
        try: return raw.decode(enc)
        except UnicodeDecodeError: pass
    return raw.decode("utf-8", errors="replace")


def _parse_number(value):
    try:
        text=str(value).replace(",", "").replace("%", "").replace("—", "").strip()
        if text in ("", "-", "--", "N/A"): return None
        return float(text)
    except (TypeError, ValueError): return None


def fetch_chart_history(all_data, months=12):
    """擷取近 N 個月 MOPS 月營收及 TWSE 月底附近日成交快照，失敗月份略過。"""
    companies_data=all_data.get("company", {}).get("data", [])
    if not isinstance(companies_data, list): companies_data=[]
    code_industry={}
    for row in companies_data:
        code=str(row.get("公司代號", row.get("公司代碼", ""))).strip()
        industry=str(row.get("產業別", "未分類")).strip() or "未分類"
        code_industry[code]=industry
    revenue_by_month=[]; turnover_by_month=[]
    today=datetime.date.today()
    month_cursor=today.replace(day=1)
    month_list=[]
    for offset in range(months-1, -1, -1):
        y=month_cursor.year; m=month_cursor.month-offset
        while m <= 0: y-=1; m+=12
        while m > 12: y+=1; m-=12
        month_list.append((y,m))

    for year, month in month_list:
        label=f"{year}-{month:02d}"
        roc_year=year-1911
        # MOPS 官方歷史月營收彙總頁，_0 為國內公司、_1 為外國企業。
        revenue_totals={}; yoy_values={}
        for suffix in (0,1):
            url=f"https://mopsov.twse.com.tw/nas/t21/sii/t21sc03_{roc_year}_{month}_{suffix}.html"
            try:
                parser=_TableParser(); parser.feed(_read_url(url))
                for table in parser.tables:
                    if not table: continue
                    header_idx=None; headers=[]
                    for ri,row in enumerate(table[:5]):
                        joined="|".join(row)
                        if ("公司代號" in joined or "公司代碼" in joined) and ("當月營收" in joined or "營業收入" in joined):
                            header_idx=ri; headers=[h.replace("\n", "").strip() for h in row]; break
                    if header_idx is None: continue
                    def col_index(words):
                        return next((i for i,h in enumerate(headers) if any(w in h for w in words)), None)
                    code_i=col_index(["公司代號","公司代碼"]); rev_i=col_index(["當月營收","本月營收"]); yoy_i=col_index(["去年同月增減","去年同月增減(%)","年增率"])
                    if code_i is None or rev_i is None: continue
                    for row in table[header_idx+1:]:
                        if len(row)<=max(code_i,rev_i): continue
                        code=row[code_i].strip()
                        if not code.isdigit(): continue
                        industry=code_industry.get(code,"未分類")
                        rev=_parse_number(row[rev_i])
                        yoy=_parse_number(row[yoy_i]) if yoy_i is not None and len(row)>yoy_i else None
                        if rev is not None: revenue_totals[industry]=revenue_totals.get(industry,0)+rev
                        if yoy is not None: yoy_values.setdefault(industry,[]).append(yoy)
            except Exception:
                continue
        if revenue_totals:
            all_rev=sum(revenue_totals.values())
            overall_yoy=None
            # 以產業營收加權平均各產業已公布年增率；缺資料的月份不造值。
            weighted=[]; weights=[]
            for ind, vals in yoy_values.items():
                weight=revenue_totals.get(ind,0)
                if vals and weight>0: weighted.append(sum(vals)/len(vals)*weight); weights.append(weight)
            if weights: overall_yoy=sum(weighted)/sum(weights)
            revenue_by_month.append({"month":label,"overall":overall_yoy,"industries":{k:(sum(v)/len(v)) for k,v in yoy_values.items() if v}})

        # TWSE 月底附近最近一個有資料的交易日，取全上市股票成交金額後按產業彙總。
        last_day=calendar.monthrange(year,month)[1]
        day=datetime.date(year,month,last_day)
        amount_by_industry={}
        for _ in range(8):
            if day.weekday()<5 and day<=today:
                url=f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={day:%Y%m%d}&type=ALLBUT0999&response=json"
                try:
                    payload=json.loads(_read_url(url))
                    found=False
                    for table in payload.get("tables",[]):
                        fields=table.get("fields",[]); data=table.get("data",[])
                        code_i=next((i for i,h in enumerate(fields) if "證券代號" in h or "股票代號" in h),None)
                        amount_i=next((i for i,h in enumerate(fields) if "成交金額" in h),None)
                        if code_i is None or amount_i is None: continue
                        for row in data:
                            if len(row)<=max(code_i,amount_i): continue
                            code=str(row[code_i]).strip()
                            amount=_parse_number(row[amount_i])
                            if code.isdigit() and amount is not None:
                                ind=code_industry.get(code,"未分類")
                                amount_by_industry[ind]=amount_by_industry.get(ind,0)+amount
                        found=True
                    if found and amount_by_industry: break
                except Exception:
                    pass
            day-=datetime.timedelta(days=1)
        if amount_by_industry:
            total=sum(amount_by_industry.values())
            turnover_by_month.append({"month":label,"overall":100.0 if total else None,"industries":{k:v/total*100 for k,v in amount_by_industry.items()} if total else {}})

    industries=set()
    for item in revenue_by_month: industries.update(item["industries"].keys())
    for item in turnover_by_month: industries.update(item["industries"].keys())
    def series_for(rows, key):
        return [{"month":r["month"],"value":r.get(key)} for r in rows if r.get(key) is not None]
    revenue_ind={ind:[{"month":r["month"],"value":r["industries"].get(ind)} for r in revenue_by_month if r["industries"].get(ind) is not None] for ind in industries}
    turnover_ind={ind:[{"month":r["month"],"value":r["industries"].get(ind)} for r in turnover_by_month if r["industries"].get(ind) is not None] for ind in industries}
    return {"revenue_yoy_overall":series_for(revenue_by_month,"overall"),"revenue_yoy_by_industry":revenue_ind,"turnover_share_overall":[],"turnover_share_by_industry":turnover_ind}


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
  --bg: #f3f6fb;
  --surface: #ffffff;
  --surface-2: #edf2f8;
  --surface-3: #dbe4ef;
  --ink: #172033;
  --muted: #64748b;
  --accent: #38bdf8;
  --accent-2: #818cf8;
  --success: #34d399;
  --warning: #fbbf24;
  --danger: #f87171;
  --line: rgba(100,116,139,.22);
  --radius: 14px;
  --shadow: 0 4px 12px rgba(15,23,42,.06);
  --shadow-lg: 0 12px 28px rgba(15,23,42,.10);
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
  background: linear-gradient(135deg, #ffffff 0%, #edf5ff 100%);
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
  max-width: 1400px;
  margin: .35rem auto .6rem;
  padding: .35rem 1.25rem .25rem;
  position: sticky;
  top: 0;
  z-index: 20;
  background: var(--bg);
  border-bottom: 1px solid var(--line);
}

.tab-section-title {
  font-size: .68rem;
  color: var(--muted);
  letter-spacing: .06em;
  margin-bottom: .25rem;
}

.tab-grid {
  display: flex;
  gap: .45rem;
  overflow-x: auto;
  padding: .15rem .1rem .45rem;
  scrollbar-width: thin;
}

.tab-card {
  flex: 0 0 auto;
  min-width: 118px;
  max-width: 180px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: .55rem .8rem;
  text-align: left;
  cursor: pointer;
  transition: background .18s, border-color .18s;
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
  font-size: 1.05rem;
  margin-right: .35rem;
  display: inline;
}

.tab-title {
  display: inline;
  font-size: .78rem;
  font-weight: 600;
  white-space: nowrap;
}

.tab-desc { display: none; }

.tab-count {
  display: none;
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
  max-width: 1400px;
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


.overview-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem;margin:1rem 0 1.2rem}
.overview-columns{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1rem}
.overview-card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:1.2rem;box-shadow:var(--shadow);min-width:0}
.overview-label{font-size:.82rem;color:var(--muted);margin-bottom:.35rem}.overview-value{font-size:clamp(1.35rem,2.2vw,2rem);font-weight:700;letter-spacing:-.03em;overflow-wrap:anywhere}.overview-note{font-size:.75rem;color:var(--muted);margin-top:.35rem}.overview-card h3{font-size:1rem;margin-bottom:1rem}.breadth-row{display:flex;flex-wrap:wrap;gap:1rem;font-weight:600;font-size:.9rem}.trend-up{color:#15803d}.trend-down{color:#b91c1c}.breadth-bar{height:10px;display:flex;overflow:hidden;border-radius:99px;margin:1rem 0}.industry-bar-row{display:grid;grid-template-columns:minmax(70px,auto) 1fr 36px;gap:.6rem;align-items:center;margin:.7rem 0;font-size:.82rem}.industry-bar{height:9px;border-radius:99px;background:#e2e8f0;overflow:hidden}.industry-bar i{display:block;height:100%;background:#3b82f6;border-radius:99px}.industry-bar-row b{text-align:right;font-variant-numeric:tabular-nums}.overview-foot{display:flex;flex-wrap:wrap;gap:1rem;padding:1rem;background:#eaf2ff;border-radius:12px;font-size:.82rem;color:#334155}.overview-disclaimer{font-size:.75rem;color:var(--muted);margin-top:1rem;line-height:1.7}
.trend-controls{display:flex;align-items:center;gap:.55rem;flex-wrap:wrap;margin:.65rem 0 1rem}.trend-controls label{font-size:.8rem;color:var(--muted);font-weight:600}.trend-controls select{border:1px solid var(--line);border-radius:8px;padding:.45rem .65rem;background:#fff;color:var(--ink);font:inherit;font-size:.82rem}.trend-grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:1rem 0}.trend-card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:1.1rem;min-width:0;box-shadow:var(--shadow)}.trend-card h3{font-size:1rem;margin-bottom:.25rem}.trend-card .trend-desc{font-size:.76rem;color:var(--muted);margin-bottom:.75rem}.trend-chart{width:100%;min-height:210px;overflow:hidden}.trend-chart svg{display:block;width:100%;height:auto}.chart-empty{min-height:170px;display:flex;align-items:center;justify-content:center;text-align:center;padding:1rem;color:var(--muted);font-size:.85rem;background:var(--surface-2);border-radius:10px}.chart-legend{display:flex;gap:.7rem;flex-wrap:wrap;font-size:.75rem;color:var(--muted);margin-top:.45rem}.chart-legend span{display:inline-flex;align-items:center;gap:.3rem}.legend-dot{display:inline-block;width:9px;height:9px;border-radius:50%}@media(max-width:760px){.trend-grid{grid-template-columns:1fr}}
.industry-table-wrap{overflow:auto;border:1px solid var(--line);border-radius:12px;margin-top:.6rem}.industry-table{border-collapse:collapse;width:100%;font-size:.82rem;white-space:nowrap}.industry-table th,.industry-table td{padding:.7rem .8rem;border-bottom:1px solid var(--line);text-align:right}.industry-table th{background:var(--surface-2);color:var(--accent);position:sticky;top:0}.industry-table th:first-child,.industry-table td:first-child{text-align:left}.industry-table tbody tr:hover{background:rgba(59,130,246,.06)}
.nav-hint{font-size:.68rem;color:var(--muted);margin-left:.3rem}
@media(max-width:760px){.overview-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.overview-columns{grid-template-columns:1fr}}
@media(max-width:420px){.overview-grid{grid-template-columns:1fr}}

@media (max-width: 768px) {
  .header-inner {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-right {
    width: 100%;
    justify-content: space-between;
  }

  .tab-grid { display:flex; }
  .tab-card { min-width: 112px; }

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
  .tab-grid { display:flex; }
  .tab-card { min-width: 108px; }

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
  <div class="tab-section-title">快速導覽 <span class="nav-hint">· 橫向排列、固定於上方，切換頁籤不必回到頁首</span></div>
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
const CHART_HISTORY = {{CHART_HISTORY_JSON}};

let currentTab = "overview";
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
  let s = String(value).trim();
  if (!s || ["—", "－", "-", "--", "N/A", "X", "除權息", "除息", "除權"].includes(s)) return null;
  // TWSE 部分欄位使用逗號、百分比符號或括號表示負數。
  const negative = /^\(.*\)$/.test(s);
  s = s.replace(/[，,\s]/g, "").replace(/%$/, "").replace(/^\(|\)$/g, "");
  if (!s || !/^[+-]?(?:\d+\.?\d*|\.\d+)$/.test(s)) return null;
  const number = Number(s);
  return Number.isFinite(number) ? (negative ? -Math.abs(number) : number) : null;
}

function signedChange(row) {
  // TWSE OpenAPI 的 STOCK_DAY_ALL 使用英文 Change；傳統表格則可能拆成漲跌(+/-)與漲跌價差。
  if (!row) return null;
  const signed = row["漲跌(+/-)"] ?? row["漲跌"];
  const rawChange = row["Change"] ?? row["change"];
  const delta = parseNumeric(row["漲跌價差"]);
  if (signed != null && String(signed).trim()) {
    const sign = String(signed).trim();
    if (sign.includes("+") || sign === "紅") return delta == null ? 1 : Math.abs(delta);
    if (sign.includes("-") || sign === "綠") return delta == null ? -1 : -Math.abs(delta);
    const n = parseNumeric(sign);
    if (n !== null) return n;
  }
  if (rawChange != null && String(rawChange).trim()) {
    const n = parseNumeric(rawChange);
    if (n !== null) return n;
    // X、除權息等非數值標記代表不能由該欄判定漲跌，避免誤當平盤。
    if (/^(X|除權息|除權|除息|—|－|-|--)$/i.test(String(rawChange).trim())) return null;
  }
  if (delta !== null) return delta;
  return null;
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

  const dashboardMeta = {tab_id:"overview", title:"整體統計分析看板", icon:"🧭", color:"#2563eb", desc:"市場廣度、成交量、估值與營收快速總覽"};
  [dashboardMeta, ...TAB_META].forEach(meta => {
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
  if (tabId === "overview") renderOverview();
  else renderContentPanel(tabId);
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
  // 以公司基本資料的中文產業名稱為準。營收資料的「產業別」欄位可能是數字代碼，
  // 因此先用股票代號對應基本資料，避免下拉選單出現代碼或篩選失敗。
  const code = getStockCode(row);
  const mapped = code ? getCompanyIndustryMap().get(code) : "";
  if (mapped) return mapped;
  const raw = row && row["產業別"] != null ? String(row["產業別"]).trim() : "";
  const known = new Set(getIndustries("company"));
  return known.has(raw) ? raw : "";
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

function renderTrendChart(containerId, series, period, valueSuffix = "%") {
  const host = document.getElementById(containerId);
  if (!host) return;
  const sliced = (series || []).slice(-period);
  const usable = sliced.filter(p => Number.isFinite(Number(p.value)));
  if (usable.length < 2) {
    host.innerHTML = '<div class="chart-empty">目前可用的歷史月份不足，無法繪製趨勢線。<br>請更新／補齊歷史月資料後再查看。</div>';
    return;
  }
  const W=620,H=220,L=48,R=16,T=16,B=34, plotW=W-L-R, plotH=H-T-B;
  const vals=usable.map(p=>Number(p.value));
  let min=Math.min(...vals), max=Math.max(...vals);
  if (min===max) { min-=1; max+=1; }
  const pad=(max-min)*.12; min-=pad; max+=pad;
  const x=i=>L+(usable.length===1?plotW/2:i*plotW/(usable.length-1));
  const y=v=>T+(max-v)/(max-min)*plotH;
  const points=usable.map((p,i)=>`${x(i)},${y(Number(p.value))}`).join(' ');
  const grid=[0,.5,1].map(fr=>{const yy=T+fr*plotH, vv=max-fr*(max-min);return `<line x1="${L}" y1="${yy}" x2="${W-R}" y2="${yy}" stroke="#e2e8f0"/><text x="${L-8}" y="${yy+4}" text-anchor="end" font-size="10" fill="#64748b">${vv.toLocaleString('zh-TW',{maximumFractionDigits:1})}${valueSuffix}</text>`}).join('');
  const labelEvery=Math.max(1,Math.ceil(usable.length/6));
  const labels=usable.map((p,i)=>(i%labelEvery===0||i===usable.length-1)?`<text x="${x(i)}" y="${H-10}" text-anchor="middle" font-size="10" fill="#64748b">${escapeHtml(p.month)}</text>`:'').join('');
  const dots=usable.map((p,i)=>`<circle cx="${x(i)}" cy="${y(Number(p.value))}" r="3.2" fill="#2563eb"><title>${escapeHtml(p.month)}：${Number(p.value).toLocaleString('zh-TW',{maximumFractionDigits:2})}${valueSuffix}</title></circle>`).join('');
  host.innerHTML=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="期間趨勢圖">${grid}<polyline points="${points}" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>${dots}${labels}</svg>`;
}
function refreshTrendCharts() {
  const periodEl=document.getElementById('trendPeriod');
  const period=periodEl?Number(periodEl.value):12;
  const selected=document.getElementById('trendIndustry');
  const industry=selected?selected.value:'all';
  const revenueSeries=industry==='all'?(CHART_HISTORY.revenue_yoy_overall||[]):((CHART_HISTORY.revenue_yoy_by_industry||{})[industry]||[]);
  renderTrendChart('revenueTrendChart',revenueSeries,period,'%');
  let turnoverIndustry=industry;
  if (turnoverIndustry==='all') {
    const latest=(CHART_HISTORY.turnover_share_by_industry||{});
    turnoverIndustry=Object.keys(latest).sort((a,b)=>{
      const av=latest[a].length?Number(latest[a][latest[a].length-1].value):-1;
      const bv=latest[b].length?Number(latest[b][latest[b].length-1].value):-1;
      return bv-av;
    })[0]||'';
  }
  const turnoverSeries=turnoverIndustry?((CHART_HISTORY.turnover_share_by_industry||{})[turnoverIndustry]||[]):[];
  const turnoverTitle=document.querySelector('#turnoverTrendChart')?.closest('.trend-card')?.querySelector('.trend-desc');
  if (turnoverTitle) turnoverTitle.textContent=industry==='all'?(turnoverIndustry?`目前顯示最新月份成交占比最高的產業：${turnoverIndustry}；可從上方選單切換產業。`:'歷史成交資料尚未取得。'):'目前選取產業：'+industry+'；占比為該月產業成交金額／全市場成交金額。';
  renderTrendChart('turnoverTrendChart',turnoverSeries,period,'%');
}

function industryDisplayLabel(name, indexMap) {
  const raw = String(name || "未分類").trim() || "未分類";
  // 若來源已帶分類編號，直接保留；否則依中文產業名稱建立穩定的兩位數序號。
  if (/^\d{1,2}\s+/.test(raw)) return raw.replace(/^(\d{1,2})\s+/, (_, n) => n.padStart(2, "0") + " ");
  const n = indexMap && indexMap.get(raw);
  return (n ? String(n).padStart(2, "0") + " " : "") + raw;
}

function renderOverview() {
  const fmt = v => Number.isFinite(v) ? v.toLocaleString("zh-TW", {maximumFractionDigits:2}) : "—";
  const rows = id => API_DATA[id] && Array.isArray(API_DATA[id].data) ? API_DATA[id].data : [];
  const stocks = rows("stock_day"), valuation = rows("bwibbu"), revenue = rows("revenue"), companies = rows("company");
  const firstValue = (r, keys) => { for (const k of keys) if (r[k] != null && String(r[k]).trim() !== "") return r[k]; return null; };
  const numeric = (r, keys) => parseNumeric(firstValue(r, keys));
  const sum = (arr, keys) => arr.reduce((n,r)=>n+(numeric(r,keys)||0),0);
  const avg = a => a.length ? a.reduce((x,y)=>x+y,0)/a.length : null;
  const codeOf = r => getStockCode(r);
  const industryOf = r => {
    const mapped = getIndustryForRow(r, "company");
    if (mapped) return mapped;
    const raw = r && r["產業別"] != null ? String(r["產業別"]).trim() : "";
    return raw && !/^\d+$/.test(raw) ? raw : "未分類";
  };
  const industryMap = new Map();
  companies.forEach(r => { const i=industryOf(r); if(!industryMap.has(i)) industryMap.set(i,{name:i,companies:0,pe:[],yield:[],revenue:0,revenueYoY:[],stocks:0,amount:0,up:0,down:0}); industryMap.get(i).companies++; });
  valuation.forEach(r=>{const i=industryOf(r);if(!industryMap.has(i))industryMap.set(i,{name:i,companies:0,pe:[],yield:[],revenue:0,revenueYoY:[],stocks:0,amount:0,up:0,down:0});const x=industryMap.get(i);const pe=numeric(r,["本益比","PEratio","PERatio","peRatio"]), y=numeric(r,["殖利率(%)","殖利率","DividendYield","dividendYield"]);if(pe!==null&&pe>0&&pe<1000)x.pe.push(pe);if(y!==null&&y>=0&&y<=100)x.yield.push(y);});
  revenue.forEach(r=>{const i=industryOf(r);if(!industryMap.has(i))industryMap.set(i,{name:i,companies:0,pe:[],yield:[],revenue:0,revenueYoY:[],stocks:0,amount:0,up:0,down:0});const x=industryMap.get(i);const rev=numeric(r,["當月營收","營業收入-當月營收","當月營業收入","營業收入"]);if(rev!==null)x.revenue+=rev;const yoy=numeric(r,["去年同月增減(%)","營業收入-去年同月增減(%)","去年同月增減百分比","年增率"]);if(yoy!==null)x.revenueYoY.push(yoy);});
  stocks.forEach(r=>{const i=industryOf(r);if(!industryMap.has(i))industryMap.set(i,{name:i,companies:0,pe:[],yield:[],revenue:0,revenueYoY:[],stocks:0,amount:0,up:0,down:0});const x=industryMap.get(i);x.stocks++;x.amount+=numeric(r,["成交金額","TradeValue","tradeValue"])||0;const ch=signedChange(r);if(ch!==null){if(ch>0)x.up++;else if(ch<0)x.down++;}});
  const industryStats=[...industryMap.values()].sort((a,b)=>b.companies-a.companies);
  const industryNameOrder=[...new Set(industryStats.map(x=>x.name))].sort((a,b)=>a.localeCompare(b,"zh-TW"));
  const industryIndexMap=new Map(industryNameOrder.map((name,i)=>[name,i+1]));
  const industryLabel=name=>industryDisplayLabel(name,industryIndexMap);
  const topIndustries=industryStats.slice(0,10);
  const up = stocks.filter(r => { const v=signedChange(r); return v!==null && v>0; }).length;
  const down = stocks.filter(r => { const v=signedChange(r); return v!==null && v<0; }).length;
  const flat = stocks.filter(r => { const v=signedChange(r); return v===null || v===0; }).length;
  const volume=sum(stocks,["成交股數","成交量","TradeVolume","tradeVolume"]), amount=sum(stocks,["成交金額","TradeValue","tradeValue"]);
  const peValues=valuation.map(r=>numeric(r,["本益比","PEratio","PERatio","peRatio"])).filter(v=>v!==null&&v>0&&v<1000);
  const yieldValues=valuation.map(r=>numeric(r,["殖利率(%)","殖利率","DividendYield","dividendYield"])).filter(v=>v!==null&&v>=0&&v<=100);
  const revenueTotal=sum(revenue,["當月營收","營業收入-當月營收","當月營業收入"]);
  const errorCount=Object.values(API_DATA).filter(x=>x.has_error).length;
  const highYield=valuation.filter(r=>{const v=numeric(r,["殖利率(%)","殖利率","DividendYield","dividendYield"]);return v!==null&&v>=5&&v<=100;}).length;
  const lowPE=valuation.filter(r=>{const v=numeric(r,["本益比","PEratio","PERatio","peRatio"]);return v!==null&&v>0&&v<=15;}).length;
  const industryRows=topIndustries.map(x=>`<tr><td>${escapeHtml(industryLabel(x.name))}</td><td>${fmt(x.companies)}</td><td>${fmt(x.stocks)}</td><td>${fmt(x.amount)}</td><td>${fmt(avg(x.pe))}</td><td>${avg(x.yield)===null?"—":fmt(avg(x.yield))+"%"}</td><td>${fmt(x.revenue)}</td><td>${avg(x.revenueYoY)===null?"—":fmt(avg(x.revenueYoY))+"%"}</td><td><span class="trend-up">${fmt(x.up)}</span> / <span class="trend-down">${fmt(x.down)}</span></td></tr>`).join("");
  mainContent.innerHTML = `<section class="content-panel active">
    <div class="panel-header"><div class="panel-icon">🧭</div><div><div class="panel-title">整體統計分析看板</div><div class="panel-subtitle">市場交易、估值、股利收益與產業財務概況；指標僅以本次取得的 API 資料計算。</div></div></div>
    <div class="overview-grid">
      <article class="overview-card"><div class="overview-label">上市公司家數</div><div class="overview-value">${fmt(companies.length)}</div><div class="overview-note">基本資料回傳筆數</div></article>
      <article class="overview-card"><div class="overview-label">成交金額合計</div><div class="overview-value">${fmt(amount)}</div><div class="overview-note">原始欄位：成交金額／TradeValue；成功解析 ${fmt(stocks.filter(r=>numeric(r,["成交金額","TradeValue","tradeValue"])!==null).length)} 筆</div></article>
      <article class="overview-card"><div class="overview-label">成交股數合計</div><div class="overview-value">${fmt(volume)}</div><div class="overview-note">原始欄位：成交股數／TradeVolume；成功解析 ${fmt(stocks.filter(r=>numeric(r,["成交股數","成交量","TradeVolume","tradeVolume"])!==null).length)} 筆</div></article>
      <article class="overview-card"><div class="overview-label">平均本益比</div><div class="overview-value">${fmt(avg(peValues))}</div><div class="overview-note">有效正值樣本 ${fmt(peValues.length)} 檔；來源欄位含 PEratio</div></article>
      <article class="overview-card"><div class="overview-label">平均殖利率</div><div class="overview-value">${avg(yieldValues)===null?"—":fmt(avg(yieldValues))+"%"}</div><div class="overview-note">有效樣本 ${fmt(yieldValues.length)} 檔；來源欄位含 DividendYield</div></article>
      <article class="overview-card"><div class="overview-label">高殖利率個股</div><div class="overview-value">${fmt(highYield)}</div><div class="overview-note">殖利率 ≥ 5%（依當前資料）</div></article>
      <article class="overview-card"><div class="overview-label">低本益比個股</div><div class="overview-value">${fmt(lowPE)}</div><div class="overview-note">本益比 > 0 且 ≤ 15</div></article>
      <article class="overview-card"><div class="overview-label">營收資料筆數</div><div class="overview-value">${fmt(revenue.length)}</div><div class="overview-note">營收合計 ${fmt(revenueTotal)}（原始單位）</div></article>
      <article class="overview-card"><div class="overview-label">資料異常端點</div><div class="overview-value">${fmt(errorCount)}</div><div class="overview-note">共 ${fmt(Object.keys(API_DATA).length)} 個資料端點</div></article>
    </div>
    <div class="overview-columns"><article class="overview-card"><h3>市場漲跌廣度</h3><div class="breadth-row"><span class="trend-up">上漲 ${fmt(up)}</span><span class="trend-down">下跌 ${fmt(down)}</span><span>其他 ${fmt(flat)}</span></div><div class="breadth-bar"><span style="width:${stocks.length?up/stocks.length*100:0}%;background:#16a34a"></span><span style="width:${stocks.length?down/stocks.length*100:0}%;background:#dc2626"></span><span style="flex:1;background:#cbd5e1"></span></div><p class="overview-note">漲跌以 API 可辨識的「漲跌價差／漲跌」欄位計算；若欄位缺失，請以大盤統計資料核對。</p></article>
    <article class="overview-card"><h3>上市公司家數最多的產業</h3>${topIndustries.length?topIndustries.slice(0,8).map(x=>`<div class="industry-bar-row"><span>${escapeHtml(industryLabel(x.name))}</span><div class="industry-bar"><i style="width:${x.companies/Math.max(...topIndustries.map(z=>z.companies),1)*100}%"></i></div><b>${fmt(x.companies)}</b></div>`).join(""):'<p>尚無產業資料</p>'}</article></div>
    <article class="overview-card"><h3>主要產業比較（按上市公司家數排序）</h3><p class="overview-note">成交金額、營收合計沿用 API 原始單位；平均本益比與殖利率只使用有效數值。營收年增率為可辨識年增欄位的簡單平均，若來源欄位不同會顯示 —。</p><div class="industry-table-wrap"><table class="industry-table"><thead><tr><th>產業別</th><th>公司家數</th><th>成交資料檔數</th><th>成交金額合計</th><th>平均本益比</th><th>平均殖利率</th><th>營收合計</th><th>平均營收年增率</th><th>上漲 / 下跌</th></tr></thead><tbody>${industryRows||'<tr><td colspan="9">目前沒有可用產業資料</td></tr>'}</tbody></table></div></article>
    <section class="trend-grid-wrap"><div class="panel-header" style="margin-top:1.25rem"><div><div class="panel-title">產業趨勢分析</div><div class="panel-subtitle">可切換觀察期間與產業；僅繪製來源確實提供的歷史資料，不以單月快照推估過去月份。</div></div></div>
    <div class="trend-controls"><label for="trendPeriod">觀察期間</label><select id="trendPeriod" onchange="refreshTrendCharts()"><option value="3">近 3 個月</option><option value="6">近 6 個月</option><option value="12" selected>近 12 個月</option></select><label for="trendIndustry">產業</label><select id="trendIndustry" onchange="refreshTrendCharts()"><option value="all">整體市場</option>${industryStats.map(x=>`<option value="${escapeHtml(x.name)}">${escapeHtml(industryLabel(x.name))}</option>`).join('')}</select></div>
    <div class="trend-grid"><article class="trend-card"><h3>近 12 個月各產業營收年增率趨勢</h3><p class="trend-desc">月營收年增率；切換產業可查看單一產業的月度變化。</p><div id="revenueTrendChart" class="trend-chart"></div></article><article class="trend-card"><h3>產業成交金額占比變化</h3><p class="trend-desc">各月產業成交金額占上市股票成交金額總和的比例。</p><div id="turnoverTrendChart" class="trend-chart"></div></article></div></section>
    <div class="overview-foot"><span>日成交資料：${fmt(stocks.length)} 筆</span><span>估值資料：${fmt(valuation.length)} 筆</span><span>股利資料：${fmt(rows("dividend").length)} 筆</span><span>資料端點異常：${fmt(errorCount)}</span></div>
    <p class="overview-disclaimer">本看板為描述性統計，不構成投資建議。這些數值是本次擷取資料的橫斷面概況，不代表歷史趨勢或即時行情；產業間比較可能受缺漏欄位、資料更新時間及公司家數差異影響。</p>
  </section>`;
  refreshTrendCharts();
}
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
renderOverview();

</script>
</body>
</html>
"""


# ============================================================
# 產生 HTML
# ============================================================

def generate_html(all_data, chart_history=None):
    total_endpoints = len(all_data)

    total_records = sum(
        item["count"] for item in all_data.values()
    )

    error_count = sum(
        1
        for item in all_data.values()
        if item["has_error"]
    )

    if chart_history is None:
        chart_history = {"revenue_yoy_overall": [], "revenue_yoy_by_industry": {}, "turnover_share_overall": [], "turnover_share_by_industry": {}}

    chart_history_json = json.dumps(chart_history, ensure_ascii=False, default=str)

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
        "{{CHART_HISTORY_JSON}}": chart_history_json,
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

    print("擷取近 12 個月產業趨勢資料...")
    chart_history = fetch_chart_history(all_data, months=12)

    html = generate_html(all_data, chart_history=chart_history)

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
