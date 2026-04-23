import json
import os
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import sys
load_dotenv()
os.makedirs("outputs/geometry", exist_ok=True)
os.makedirs("outputs/profile", exist_ok=True)
llm = ChatOpenAI(
    openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    model="deepseek/deepseek-v3.2",
    temperature=0,
    max_tokens=5000,
)
def safe_parse(text):
    try:
        return json.loads(text)
    except:
        cleaned = re.sub(r"```json|```", "", text).strip()
        try:
            return json.loads(cleaned)
        except:
            print("\nJSON ERROR:\n", text)
            return None
PROMPT = """
You are a deterministic parametric system builder.
INPUT:
- Component
- Structural elements
- Measurements
- Context
---
GOAL:
Construct a COMPLETE, ORDERED, and CONSISTENT parametric system.
---
STRICT RULES (MANDATORY):
1. FILTER STRUCTURE:
- Keep ONLY elements physically part of the component
- REMOVE external elements (doors, windows, towers, etc.)
---
2. STRUCTURE TYPE:
Determine structure type:
- vertical_stack
- radial
- planar
- modular
---
3. PRIMARY DIMENSION:
- Based on structure type (NOT frequency)
- vertical_stack → height
- radial → radius/diameter
- planar → width/length
---
4. ORDERING (CRITICAL):
- If structure is sequential (like vertical_stack),
  assign ORDER to each subcomponent
- Order must reflect physical stacking (bottom → top)
---
5. COMPLETENESS:
- EVERY subcomponent MUST have at least one parameter
- NO empty parameter objects
---
6. PARAMETER ASSIGNMENT:
- Use explicit values if available
- Otherwise infer logically
---
7. GLOBAL CONSTRAINT (MANDATORY):
- If vertical_stack:
    Sum of ALL height ratios MUST equal EXACTLY 1.0
- Adjust proportionally if needed
---
8. DERIVED PARAMETERS:
- Define relationships between:
    width, height, diameter, module
- Ensure consistency (no disconnected references)
---
9. MICRO COMPONENTS:
- Identify small joinery/details (peg, tenon, etc.)
- DO NOT include them in main structure
- Place them under "micro_components"
---
OUTPUT FORMAT:
{
  "component": "",
  "structure_type": "",
  "reference": {
    "primary_dimension": "",
    "normalized_value": 1.0
  },
  "derived_parameters": {
    "<param>": {
      "ratio": float,
      "relative_to": ""
    }
  },
  "subcomponents": [
    {
      "name": "",
      "order": int,
      "parameters": {
        "<dimension>": {
          "ratio": float,
          "relative_to": ""
        }
      },
      "source": "explicit | inferred"
    }
  ],
  "micro_components": [
    {
      "name": "",
      "parameters": {
        "<dimension>": {
          "ratio": float,
          "relative_to": ""
        }
      }
    }
  ]
}
"""

def clean_structure(structure):
    seen = set()
    cleaned = []

    for s in structure:
        key = s.lower().strip()
        if key not in seen:
            seen.add(key)
            cleaned.append(s)

    return cleaned


def save_geometry(component, data):
    path = f"outputs/geometry/{component}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Geometry saved → {path}")



def build_geometry(component):
    with open(f"split_outputs/{component}_geometry.json", "r", encoding="utf-8") as f:
        geometry = json.load(f)

    with open(f"split_outputs/{component}_semantics.json", "r", encoding="utf-8") as f:
        semantics = json.load(f)

    data = {
        "component": component,
        "structure": geometry.get("structure", []),
        "measurements": geometry.get("measurements", []),
        "context": semantics.get("contextual_info", [])
    }
    data["structure"] = clean_structure(data["structure"])
    prompt = f"Data:\n{json.dumps(data)}"

    res = llm.invoke([
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": prompt}
    ])

    return safe_parse(res.content)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        component = sys.argv[1]
    else:
        component = input("Component: ")

    result = build_geometry(component)

    if result:
        save_geometry(component, result)
        print(json.dumps(result, indent=2))