import os
import json
import time
import re
import glob
from dotenv import load_dotenv
from tqdm import tqdm
from langchain_openai import ChatOpenAI
load_dotenv()
client = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    model=os.getenv("MODEL_NAME"),
    temperature=0,
    max_tokens=6000
)
INPUT_DIR = "data/ocr"
OUTPUT_DIR = "data/parsed"
LOG_FILE = "llm_logs/llm_trace.log"
os.makedirs(OUTPUT_DIR, exist_ok=True)
SYSTEM_PROMPT = """
You are a linguistic parser specializing in ancient Sanskrit architectural texts.
Your task is to read OCR'd English translation text from the Mayamata and extract structured verses.
RULES:
1. Match each verse number (e.g., "1", "3-6a", "11b-12") to its corresponding MAIN TEXT ONLY.
2. IGNORE ALL FOOTNOTES (patterns like "1.", "2.", etc.)
3. DO NOT include references or commentary
4. DO NOT hallucinate
5. Preserve meaning exactly
6. Ensure continuity of verse numbers (e.g., if "1-4a" is present, "4b" should follow if it exists)
7. If a verse is split across pages, combine it into one entry.
OUTPUT FORMAT (STRICT JSON ONLY):
{
  "verses": [
    {
      "verse": "1-4a",
      "text": "Clean verse text"
    },
    {
      "verse": "4b-8",
      "text": "Another verse text"
    }
  ]
}
"""

# --- LLM CALL WITH RETRY ---
def safe_generate(prompt, retries=3):
    for attempt in range(retries):
        try:
            response = client.invoke([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ])
            return response.content

        except Exception as e:
            print(f"Retry {attempt+1}: {e}")
            time.sleep(3 * (attempt + 1))

    return None

# --- LOGGING ---
def log_interaction(input_text, output_text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n--- NEW ENTRY ---\n")
        f.write("INPUT:\n" + input_text + "\n\n")
        f.write("OUTPUT:\n" + str(output_text) + "\n")

# --- CLEANING ---
def remove_footnotes(text):
    return re.sub(r"\b\d+\.\s.*", "", text)

# --- VALIDATION ---
def validate_verses(verses):
    valid = []

    for v in verses:
        if not isinstance(v, dict):
            continue

        if "verse" not in v or "text" not in v:
            continue

        text = remove_footnotes(v["text"].strip())

        if len(text) < 20:
            continue

        valid.append({
            "verse": v["verse"],
            "text": text
        })

    return valid

# --- PARSER ---
def parse_page_text(page_text):
    prompt = f"TEXT:\n{page_text}"

    response_text = safe_generate(prompt)

    if not response_text:
        return None

    log_interaction(page_text, response_text)

    try:
        parsed = json.loads(response_text)
        verses = parsed.get("verses", [])
        return validate_verses(verses)

    except Exception as e:
        print(f"JSON parse error: {e}")
        return None

# --- BATCH PROCESSING ---
def run_full_batch_parse(input_directory, output_directory):
    files = glob.glob(os.path.join(input_directory, "*_text.json"))

    if not files:
        print("No input files found.")
        return

    print(f"Found {len(files)} files.")

    for file_path in tqdm(files, desc="Processing Files", unit="file"):
        base_name = os.path.basename(file_path)
        output_name = base_name.replace("_text.json", "_parsed.json")
        output_path = os.path.join(output_directory, output_name)

        # Skip already processed
        if os.path.exists(output_path):
            tqdm.write(f"Skipping {base_name}")
            continue

        # Load file
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            tqdm.write(f"Error loading {base_name}: {e}")
            continue

        all_verses = []

        for page in data:
            page_text = page.get("text", "")
            page_num = page.get("source_page", None)

            verses = parse_page_text(page_text)

            if verses:
                for v in verses:
                    v["source_page"] = page_num
                all_verses.extend(verses)

        # Save
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"verses": all_verses}, f, indent=2, ensure_ascii=False)

        tqdm.write(f"Saved {output_name} ({len(all_verses)} verses)")

    print("\n--- ALL FILES PROCESSED ---")

# --- RUN ---
if __name__ == "__main__":
    run_full_batch_parse(INPUT_DIR, OUTPUT_DIR)