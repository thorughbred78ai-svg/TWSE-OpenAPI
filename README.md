# TWSE-OpenAPI

# TWSE 上市個股及大盤統計資訊儀表板

自動從臺灣證券交易所（TWSE）免費 OpenAPI 抓取上市股票核心資料，每日透過 GitHub Actions 建置並部署為靜態網站，發佈於 GitHub Pages。

---

## 功能特性

- **6 大核心資料頁籤**：大盤統計、個股日成交、本益比殖利率、每月營業收入、股利分派、公司基本資料
- **即時關鍵字搜尋**：每個頁籤獨立搜尋框，支援股票代號（如 `2330`）與公司名稱（如 `台積電`）搜尋
- **欄位排序**：點擊任意表格標題即可排序，自動解析數值（含逗號分隔與百分比格式）
- **產業別篩選**：在「上市公司基本資料」頁籤可選擇產業別進行篩選
- **每日自動更新**：透過 GitHub Actions 定時執行，無需手動維護
- **全免費**：使用 TWSE 公開 API，無需 API Key

---

## 資料來源

| 頁籤 | API 端點 | 說明 |
|---|---|---|
| 大盤統計資訊 | `exchangeReport/MI_INDEX` | 每日大盤成交統計、漲跌家數 |
| 上市個股日成交資訊 | `exchangeReport/STOCK_DAY_ALL` | 全部上市股票當日開高低收、成交量、成交金額 |
| 上市個股本益比殖利率 | `exchangeReport/BWIBBU_ALL` | 本益比、殖利率、股價淨值比 |
| 上市公司每月營業收入 | `opendata/t187ap05_L` | 當月營收、上月營收、去年同月、增減百分比 |
| 上市公司股利分派情形 | `opendata/t187ap45_L` | 現金股利、股票股利、除權息日期、股東會日期 |
| 上市公司基本資料 | `opendata/t187ap03_L` | 公司全名、產業別、統一編號、資本額、成立日期 |

所有資料來自 [臺灣證券交易所 OpenAPI](https://openapi.twse.com.tw/)。

---

## 線上預覽

部署網址：`https://<你的使用者名稱>.github.io/<儲存庫名稱>/`

---

## 專案結構

```
.
├── .github/
│   └── workflows/
│       └─ twse-api-dashboard.yml    # GitHub Actions 工作流程
├── build.py                           # 資料抓取與網站產生腳本
├── public/                            # 產物目錄（Actions 自動產生）
│   ├── index.html                     # 靜態儀表板網頁
│   └── data.json                      # 原始 JSON 資料
└── README.md                          # 本檔案
```

---

## 快速開始

### 1. 複製儲存庫

```bash
git clone https://github.com/<你的使用者名稱>/<儲存庫名稱>.git
cd <儲存庫名稱>
```

### 2. 本地執行建置

```bash
python build.py
```

執行後會在 `public/` 目錄產生 `index.html` 與 `data.json`。直接用瀏覽器開啟 `public/index.html` 即可預覽。

---

## GitHub Actions 自動部署

本專案已設定 GitHub Actions 工作流程，每日 UTC 06:00 自動抓取最新資料並部署至 GitHub Pages。

### 設定步驟

1. **上傳程式碼**
   ```bash
   git add build.py .github/workflows/twse-api-dashboard.yml README.md
   git commit -m "Initial commit"
   git push origin main
   ```

2. **設定 GitHub Pages**
   - 前往儲存庫 **Settings → Pages**
   - **Source** 選擇 **Deploy from a branch**
   - **Branch** 選擇 `gh-pages` / `root`
   - 點擊 **Save**

3. **手動觸發建置**
   - 前往 **Actions → Build and Deploy TWSE API Dashboard**
   - 點擊 **Run workflow → Run workflow**

4. **等待部署完成**
   - 工作流程約 1-2 分鐘完成
   - 完成後即可透過 GitHub Pages 網址瀏覽

---

## 使用說

### 搜尋資料

- 在每個頁籤頂部的搜尋框輸入關鍵字
- 支援股票代號（如 `2330`）或公司名稱（如 `台積電`）
- 搜尋結果即時篩選，符合的文字會以高亮標記

### 排序資料

- 點擊表格任意標題欄位即可排序
- 點擊順序：**升序 → 降序 → 恢復原始順序**
- 數值欄位（如成交金額、本益比、殖利率）會自動解析並按數值大小排序
- 文字欄位則按字母/筆畫排序

### 產業別篩選

- 在「上市公司基本資料」頁籤，頂部搜尋框右側會顯示「產業別」下拉選單
- 選擇特定產業別後，表格只顯示該產業的公司
- 可搭配搜尋框同時使用

---

## 工作流程設定檔

`.github/workflows/twse-api-dashboard.yml`：

```yaml
name: Build and Deploy TWSE API Dashboard

on:
  schedule:
    - cron: '0 6 * * *'    # 每日 UTC 06:00 執行
  workflow_dispatch:       # 支援手動觸發

permissions:
  contents: write
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Build site
        run: python build.py

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./public
          publish_branch: gh-pages
```

---

## 注意事項

- TWSE OpenAPI 為免費公開資料，**無需申請 API Key**
- 資料更新頻率為每日，建置時間為 UTC 06:00（台灣時間 14:00）
- 若 API 端點暫時無法存取，頁面會顯示異常狀態並保留上次成功建置的資料
- 本專案僅供資訊參考，不構成任何投資建議

---

## 技術棧

- **資料抓取**：Python 3 + `urllib`
- **靜態網站**：純 HTML / CSS / JavaScript（無框架依賴）
- **部署**：GitHub Actions + GitHub Pages
- **字型**：Noto Sans TC、JetBrains Mono

---

## 授權

本專案程式碼採用 MIT License。資料來源與版權歸臺灣證券交易所所有。

---

## 致謝

- [臺灣證券交易所 OpenAPI](https://openapi.twse.com.tw/)
- [peaceiris/actions-gh-pages](https://github.com/peaceiris/actions-gh-pages)
