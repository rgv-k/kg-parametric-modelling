import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(
    openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    model="deepseek/deepseek-v3.2",
    temperature=0,
    max_tokens=2500,
)

def load_profile(component):
    with open(f"outputs/profile/{component}.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_semantics(component):
    path = f"outputs/semantics/{component}.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"note": "no semantic data available"}

def classify_geometry(component):
    name = component.lower()

    if any(k in name for k in ["pillar", "stambha", "linga", "shikhara"]):
        return "revolve"

    if any(k in name for k in ["base", "adhisthana", "plinth", "roof", "prastara", "wall"]):
        return "extrude"

    if any(k in name for k in ["garbha", "griha", "mandapa", "temple"]):
        return "volumetric"

    return "extrude"


REVOLVE_PROMPT = """
You are generating Blender Python code for a REVOLVE geometry.

STRICT RULES:

- MUST define PROFILE
- MUST loop through PROFILE
- MUST use seg["size"]
- MUST use SCREW modifier
- DO NOT use cubes

STEPS:

1. Create curve
2. Add bezier points using PROFILE heights
3. Convert to mesh
4. Apply SCREW modifier

INPUT:
{profile}

OUTPUT:
ONLY Python code
"""

EXTRUDE_PROMPT = """
You are generating Blender Python code for an EXTRUDE geometry.

RULES:

- MUST define PROFILE
- MUST loop through PROFILE
- MUST use seg["size"]

- Build geometry vertically using cubes
- Use scaling to vary width

SPECIAL CASE: ROOF

If component is roof/prastara:
- create a wide slab
- low height
- slightly larger than below

FORBIDDEN:
- NO boolean
- NO hollow structures

INPUT:
{profile}

OUTPUT:
ONLY Python code
"""

VOLUMETRIC_PROMPT = """
You are generating Blender Python code for a VOLUMETRIC structure.

RULES:

- DO NOT loop over PROFILE directly
- Use PROFILE only for proportions

- Create:
  base (wide)
  wall (vertical)
  top (smaller/tapered)

- Use cubes + scaling

FORBIDDEN:
- NO boolean
- NO hollow geometry
- NO cube stacking

INPUT:
{profile}
{semantics}

OUTPUT:
ONLY Python code
"""

def generate_script(component, profile, semantics, geometry):

    if geometry == "revolve":
        prompt = REVOLVE_PROMPT.format(
            profile=json.dumps(profile["profile"], indent=2)
        )

    elif geometry == "extrude":
        prompt = EXTRUDE_PROMPT.format(
            profile=json.dumps(profile["profile"], indent=2)
        )

    else:
        prompt = VOLUMETRIC_PROMPT.format(
            profile=json.dumps(profile, indent=2),
            semantics=json.dumps(semantics, indent=2)
        )

    res = llm.invoke([
        {"role": "system", "content": "You must strictly follow instructions."},
        {"role": "user", "content": prompt}
    ])

    return res.content

def validate_script(script, geometry):

    errors = []

    if geometry == "revolve":
        if "SCREW" not in script.upper():
            errors.append("missing revolve (screw)")

        if "for" not in script:
            errors.append("missing loop")

    if geometry == "extrude":
        if "primitive_cube_add" not in script:
            errors.append("missing extrusion cubes")

    if geometry == "volumetric":
        if script.count("primitive_cube_add") > 5:
            errors.append("cube stacking")

    if "BOOLEAN" in script.upper():
        errors.append("boolean not allowed")

    if "difference" in script.lower():
        errors.append("subtraction detected")

    if len(script) < 200:
        errors.append("script too short")

    if errors:
        print("\nVALIDATION FAILED:")
        for e in errors:
            print(e)
        return False

    return True

def save_script(component, script):
    os.makedirs("generated_scripts", exist_ok=True)
    path = f"generated_scripts/{component}.py"

    with open(path, "w", encoding="utf-8") as f:
        f.write(script)

    print(f"\nSaved → {path}")

if __name__ == "__main__":

    component = input("Component: ").strip()

    print("\n🔹 Loading data...")
    profile = load_profile(component)
    semantics = load_semantics(component)

    geometry = classify_geometry(component)
    print(f"🔹 Geometry type: {geometry}")

    print("\nGenerating Blender scrip")

    max_attempts = 3

    for attempt in range(max_attempts):

        script = generate_script(component, profile, semantics, geometry)


        if validate_script(script, geometry):
            save_script(component, script)
            print("\nOk")
            break
        else:
            print(f"\nRetry {attempt+1}/{max_attempts}")

    else:
        print("\nFailed after retries")