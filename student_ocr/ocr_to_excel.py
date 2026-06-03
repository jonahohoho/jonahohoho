#!/usr/bin/env python3
"""
學生心得單 OCR 轉 Excel 工具
掃描學生心得單圖片/PDF，自動提取學號、姓名、成績，匯出至 Excel

使用方式:
  python ocr_to_excel.py <掃描檔資料夾> [選項]

範例:
  python ocr_to_excel.py ./scans
  python ocr_to_excel.py ./scans -o 班級成績.xlsx
  python ocr_to_excel.py ./scans --engine claude --api-key sk-ant-...
  python ocr_to_excel.py ./scans --review        # 逐一確認再存檔
"""

import os
import re
import json
import argparse
import base64
import tempfile
from pathlib import Path

# ── 依賴檢查 ──────────────────────────────────────────────────────────
try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


# ── 圖片前處理（提升 Tesseract 辨識率）─────────────────────────────────
def preprocess_image(image):
    """強化圖片對比度與清晰度，提升 OCR 準確率"""
    image = image.convert('L')  # 灰階
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    image = image.filter(ImageFilter.SHARPEN)
    return image


# ── Tesseract OCR ────────────────────────────────────────────────────
def ocr_with_tesseract(image):
    """使用 Tesseract OCR 辨識繁體中文 + 英數"""
    processed = preprocess_image(image)
    config = r'--oem 3 --psm 6 -l chi_tra+eng'
    return pytesseract.image_to_string(processed, config=config)


# ── Claude Vision OCR ────────────────────────────────────────────────
def ocr_with_claude(image_path, client):
    """使用 Claude Vision API 辨識，回傳 JSON 格式"""
    ext = Path(image_path).suffix.lower()
    mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp'}
    media_type = mime_map.get(ext, 'image/jpeg')

    with open(image_path, 'rb') as f:
        image_data = base64.standard_b64encode(f.read()).decode('utf-8')

    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": image_data}
                },
                {
                    "type": "text",
                    "text": (
                        "請仔細閱讀這份學生心得單，找出以下三個欄位，以 JSON 格式回應：\n"
                        "- student_id: 學號（通常是數字或字母+數字，例如 B12345678）\n"
                        "- name: 學生姓名（中文）\n"
                        "- score: 成績或分數（數字，0~100）\n\n"
                        "找不到的欄位請填 null。\n"
                        "只回傳 JSON，不要任何說明文字。\n"
                        "格式範例: {\"student_id\": \"B12345678\", \"name\": \"王小明\", \"score\": 85}"
                    )
                }
            ]
        }]
    )
    return response.content[0].text


# ── 文字解析（Tesseract 用）──────────────────────────────────────────
def parse_ocr_text(text):
    """從 OCR 文字中用正規表示式提取學號、姓名、成績"""
    result = {'student_id': None, 'name': None, 'score': None}

    # 學號：「學號:」後面的字母+數字組合，或純數字 7~10 碼
    id_patterns = [
        r'學\s*號\s*[：:＊*]?\s*([A-Za-z]?\d{6,10})',
        r'(?:No|ID|學號)[.．：:\s]*([A-Za-z]\d{7,9})',
        r'\b([A-Z]\d{8,9})\b',   # 字母開頭的學號
        r'\b(\d{8,10})\b',        # 純數字學號
    ]
    for pat in id_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result['student_id'] = m.group(1).strip()
            break

    # 姓名：「姓名:」後面 2~5 個中文字，或 "Name:" 後面的文字
    name_patterns = [
        r'姓\s*名\s*[：:＊*]?\s*([一-鿿]{2,5})',
        r'學生\s*[姓名]*\s*[：:]\s*([一-鿿]{2,5})',
        r'(?:Name|name)\s*[：:]\s*([一-鿿]{2,5})',  # 英文標籤
        r'(?:Name|name)\s*[：:]\s*(\S+)',            # 萬用後備
    ]
    for pat in name_patterns:
        m = re.search(pat, text)
        if m:
            result['name'] = m.group(1).strip()
            break

    # 成績：「成績/分數/得分:」後面的數字，或「XX 分」
    score_patterns = [
        r'(?:成績|分數|得分|Score)\s*[：:＊*]?\s*(\d{1,3})',
        r'(\d{1,3})\s*[分/]',
        r'[\[【（(](\d{1,3})[\]】）)]',
    ]
    for pat in score_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            s = int(m.group(1))
            if 0 <= s <= 100:
                result['score'] = s
                break

    return result


# ── 檔案處理 ──────────────────────────────────────────────────────────
def load_images_from_file(file_path):
    """將圖片或 PDF 轉為 PIL Image 列表"""
    suffix = Path(file_path).suffix.lower()
    if suffix == '.pdf':
        if not PDF_SUPPORT:
            raise RuntimeError("請安裝 pdf2image：pip install pdf2image")
        return convert_from_path(str(file_path), dpi=300)
    elif suffix in {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif'}:
        return [Image.open(str(file_path))]
    else:
        raise ValueError(f"不支援的檔案類型：{suffix}")


def process_with_tesseract(file_path):
    images = load_images_from_file(file_path)
    full_text = '\n'.join(ocr_with_tesseract(img) for img in images)
    return parse_ocr_text(full_text), full_text


def process_with_claude(file_path, client):
    suffix = Path(file_path).suffix.lower()
    temp_files = []

    if suffix == '.pdf':
        images = load_images_from_file(file_path)
        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        images[0].save(tmp.name)  # 只取第一頁
        target_path = tmp.name
        temp_files.append(tmp.name)
    else:
        target_path = str(file_path)

    try:
        raw = ocr_with_claude(target_path, client)
        try:
            data = json.loads(raw.strip())
            return {
                'student_id': data.get('student_id'),
                'name': data.get('name'),
                'score': data.get('score')
            }
        except json.JSONDecodeError:
            return parse_ocr_text(raw)
    finally:
        for f in temp_files:
            try:
                os.unlink(f)
            except OSError:
                pass


# ── Excel 輸出 ────────────────────────────────────────────────────────
def save_to_excel(records, output_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "學生成績"

    thin = Side(border_style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # 標題列
    headers = ['序號', '學號', '姓名', '成績', '來源檔案', '備註']
    header_fill = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11, name="微軟正黑體")
    center = Alignment(horizontal='center', vertical='center')

    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center
        cell.border = border

    ws.row_dimensions[1].height = 28

    # 資料列
    warn_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    ok_fills = [
        PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid"),
        PatternFill(start_color="F5F5F5", end_color="F5F5F5", fill_type="solid"),
    ]

    for idx, rec in enumerate(records, 1):
        row = idx + 1
        missing = (not rec.get('student_id') or
                   not rec.get('name') or
                   rec.get('score') is None)
        row_fill = warn_fill if missing else ok_fills[idx % 2]

        values = [
            idx,
            rec.get('student_id') or '（未識別）',
            rec.get('name') or '（未識別）',
            rec.get('score') if rec.get('score') is not None else '',
            rec.get('source_file', ''),
            rec.get('note', '⚠ 請手動確認' if missing else ''),
        ]
        for col, val in enumerate(values, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.fill = row_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center' if col in (1, 4) else 'left',
                                       vertical='center')

        ws.row_dimensions[row].height = 22

    # 欄寬
    widths = [8, 16, 12, 10, 30, 20]
    for col, w in enumerate(widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = w

    # 凍結標題列
    ws.freeze_panes = 'A2'

    wb.save(output_path)
    print(f"\n已儲存至 {output_path}")


# ── 互動確認 ──────────────────────────────────────────────────────────
def interactive_review(info, filename):
    """讓使用者逐一確認並修正辨識結果"""
    print(f"\n  --- 請確認 {filename} 的辨識結果 ---")

    for field, label in [('student_id', '學號'), ('name', '姓名'), ('score', '成績')]:
        current = info.get(field)
        display = current if current is not None else '（未識別）'
        new_val = input(f"  {label} [{display}]（按 Enter 保留）: ").strip()
        if new_val:
            if field == 'score':
                try:
                    info[field] = int(new_val)
                except ValueError:
                    info[field] = new_val
            else:
                info[field] = new_val
    return info


# ── 主程式 ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description='學生心得單 OCR 轉 Excel 工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('input_folder', help='含掃描檔案的資料夾路徑')
    parser.add_argument('-o', '--output', default='學生成績.xlsx',
                        help='輸出 Excel 檔名（預設：學生成績.xlsx）')
    parser.add_argument('--engine', choices=['tesseract', 'claude'], default='tesseract',
                        help='OCR 引擎（tesseract=免費本機；claude=更準確，需 API Key）')
    parser.add_argument('--api-key', default=None,
                        help='Anthropic API Key（engine=claude 時使用，或設 ANTHROPIC_API_KEY 環境變數）')
    parser.add_argument('--review', action='store_true',
                        help='逐一手動確認每筆辨識結果再存檔')
    args = parser.parse_args()

    # 確認 Excel 套件
    if not EXCEL_AVAILABLE:
        print("請先安裝 openpyxl：pip install openpyxl")
        return

    # 確認輸入資料夾
    folder = Path(args.input_folder)
    if not folder.exists():
        print(f"找不到資料夾：{folder}")
        return

    exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.pdf'}
    files = sorted(f for f in folder.iterdir() if f.suffix.lower() in exts)
    if not files:
        print(f"在 {folder} 中找不到圖片或 PDF 檔案")
        return

    print(f"找到 {len(files)} 個檔案，開始處理...\n")

    # 初始化 OCR 引擎
    client = None
    if args.engine == 'claude':
        if not CLAUDE_AVAILABLE:
            print("請先安裝 anthropic：pip install anthropic")
            return
        api_key = args.api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            print("請提供 API Key（--api-key 參數或設定 ANTHROPIC_API_KEY 環境變數）")
            return
        client = anthropic.Anthropic(api_key=api_key)
        print("OCR 引擎：Claude Vision API\n")
    else:
        if not TESSERACT_AVAILABLE:
            print("請先安裝 pytesseract 與 Pillow：pip install pytesseract Pillow")
            print("並安裝 Tesseract（含繁體中文語言包 chi_tra）")
            return
        print("OCR 引擎：Tesseract（請確認已安裝繁體中文語言包 chi_tra）\n")

    # 逐檔處理
    records = []
    for i, fp in enumerate(files, 1):
        print(f"[{i:>3}/{len(files)}] {fp.name}", end='  ', flush=True)
        try:
            if args.engine == 'claude':
                info = process_with_claude(fp, client)
            else:
                info, _ = process_with_tesseract(fp)

            info['source_file'] = fp.name

            sid = info.get('student_id') or '?'
            name = info.get('name') or '?'
            score = info.get('score') if info.get('score') is not None else '?'
            print(f"學號:{sid}  姓名:{name}  成績:{score}")

            if args.review:
                info = interactive_review(info, fp.name)

        except Exception as e:
            print(f"[錯誤] {e}")
            info = {
                'student_id': None,
                'name': None,
                'score': None,
                'source_file': fp.name,
                'note': f'處理失敗：{e}',
            }

        records.append(info)

    # 統計
    total = len(records)
    ok = sum(1 for r in records
             if r.get('student_id') and r.get('name') and r.get('score') is not None)
    print(f"\n{'─'*50}")
    print(f"處理完成：{total} 筆  |  完整辨識：{ok} 筆  |  需確認：{total - ok} 筆（Excel 中以黃色標示）")

    save_to_excel(records, args.output)


if __name__ == '__main__':
    main()
