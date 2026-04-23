import os
import json
import time
from dotenv import load_dotenv
from tqdm import tqdm
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
load_dotenv()
model = ChatOpenAI(
    openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    model=os.getenv("MODEL_NAME"),
    temperature=0
)
INPUT_FILE = "data/glossary_final/GLOSSARY_FINAL.json"
OUTPUT_FILE = "data/nodes/KG_NODES_FULL.json"
PARTIAL_FILE = "data/nodes/KG_NODES_PARTIAL.json"
BATCH_SIZE = 20
SYSTEM_PROMPT = """
You are an expert architect and data scientist building a Knowledge Graph for the "Mayamata" (an ancient Indian architectural text).
Your goal is to extract structured entities and attributes from glossary terms to support procedural 3D modeling in Blender.
**INPUT:** A JSON list of glossary terms and their definitions.
**OUTPUT:** A JSON list of "Entity Objects".
**RULES FOR EXTRACTION:**
1.  **Analyze the Term:** Read the term and its definition carefully.
2.  **Determine Category:** Classify the term into one of these categories:
    -   `ARCHITECTURAL_ELEMENT` (e.g., pillar, base, window, door)
    -   `BUILDING_TYPE` (e.g., temple, pavilion, storeyed-building)
    -   `MEASUREMENT` (e.g., cubit, digit, span)
    -   `MATERIAL` (e.g., brick, stone, wood)
    -   `RITUAL` (e.g., foundation deposit, consecration)
    -   `DEITY` (e.g., Brahma, Shiva - relevant for placement rules)
    -   `ABSTRACT_CONCEPT` (e.g., gain, loss, asterism)
    -   `UNKNOWN` (if unclear)
3.  **Extract Attributes:** Extract key properties mentioned in the text.
    -   *Example:* If def is "Square pillar type", properties: {"shape": "square", "is_a": "pillar"}
4.  **Handle Polysemy:** If a term has multiple distinct meanings (numbered 1, 2, 3...), create a SEPARATE entity for each meaning with a unique ID (e.g., `term_1`, `term_2`).
**JSON OUTPUT FORMAT:**
Return ONLY a JSON list. Format:
[
  {
    "id": "unique_id_for_graph",
    "term": "original_term_name",
    "category": "CATEGORY_NAME",
    "definition_summary": "Short summary of what it is",
    "attributes": {
      "shape": "...",
      "parent_type": "...", 
      "associated_with": "..."
    }
  }
]
"""

def process_batch(batch):
    """Sends a batch of terms to the LLM for extraction."""
    import re
    batch_text = json.dumps(batch, ensure_ascii=False)
    try:
        response = model.invoke(
            f"{SYSTEM_PROMPT}\n\nINPUT:\n{batch_text}"
        )
        raw_output = response.content.strip()
        if not raw_output:
            print("Empty response from model")
            return []
        if "```" in raw_output:
            raw_output = raw_output.split("```")[1]
            if raw_output.startswith("json"):
                raw_output = raw_output[4:]
        raw_output = raw_output.strip()
        match = re.search(r"\[\s*{.*}\s*\]", raw_output, re.DOTALL)
        if not match:
            print("No valid JSON found in response")
            print("Raw output:", raw_output[:500])
            return []
        clean_json = match.group(0)
        return json.loads(clean_json)
    except Exception as e:
        print(f"\nError processing batch: {e}")
        print("Retrying in 5 seconds...")
        time.sleep(5)
        try:
            response = model.invoke(
                f"{SYSTEM_PROMPT}\n\nINPUT:\n{batch_text}"
            )
            raw_output = response.content.strip()
            if not raw_output:
                return []
            if "```" in raw_output:
                raw_output = raw_output.split("```")[1]
                if raw_output.startswith("json"):
                    raw_output = raw_output[4:]
            raw_output = raw_output.strip()
            match = re.search(r"\[\s*{.*}\s*\]", raw_output, re.DOTALL)
            if not match:
                print("Retry failed: No valid JSON found")
                return []
            clean_json = match.group(0)
            return json.loads(clean_json)
        except Exception as e:
            print("Retry failed:", e)
            return []
def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Please make sure '{INPUT_FILE}' is in this folder.")
        return
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        glossary_data = json.load(f)
    total_terms = len(glossary_data)
    all_nodes = []
    start_index = 0
    if os.path.exists(PARTIAL_FILE):
        print(f"Found checkpoint file '{PARTIAL_FILE}'. Resuming...")
        try:
            with open(PARTIAL_FILE, 'r', encoding='utf-8') as f:
                all_nodes = json.load(f)
            if all_nodes:
                last_term = all_nodes[-1]['term']
                for i, item in enumerate(glossary_data):
                    if item['term'] == last_term:
                        start_index = i + 1
                        break
                print(f"Resuming from index {start_index} (Term: {glossary_data[start_index]['term']})")
        except Exception as e:
            print(f"Error reading partial file: {e}. Starting from scratch.")
            all_nodes = []
            start_index = 0
    print(f"Processing {total_terms - start_index} remaining terms...")
    for i in tqdm(range(start_index, total_terms, BATCH_SIZE), desc="Extracting Nodes"):
        batch = glossary_data[i : i + BATCH_SIZE]
        if i > start_index: # Don't sleep on the very first batch of the run
            time.sleep(1) 
        nodes = process_batch(batch)
        if nodes:
            all_nodes.extend(nodes)
        with open(PARTIAL_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_nodes, f, indent=2, ensure_ascii=False)
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_nodes, f, indent=2, ensure_ascii=False)
        print(f"\n---  Phase 1 Complete! ---")
        print(f"Extracted {len(all_nodes)} nodes.")
        print(f"Saved to '{OUTPUT_FILE}'.")
    except Exception as e:
        print(f"Error saving output: {e}")
if __name__ == "__main__":
    main()