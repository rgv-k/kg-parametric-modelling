import fitz
import pytesseract
from PIL import Image
import io
import sys
import json
import re
from tqdm import tqdm
import os

def clean_text(text):
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def ocr_page(page):
    pix = page.get_pixmap(dpi=300)
    img_data = pix.tobytes("png")
    image = Image.open(io.BytesIO(img_data))
    return pytesseract.image_to_string(image, lang='eng')

def process_pdf(pdf_path):
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_file = f"data/ocr/{base_name}_text.json"

    os.makedirs("data/ocr", exist_ok=True)

    doc = fitz.open(pdf_path)
    results = []

    for page_num in tqdm(range(len(doc)), desc="OCR Processing"):
        page = doc.load_page(page_num)
        text = ocr_page(page)

        if text.strip():
            results.append({
                "source_pdf": base_name,
                "source_page": page_num + 1,
                "text": clean_text(text)
            })

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"OCR saved → {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ocr_extract.py <input_pdf>")
        sys.exit(1)

    process_pdf(sys.argv[1])