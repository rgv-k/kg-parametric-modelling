import os
import json
from glob import glob
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import re
load_dotenv()
INPUT_DIR = "rag_outputs"
OUTPUT_DIR = "split_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
llm = ChatOpenAI(
    openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    model=os.getenv("MODEL_NAME"),
    temperature=0,
    max_tokens=6000
)
SPLIT_PROMPT = """
You are a deterministic data classification engine.
You MUST follow rules exactly.
---
INPUT:
Structured architectural knowledge.
---
TASK:
Split the data into 4 categories.
---
DEFINITIONS (STRICT):
1. GEOMETRY:
   Include ONLY:
   - Physical parts of the component
   - Structural hierarchy elements
   - Measurements that DEFINE the component itself or its parts
2. MATERIALS:
   Include ONLY:
   - Materials (wood, stone, etc.)
3. SEMANTICS:
   Include:
   - Variants / types
   - Contextual rules
   - Descriptive or symbolic info
   - Measurements NOT defining the component itself
4. RELATIONSHIPS:
   Include:
   - Functional roles
   - Structural descriptions
   - System-level constraints
---
DECISION RULES (MANDATORY):
For EACH item:
- If it is a PHYSICAL PART → geometry.structure
- If it is a DIMENSION OF THE COMPONENT → geometry.measurements
- If it is a DIMENSION OF ANOTHER OBJECT → semantics
- If it is MATERIAL → materials
- If it is TYPE/VARIANT → semantics.variants
- If it is CONTEXT → semantics.contextual_info
- If it describes FUNCTION → relationships
---
CONFLICT RESOLUTION:
If unsure:
- DO NOT guess
- Place in semantics.contextual_info
---
FORBIDDEN:
- Do NOT invent
- Do NOT drop data
- Do NOT duplicate entries
- Do NOT rewrite meaning
---
OUTPUT FORMAT (STRICT):
{
  "geometry": {
    "structure": [],
    "measurements": []
  },
  "materials": [],
  "semantics": {
    "variants": [],
    "contextual_info": []
  },
  "relationships": []
}
"""

VALIDATION_PROMPT = """
You are a strict validator.

Check the output for:

1. Missing data
2. Misclassification
3. Duplicates
4. Violations of rules

Fix ONLY if necessary.

Return corrected JSON ONLY.
"""
def safe_json_parse(text):
    try:
        return json.loads(text)
    except:
        cleaned = re.sub(r"```json|```", "", text).strip()
        try:
            return json.loads(cleaned)
        except:
            print("\nSTILL INVALID JSON:\n", text)
            return None
def call_llm(system_prompt, data):
    prompt = f"Data:\n{json.dumps(data)}"
    res = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ])
    try:
        return safe_json_parse(res.content)
    except:
        print("\nJSON ERROR:\n", res.content)
        return None
def save_split(component, split_data):
    base = os.path.join(OUTPUT_DIR, component)
    with open(base + "_geometry.json", "w", encoding="utf-8") as f:
        json.dump(split_data["geometry"], f, indent=2, ensure_ascii=False)
    with open(base + "_materials.json", "w", encoding="utf-8") as f:
        json.dump(split_data["materials"], f, indent=2, ensure_ascii=False)
    with open(base + "_semantics.json", "w", encoding="utf-8") as f:
        json.dump(split_data["semantics"], f, indent=2, ensure_ascii=False)
    with open(base + "_relationships.json", "w", encoding="utf-8") as f:
        json.dump(split_data["relationships"], f, indent=2, ensure_ascii=False)
    print(f" Saved: {component}")
def process_file(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    component = data.get("component", "unknown")
    print(f"\nProcessing: {component}")
    split_data = call_llm(SPLIT_PROMPT, data)
    if not split_data:
        return
    validated = call_llm(VALIDATION_PROMPT, split_data)
    if not validated:
        return
    save_split(component, validated)
if __name__ == "__main__":
    files = glob(os.path.join(INPUT_DIR, "roof_*.json"))
    if not files:
        print("No RAG outputs found")
        exit()
    print(f"Found {len(files)} files")
    for file in files:
        process_file(file)
