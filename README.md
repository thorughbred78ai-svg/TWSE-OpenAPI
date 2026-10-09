# TWSE-OpenAPI

# TWSE OpenAPI Dashboard

台灣證券交易所免費開放資料 API 瀏覽與查詢工具，透過 GitHub Actions 每日自動抓取最新資料並部署為靜態網站。

## 功能特色

- **免費資料來源**：直接串接臺灣券交易所 OpenAPI，無需註冊、無需 API Key
- **每日自動更新**：透過 GitHub Actions 排程自動抓取最新資料
- **網頁即時查詢**：搜尋端點名稱、代號或描述，快速找到所需資料
- **資料表格瀏覽**：點擊端點卡片即可查看資料表格與 JSON 原始資料
- **分類瀏覽**：依資料類別（公司基本資料、股利、每日交易、指數、融資融券等）篩選

## 涵蓋資料類別

| 類別 | 端點範例 |
|------|----------|
| 公司基本資料 | 上市公司基本資料、董監事資料 |
| 股利與除權息 | 股利分派、除權息參考價 |
| 每日交易 | 收盤行情、本益比、殖利率 |
| 指數 | 大盤統計、各類指數收盤 |
| 融資融券 | 融資餘額、融券餘額 |
| 借券 | 借券賣出餘額、借券成交明細 |
| ETF | ETF 淨值與折溢價 |
| 權證 | 權證基本資料、交易資料 |
| ESG | 企業 ESG 資訊揭露 |

## 快速開始

### 1. 建立 GitHub 儲存庫

1. 在 GitHub 建立一個新儲存庫（例如 `twse-api-dashboard`）
2. 將以下檔案上傳到儲存庫根目錄：
   - `.github/workflows/twse-api-dashboard.yml`
   - `build.py`

### 2. 啟用 GitHub Pages

1. 前往儲存庫 **Settings → Pages**
2. **Source** 選擇 **GitHub Actions**
3. 儲存設定

### 3. 手動觸發第一次建置

1. 前往 **Actions** 分頁
2. 選擇 **Build and Deploy TWSE API Dashboard**
3. 點擊 **Run workflow** → **Run workflow**
4. 等待建置完成後，即可在 GitHub Pages URL 瀏覽網站

### 4. 自動排程

Workflow 已設定每天台灣時間下午 2 點（UTC 06:00）自動執行，無需額外設定。

## 檔案結構

```
.
├── .github/
│   └── workflows/
│       └── twse-api-dashboard.yml   # GitHub Actions 工作流程
├── build.py                          # 網站建置腳本
├── public/                           # 建置輸出目錄（自動生成）
│   ├── index.html                    # 主網站
│   └── data.json                     # 原始資料 JSON
└── README.md
```

## 自訂端點

如需新增或移除 API 端點，請編輯 `build.py` 中的 `ENDPOINTS` 字典：

```python
ENDPOINTS = {
    "你的類別名稱": [
        {"id": "端點代號", "name": "顯示名稱", "desc": "描述說明"},
        # ...
    ],
}
```

端點代號可參考 [臺灣證券交易所 OpenAPI 文件](https://openapi.twse.com.tw/)。

## 資料來源

- [臺灣證券交易所 OpenAPI](https://openapi.twse.com.tw/)
- [證券櫃檯買賣中心 OpenAPI](https://www.tpex.org.tw/openapi/)

## 授權

本專案採用 MIT 授權。資料來源為臺灣證券交易所開放資料，依政府資料開放授權條款使用。
