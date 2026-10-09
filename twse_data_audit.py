#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TWSE OpenAPI 原始資料核對工具（標準函式庫；需可連線至官方 API）。
執行：python twse_data_audit.py
輸出：twse_validation_report.json、twse_industry_validation.csv
"""
import csv, json, math, urllib.request, urllib.error
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://openapi.twse.com.tw/v1"
ENDPOINTS = {
    "stock_day": "exchangeReport/STOCK_DAY_ALL",
    "valuation": "exchangeReport/BWIBBU_ALL",
    "company": "opendata/t187ap03_L",
    "revenue": "opendata/t187ap05_L",
    "market": "exchangeReport/MI_INDEX",
}
OUT = Path(__file__).resolve().parent

def fetch(name, endpoint):
    url = f"{BASE}/{endpoint}"
    req = urllib.request.Request(url, headers={"User-Agent":"TWSE-Data-Audit/1.0", "Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8-sig")
        data = json.loads(raw)
        if isinstance(data, list): return {"url":url,"data":data,"error":None}
        return {"url":url,"data":data if isinstance(data,dict) else [],"error":None}
    except Exception as exc:
        return {"url":url,"data":[],"error":f"{type(exc).__name__}: {exc}"}

def first(row, keys):
    for key in keys:
        if key in row and row[key] is not None and str(row[key]).strip() != "":
            return row[key]
    return None

def number(value):
    if value is None: return None
    s=str(value).strip().replace(",","").replace("，","").replace("%","").replace(" ","")
    if not s or s.upper() in {"N/A","NA","X","-","--","—","－","除權息","除權","除息"}: return None
    neg=s.startswith("(") and s.endswith(")")
    if neg: s=s[1:-1]
    try:
        n=float(s)
        if not math.isfinite(n): return None
        return -abs(n) if neg else n
    except ValueError: return None

def rows(payload):
    data=payload.get("data",[])
    if isinstance(data,list): return data
    # MI_INDEX 等端點若回傳物件，盡可能找出其列資料，不猜測未知結構。
    for key in ("data","Data","tables","Tables"):
        if isinstance(data,dict) and isinstance(data.get(key),list): return data[key]
    return []

def code(row):
    v=first(row,["公司代號","證券代號","有價證券代號","股票代號","Code","code"])
    return str(v).strip().removesuffix(".0") if v is not None else ""

def label(row):
    return str(first(row,["產業別","產業名稱","Industry","industry"]) or "未分類").strip() or "未分類"

def date_value(row):
    return first(row,["Date","date","日期","資料日期"])

def main():
    fetched={k:fetch(k,v) for k,v in ENDPOINTS.items()}
    data={k:rows(v) for k,v in fetched.items()}
    errors={k:v["error"] for k,v in fetched.items() if v["error"]}
    company_map={code(r):label(r) for r in data["company"] if code(r)}
    def industry(r): return company_map.get(code(r), label(r))
    stocks=data["stock_day"]; vals=data["valuation"]
    amounts=[number(first(r,["成交金額","TradeValue","tradeValue"])) for r in stocks]
    volumes=[number(first(r,["成交股數","成交量","TradeVolume","tradeVolume"])) for r in stocks]
    pes=[number(first(r,["本益比","PEratio","PERatio","peRatio"])) for r in vals]
    yields=[number(first(r,["殖利率(%)","殖利率","DividendYield","dividendYield"])) for r in vals]
    changes=[]
    for r in stocks:
        v=number(first(r,["漲跌價差","Change","change","漲跌(+/-)","漲跌"]))
        changes.append(v)
    valid_pe=[x for x in pes if x is not None and 0<x<1000]
    valid_yield=[x for x in yields if x is not None and 0<=x<=100]
    high_yield=[x for x in yields if x is not None and 5<=x<=100]
    low_pe=[x for x in pes if x is not None and 0<x<=15]
    by_ind=defaultdict(lambda:{"company_count":0,"stock_rows":0,"unique_stock_codes":set(),"trade_value_sum":0,"trade_value_valid_rows":0,"trade_volume_sum":0,"trade_volume_valid_rows":0,"up":0,"down":0,"flat_or_unknown":0,"pe_values":[],"yield_values":[],"revenue_sum":0,"revenue_valid_rows":0})
    for r in data["company"]:
        by_ind[industry(r)]["company_count"]+=1
    for r in vals:
        i=industry(r); x=by_ind[i]
        pe=number(first(r,["本益比","PEratio","PERatio","peRatio"]))
        y=number(first(r,["殖利率(%)","殖利率","DividendYield","dividendYield"]))
        if pe is not None and 0<pe<1000: x["pe_values"].append(pe)
        if y is not None and 0<=y<=100: x["yield_values"].append(y)
    for r in stocks:
        i=industry(r); x=by_ind[i]; x["stock_rows"]+=1
        c=code(r)
        if c: x["unique_stock_codes"].add(c)
        a=number(first(r,["成交金額","TradeValue","tradeValue"]))
        v=number(first(r,["成交股數","成交量","TradeVolume","tradeVolume"]))
        if a is not None: x["trade_value_sum"]+=a; x["trade_value_valid_rows"]+=1
        if v is not None: x["trade_volume_sum"]+=v; x["trade_volume_valid_rows"]+=1
        ch=number(first(r,["漲跌價差","Change","change","漲跌(+/-)","漲跌"]))
        if ch is None: x["flat_or_unknown"]+=1
        elif ch>0: x["up"]+=1
        elif ch<0: x["down"]+=1
        else: x["flat_or_unknown"]+=1
    for r in data["revenue"]:
        x=by_ind[industry(r)]
        rev=number(first(r,["當月營收","營業收入-當月營收","當月營業收入","營業收入","營業收入-當月營收(千元)"]))
        if rev is not None: x["revenue_sum"]+=rev; x["revenue_valid_rows"]+=1
    def avg(a): return sum(a)/len(a) if a else None
    def clean(v):
        if isinstance(v,set): return sorted(v)
        if isinstance(v,dict): return {k:clean(x) for k,x in v.items()}
        if isinstance(v,list): return [clean(x) for x in v]
        return v
    date_sets={k:sorted({str(date_value(r)) for r in data[k] if date_value(r) is not None}) for k in ("stock_day","valuation","market")}
    date_summary={k:(v if len(v)<=8 else v[:4]+["…"]+v[-3:]) for k,v in date_sets.items()}
    exact_stock_valuation_overlap=bool(set(date_sets["stock_day"]) & set(date_sets["valuation"]))
    market_valuation_overlap=bool(set(date_sets["market"]) & set(date_sets["valuation"]))
    if exact_stock_valuation_overlap:
        date_check_status="PASS"
        date_check_note="個股成交與估值端點的日期欄位有交集。"
    elif not date_sets["stock_day"] and market_valuation_overlap:
        date_check_status="PARTIAL_PASS"
        date_check_note="個股成交端點未提供可辨識日期；大盤統計與估值端點日期一致，但個股成交端點仍需依官方更新時點確認。"
    elif date_sets["stock_day"] and date_sets["valuation"]:
        date_check_status="MISMATCH"
        date_check_note="個股成交與估值端點的日期欄位沒有交集。"
    else:
        date_check_status="CHECK_REQUIRED"
        date_check_note="日期欄位不足，不能由原始資料確認同一交易日。"
    industry_amount_sum=sum(v["trade_value_sum"] for v in by_ind.values())
    industry_volume_sum=sum(v["trade_volume_sum"] for v in by_ind.values())
    industry_stock_row_sum=sum(v["stock_rows"] for v in by_ind.values())
    raw_amount_sum=sum(x for x in amounts if x is not None)
    raw_volume_sum=sum(x for x in volumes if x is not None)
    report={
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "sources":{k:{"url":v["url"],"row_count":len(data[k]),"error":v["error"]} for k,v in fetched.items()},
      "errors":errors,
      "date_fields_found":date_summary,
      "same_trading_date_check":{"status":date_check_status,"note":date_check_note,"stock_day_valuation_date_overlap":exact_stock_valuation_overlap,"market_valuation_date_overlap":market_valuation_overlap},
      "reconciliation_checks":{
        "industry_stock_rows_equal_market_stock_rows":industry_stock_row_sum==len(stocks),
        "industry_trade_value_sum_equals_market_raw_sum":math.isclose(industry_amount_sum,raw_amount_sum,rel_tol=1e-9,abs_tol=0.01),
        "industry_trade_volume_sum_equals_market_raw_sum":math.isclose(industry_volume_sum,raw_volume_sum,rel_tol=1e-9,abs_tol=0.01),
        "industry_stock_rows_sum":industry_stock_row_sum,
        "market_stock_rows":len(stocks),
        "industry_trade_value_sum":industry_amount_sum,
        "market_raw_trade_value_sum":raw_amount_sum,
        "industry_trade_volume_sum":industry_volume_sum,
        "market_raw_trade_volume_sum":raw_volume_sum
      },
      "market_summary":{
        "stock_rows":len(stocks),"stock_unique_codes":len({code(r) for r in stocks if code(r)}),
        "trade_value_sum":sum(x for x in amounts if x is not None),"trade_value_valid_rows":sum(x is not None for x in amounts),"trade_value_missing_rows":sum(x is None for x in amounts),
        "trade_volume_sum":sum(x for x in volumes if x is not None),"trade_volume_valid_rows":sum(x is not None for x in volumes),"trade_volume_missing_rows":sum(x is None for x in volumes),
        "pe_average":avg(valid_pe),"pe_valid_sample_count":len(valid_pe),"pe_missing_or_invalid_count":len(vals)-len(valid_pe),
        "yield_average":avg(valid_yield),"yield_valid_sample_count":len(valid_yield),"yield_missing_or_invalid_count":len(vals)-len(valid_yield),
        "high_yield_ge_5_count":len(high_yield),"low_pe_0_to_15_count":len(low_pe),
        "up_count":sum(1 for x in changes if x is not None and x>0),"down_count":sum(1 for x in changes if x is not None and x<0),"flat_or_unknown_count":sum(1 for x in changes if x is None or x==0),
        "industry_mapping_coverage_count":sum(1 for r in stocks if code(r) in company_map),"industry_mapping_coverage_rate":(sum(1 for r in stocks if code(r) in company_map)/len(stocks) if stocks else None),
      },
      "industry_summary":clean({k:{**v,"unique_stock_codes_count":len(v["unique_stock_codes"]),"average_pe":avg(v["pe_values"]),"pe_sample_count":len(v["pe_values"]),"average_yield":avg(v["yield_values"]),"yield_sample_count":len(v["yield_values"])} for k,v in sorted(by_ind.items())}),
      "validation_notes":[
        "金額與股數只加總可解析數值；報告同時列出有效筆數與缺漏筆數。",
        "平均本益比排除非正值與 >=1000 的數值；若要調整本益比上限，請修改有效樣本篩選條件。",
        "漲跌優先採有正負號的 Change；如官方端點以特殊標記表示除權息，應列為無法判定而非平盤。",
        "產業比較以公司代號對應公司基本資料產業別；未對應資料會保留為原始產業欄位或未分類。",
        "營收合計使用原始 API 欄位單位；不同端點欄位單位若不同，不能直接混用或當作完全一致的總額。"
      ]
    }
    json_path=OUT/"twse_validation_report.json"
    json_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    csv_path=OUT/"twse_industry_validation.csv"
    with csv_path.open("w",newline="",encoding="utf-8-sig") as f:
        fields=["產業別","公司家數","成交資料筆數","唯一股票代號數","成交金額合計","成交金額有效筆數","成交股數合計","成交股數有效筆數","上漲","下跌","平盤或無法判定","平均本益比","本益比有效樣本數","平均殖利率","殖利率有效樣本數","營收合計","營收有效筆數"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for name,x in sorted(by_ind.items(),key=lambda kv:(-kv[1]["trade_value_sum"],kv[0])):
            w.writerow({"產業別":name,"公司家數":x["company_count"],"成交資料筆數":x["stock_rows"],"唯一股票代號數":len(x["unique_stock_codes"]),"成交金額合計":x["trade_value_sum"],"成交金額有效筆數":x["trade_value_valid_rows"],"成交股數合計":x["trade_volume_sum"],"成交股數有效筆數":x["trade_volume_valid_rows"],"上漲":x["up"],"下跌":x["down"],"平盤或無法判定":x["flat_or_unknown"],"平均本益比":avg(x["pe_values"]),"本益比有效樣本數":len(x["pe_values"]),"平均殖利率":avg(x["yield_values"]),"殖利率有效樣本數":len(x["yield_values"]),"營收合計":x["revenue_sum"],"營收有效筆數":x["revenue_valid_rows"]})
    print("完成原始資料核對。")
    print(f"JSON 報告：{json_path}")
    print(f"產業 CSV：{csv_path}")
    print(json.dumps({"source_rows":{k:len(data[k]) for k in data},"errors":errors,"dates":date_summary,"summary":report["market_summary"]},ensure_ascii=False,indent=2))
    if errors: raise SystemExit("部分官方端點抓取失敗，報告已標示錯誤；請確認網路後重試。")

if __name__ == "__main__": main()
