import os
import json
import glob
INPUT_PATTERN = "data/glossary_clean/GLOSSARY_BATCH_*_CLEAN.json"
OUTPUT_FILE = "data/glossary_final/GLOSSARY_FINAL.json"
os.makedirs("data/glossary_final", exist_ok=True)
def main():
    files = sorted(glob.glob(INPUT_PATTERN))
    if not files:
        print("No cleaned glossary files found.")
        return
    combined = {}
    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for entry in data:
            term = entry.get("term")
            entries = entry.get("entries", [])
            if not term:
                continue
            if term not in combined:
                combined[term] = {
                    "term": term,
                    "entries": []
                }
            combined[term]["entries"].extend(entries)
    final_output = list(combined.values())
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)
    print(f"Saved combined glossary to {OUTPUT_FILE}")
if __name__ == "__main__":
    main()