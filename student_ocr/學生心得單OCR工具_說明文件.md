# 學生心得單 OCR 轉 Excel 工具

> **情境說明**
> 老師已在學生心得單上批改完分數，為了避免一筆一筆手動 key 進 Excel，
> 將心得單掃描成圖片或 PDF 後，透過此工具自動辨識學號、姓名、成績並匯出至 Excel。

---

## 程式檔案位置

```
student_ocr/
├── ocr_to_excel.py      ← 主程式
└── requirements.txt     ← 套件清單
```

---

## 安裝步驟

### 1. 安裝 Python 套件

```bash
pip install openpyxl Pillow pytesseract pdf2image
```

### 2. 安裝 Tesseract（含繁體中文語言包）

| 作業系統 | 指令 |
|---------|------|
| **macOS** | `brew install tesseract tesseract-lang` |
| **Ubuntu / Debian** | `sudo apt install tesseract-ocr tesseract-ocr-chi-tra` |
| **Windows** | 下載安裝檔：https://github.com/UB-Mannheim/tesseract/wiki （安裝時勾選 Traditional Chinese） |

---

## 使用方式

### 準備掃描檔

把所有掃描圖片或 PDF 放在同一個資料夾，例如：

```
scans/
  ├── 001.jpg
  ├── 002.png
  └── 003.pdf
```

### 執行程式

```bash
# 基本用法（輸出「學生成績.xlsx」）
python ocr_to_excel.py ./scans

# 指定輸出檔名
python ocr_to_excel.py ./scans -o 一年甲班成績.xlsx

# 逐一確認每筆辨識結果後再存檔（推薦第一次使用）
python ocr_to_excel.py ./scans --review

# 使用 Claude Vision API（辨識更準，適合手寫分數）
python ocr_to_excel.py ./scans --engine claude --api-key sk-ant-你的金鑰
```

---

## 支援的檔案格式

| 格式 | 說明 |
|------|------|
| `.jpg` / `.jpeg` | JPEG 圖片 |
| `.png` | PNG 圖片 |
| `.bmp` / `.tiff` | 其他常見圖片格式 |
| `.pdf` | PDF 掃描檔（自動取第一頁） |

---

## Excel 輸出欄位

| 欄位 | 說明 |
|------|------|
| 序號 | 自動編號 |
| 學號 | OCR 辨識的學號 |
| 姓名 | OCR 辨識的姓名 |
| 成績 | OCR 辨識的分數（0～100） |
| 來源檔案 | 對應的掃描檔名 |
| 備註 | 辨識失敗時顯示警告 |

> **黃色列**代表該筆資料有欄位未能自動辨識，請手動補填。

---

## 心得單格式建議

為了讓 OCR 能正確辨識，心得單上的標籤建議包含以下文字：

```
學號：B11234567
姓名：王小明
成績：85
```

---

## 兩種 OCR 引擎比較

| 項目 | Tesseract（預設） | Claude Vision API |
|------|-----------------|-------------------|
| 費用 | 免費 | 需付費（依 API 用量） |
| 安裝 | 需安裝本機程式 | 只需 API Key |
| 印刷文字辨識 | 良好 | 優秀 |
| 手寫文字辨識 | 一般 | 優秀 |
| 適用情境 | 大量批次、印刷清晰 | 手寫分數、格式不固定 |

---

## 常見問題

**Q：辨識率很低怎麼辦？**
- 確認掃描解析度 ≥ 300 DPI
- 改用 `--engine claude` 提升準確率
- 執行時加上 `--review` 逐一手動確認

**Q：姓名一直辨識錯誤？**
- 確認心得單上有「姓名：」標籤
- 如果表單格式特殊，可以提供格式讓程式調整解析規則

**Q：PDF 無法讀取？**
- 確認已安裝 `pdf2image` 以及系統的 `poppler`
  - macOS：`brew install poppler`
  - Ubuntu：`sudo apt install poppler-utils`
