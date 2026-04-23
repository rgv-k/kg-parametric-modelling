import fitz  # PyMuPDF
import os
import io
import json
import re
from PIL import Image
from dotenv import load_dotenv
from tqdm import tqdm
import time
import pytesseract
load_dotenv()
INPUT_PDF = "glossary_pages.pdf"
OUTPUT_DIR = "data/glossary_batches"
BATCH_SIZE = 10
os.makedirs(OUTPUT_DIR, exist_ok=True)
def parse_glossary_text(text):
    text = re.sub(r"^\d+\s*\n", "", text, flags=re.MULTILINE) 
    text = re.sub(r"INDEX-GLOSSARY\n", "", text)
    text = re.sub(r"-references to chapters and verses\.\n", "", text)
    text = re.sub(r"abbreviation 'g.' .*\n", "", text)
    text = re.sub(r"-identification of trees .*\n", "", text)
    term_regex = re.compile(
        r"^(?P<term>[\wāīūṛḍñṇśṣţṁ\-]+:)"
        r"(?P<entries>[\s\S]+?)"
        r"(?=\n[\wāīūṛḍñṇśṣţṁ\-]+:|\Z)",
        re.MULTILINE | re.IGNORECASE
    )
    glossary_list = []
    print("Parsing extracted text with v6 logic...")
    for match in tqdm(term_regex.finditer(text), desc="Parsing Terms"):
        term_name = match.group("term").replace(":", "").strip()
        entries_text = match.group("entries").strip().replace("\n", " ")
        entries_text = re.sub(r"\s+", " ", entries_text).strip()
        if entries_text.startswith("="):
            entries_text = entries_text.lstrip("= ").strip()
        if entries_text.lstrip().startswith("1. "):
            entries_text = entries_text.lstrip()[3:].strip()
        glossary_list.append({
            "term": term_name,
            "entries": [
                {
                    "definition_text": entries_text
                }
            ]
        })
    return glossary_list
def ocr_page(page):
    pix = page.get_pixmap(dpi=300)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    text = pytesseract.image_to_string(img, lang='eng')
    return text
def main():
    if not os.path.exists(INPUT_PDF):
        print(f"Error")
        print(f"Input PDF not found: '{INPUT_PDF}'")
        return
    doc = fitz.open(INPUT_PDF)
    total_pages = len(doc)
    print(f"Total glossary pages: {total_pages}")
    batch_number = 1
    for start in range(0, total_pages, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total_pages)
        print(f"\nProcessing Batch {batch_number}: Pages {start+1}-{end}")
        full_text = ""
        for page_num in tqdm(range(start, end), desc=f"Batch {batch_number}", unit="page"):
            try:
                page = doc.load_page(page_num)
                text = ocr_page(page)
                full_text += text + "\n"
            except Exception as e:
                tqdm.write(f"Error on page {page_num + 1}: {e}")
                time.sleep(1)
        glossary_data = parse_glossary_text(full_text)
        output_path = f"{OUTPUT_DIR}/GLOSSARY_BATCH_{batch_number}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(glossary_data, f, indent=2, ensure_ascii=False)
        print(f"Saved: {output_path}")
        batch_number += 1
    doc.close()
    print("\nALL GLOSSARY BATCHES COMPLETE")
if __name__ == "__main__":
    main()