# PTCG Pocket Analysis

## 專案簡介
`PTCG_Pocket_Analysis` 是一個用於分析 Pokémon TCG Pocket 遊戲評論的專案。此專案提供以下功能：

- **情感分析**：判斷評論的情感分佈（正面、中立、負面）。
- **關鍵字提取**：從評論中找出重要的關鍵字。
- **趨勢比較**：比較不同時間範圍內的評論變化。
- **數據視覺化**：圖表呈現評論數據與情感分佈。

---

## 功能說明
### 1. API 服務
使用 FastAPI 提供 RESTful API，支援以下功能：
- 上傳 CSV 檔案，並指定兩個時間範圍。
- 返回評論的情感分佈、關鍵字提取結果，以及評論趨勢的圖表。

### 2. 資料標準化
- `standardization.py`：將 CSV 檔案標準化，確保資料格式一致。

### 3. API 請求範例
- `request.py`：提供範例程式碼，展示如何向 API 發送請求並處理回應。

---

## 專案結構
```plaintext
PTCG_Pocket_Analysis/
├── main.py                 # FastAPI 主程式，提供評論分析 API
├── standardization.py      # 資料標準化程式
├── request.py              # API 請求範例程式碼
├── PTCG_Pocket.csv         # 原始評論資料
├── filtered_data.csv       # 篩選後的評論資料
├── requirements.txt        # 專案依賴的函式庫
└── README.md               # 專案說明文件
```

---

## 安裝與使用
### 1. 環境準備
請確保已安裝 **Python 3.8 或以上版本**，並建立虛擬環境：
```sh
python3 -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows
```

### 2. 安裝依賴套件
```sh
pip install -r requirements.txt
```

### 3. 資料標準化
執行以下指令，將 `PTCG_Pocket.csv` 轉換為標準化格式，確保後續分析可正常執行。
```sh
python standardization.py
```

### 4. 啟動 API 服務
使用 Uvicorn 啟動 FastAPI 伺服器：
```sh
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
### 5. 查詢伺服器內網IP
執行範例請求程式：
```sh
ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1  # macOS/Linux
ipconfig | findstr "IPv4" | for /F "tokens=14 delims= " %i in ('findstr "IPv4"') do @echo %i  # Windows
```

### 6. 發送 API 請求
執行範例請求程式：
```sh
python request.py
```

---

## API 介面說明
### **POST `/analyze`**
**功能**：分析評論的情感分佈與趨勢。

**請求參數**：
| 參數  | 說明 |
|-------|------|
| `file` | 上傳的 CSV 檔案，包含評論資料 |
| `time1` | 第一個時間範圍（格式：YYYY-MM-DD,YYYY-MM-DD） |
| `time2` | 第二個時間範圍（格式：YYYY-MM-DD,YYYY-MM-DD） |

**回應格式（JSON）**：
```json
{
  "sentiment_distribution": {
    "positive": 45,
    "neutral": 30,
    "negative": 25
  },
  "keywords": ["gameplay", "update", "bug", "graphics"],
  "trend_chart": "data:image/png;base64,..."
}
```