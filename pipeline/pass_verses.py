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
    model="anthropic/claude-3-haiku",
    temperature=0
)

INPUT_DIR = "data/ocr"
OUTPUT_DIR = "data/parsed"
LOG_FILE = "llm_trace.log"

os.makedirs(OUTPUT_DIR, exist_ok=True)




SYSTEM_PROMPT = """
You are a linguistic parser specializing in ancient Sanskrit architectural texts.

Your task is to read OCR'd English translation text from the Mayamata and extract structured verses.

RULES:
1. Match each verse number (e.g., "1", "3-6a", "11b-12") to its corresponding MAIN TEXT ONLY.
2. IGNORE ALL FOOTNOTES. Footnotes typically start with patterns like "1.", "2.", etc.
3. DO NOT include references, citations, or commentary.
4. DO NOT hallucinate verses.
5. Preserve the exact meaning of the text.

OUTPUT FORMAT (STRICT JSON ONLY):
{
  "verses": [
    {
      "verse": "1-4a",
      "text": "Clean verse text"
    }
  ]
}
"""



def safe_generate(prompt, retries=3):
    for attempt in range(retries):
        try:
            response = client.invoke([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ])

            return response.content

        except Exception as e:
            print(f"Retry {attempt+1} due to error: {e}")
            time.sleep(5 * (attempt + 1))

    return None


def log_interaction(input_text, output_text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n--- NEW ENTRY ---\n")
        f.write("INPUT:\n" + input_text + "\n\n")
        f.write("OUTPUT:\n" + str(output_text) + "\n")


def remove_footnotes_llm(text):
    return re.sub(r"\b\d+\.\s.*", "", text)


def validate_verses(verses):
    valid = []

    for v in verses:
        if not isinstance(v, dict):
            continue

        if "verse" not in v or "text" not in v:
            continue

        text = v["text"].strip()
        text = remove_footnotes_llm(text)

        if len(text) < 20:
            continue

        valid.append({
            "verse": v["verse"],
            "text": text
        })

    return valid




def parse_page_text(page_text):
    prompt = f"TEXT:\n{page_text}"

    response_text = safe_generate(prompt)

    if not response_text:
        return None

    log_interaction(page_text, response_text)

    try:
        parsed_data = json.loads(response_text)
        verses = parsed_data.get("verses", [])
        verses = validate_verses(verses)
        return verses

    except Exception as e:
        print("JSON parsing failed:", e)
        return None




def run_full_batch_parse(input_directory, output_directory):

    files = glob.glob(os.path.join(input_directory, "*_text.json"))

    if not files:
        print("No input files found.")
        return

    for file_path in tqdm(files, desc="Processing Files"):
        base_name = os.path.basename(file_path)
        output_name = base_name.replace("_text.json", "_parsed.json")
        output_path = os.path.join(output_directory, output_name)

        if os.path.exists(output_path):
            tqdm.write(f"Skipping {base_name}")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        all_verses = []

        for page in tqdm(data, desc=f"Parsing {base_name}", leave=False):
            page_text = page["text"]
            page_num = page["source_page"]

            verses = parse_page_text(page_text)

            if verses:
                for v in verses:
                    v["source_page"] = page_num
                all_verses.extend(verses)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"verses": all_verses}, f, indent=2, ensure_ascii=False)

        tqdm.write(f"Saved: {output_name} ({len(all_verses)} verses)")

    print("\n--- ALL FILES PROCESSED ---")


# --- 6. RUN ---

if __name__ == "__main__":
    run_full_batch_parse(INPUT_DIR, OUTPUT_DIR)