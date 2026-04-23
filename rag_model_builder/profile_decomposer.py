import json
import os
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import time
import sys
os.makedirs("outputs/geometry", exist_ok=True)
os.makedirs("outputs/profile", exist_ok=True)
load_dotenv()
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
            print("JSON ERROR:\n", text)
            return None
def safe_save_profile(component, data, base_dir="outputs/profile", versioned=False):
    if not data or "profile" not in data:
        print("Invalid profile data. Not saving.")
        return
    os.makedirs(base_dir, exist_ok=True)
    if versioned:
        timestamp = int(time.time())
        filename = f"{component}_{timestamp}.json"
    else:
        filename = f"{component}.json"
    path = os.path.join(base_dir, filename)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Profile saved → {path}")
    except Exception as e:
        print(f"Failed to save profile: {e}")
PROMPT = """
You are a geometric decomposition engine.
INPUT:
A parametric architectural system.
GOAL:
Convert each subcomponent into fundamental geometric primitives.
---
PRIMITIVE TYPES:
- line
- arc (convex or concave)
- sigmoid (smooth S-curve)
- circle_segment
- rectangle
- taper
- extrusion
---
RULES:
1. Each subcomponent MUST be broken into segments
2. Each segment must have:
   - type
   - relative size (normalized)
3. Use ONLY primitives listed above
4. DO NOT invent arbitrary shapes
5. DO NOT skip components
6. Maintain order
---
OUTPUT FORMAT:
{
  "component": "",
  "profile": [
    {
      "name": "",
      "order": int,
      "segments": [
        {
          "type": "",
          "size": float
        }
      ]
    }
  ]
}
"""

def decompose(component):
    with open(f"outputs/geometry/{component}.json", "r", encoding="utf-8") as f:
        data = json.load(f)

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

    result = decompose(component)

    if result:
        print(json.dumps(result, indent=2))
        safe_save_profile(component, result)