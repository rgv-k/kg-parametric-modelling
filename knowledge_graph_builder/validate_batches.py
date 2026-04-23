import os
import json
import glob
import time
from dotenv import load_dotenv
from tqdm import tqdm
from openai import OpenAI
load_dotenv()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)
INPUT_PATTERN = "data/glossary_batches/GLOSSARY_BATCH_*.json"
OUTPUT_DIR = "data/glossary_clean"
os.makedirs(OUTPUT_DIR, exist_ok=True)
MODEL = os.getenv("MODEL_NAME")


SYSTEM_PROMPT = """
You are a meticulous data validation agent. You will receive a JSON string that is the
output of an OCR process on a Sanskrit glossary. This JSON is a list of terms, but it
may contain "junk" entries from the OCR process.
Your task is to clean and refine this JSON.
**RULES:**
1.  **Parse the entire JSON list.**
2.  **Identify and DELETE any "junk" entries.** A junk entry is an object whose "term"
    is clearly not a real word.
    -   **DELETE** entries where the "term" is just a page number (e.g., "914", "920", "933").
    -   **DELETE** entries where the "term" is just a single letter (e.g., "K", "E", "M", "S").
    -   **DELETE** entries where the "term" is a header like "INDEX-GLOSSARY".
3.  **Clean definition text:** Remove any stray page numbers or headers (like "INDEX-GLOSSARY 925")
    from the middle or end of the `definition_text` fields.
4.  **Ensure perfect JSON:** The final output must be ONLY the corrected, valid JSON list,
    starting with `[` and ending with `]`. Do not add any explanatory text.
"""


def safe_generate(prompt, retries=3):
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"Retry {attempt+1} due to error: {e}")
            time.sleep(5 * (attempt + 1))

    return None



def extract_json(text):
    if not text:
        return None

    text = text.replace("```json", "").replace("```", "").strip()

    start = text.find("[")
    end = text.rfind("]") + 1

    if start != -1 and end != -1:
        return text[start:end]

    return None

def process_file(file_path):

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    prompt = json.dumps(data, ensure_ascii=False)

    output = safe_generate(prompt)

    if not output:
        return None

    json_str = extract_json(output)

    if not json_str:
        print("JSON extraction failed")
        return None

    try:
        cleaned = json.loads(json_str)
        return cleaned
    except Exception as e:
        print("JSON parsing error:", e)
        return None



def main():

    files = glob.glob(INPUT_PATTERN)

    if not files:
        print("No glossary batch files found.")
        return

    for file_path in tqdm(files, desc="Validating Batches"):
        base_name = os.path.basename(file_path)
        output_name = base_name.replace(".json", "_CLEAN.json")
        output_path = os.path.join(OUTPUT_DIR, output_name)

        if os.path.exists(output_path):
            print(f"Skipping {base_name}")
            continue

        cleaned_data = process_file(file_path)

        if not cleaned_data:
            print(f"Failed: {base_name}")
            continue

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

        print(f"Saved: {output_path}")

    print("\nALL BATCHES VALIDATED")


if __name__ == "__main__":
    main()