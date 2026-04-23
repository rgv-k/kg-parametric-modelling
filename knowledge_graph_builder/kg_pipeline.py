from crewai import Agent, Task, Crew, Process, LLM
import os
from dotenv import load_dotenv
import json
import time
from tqdm import tqdm
load_dotenv()
llm = LLM(
    model="openrouter/anthropic/claude-3-haiku",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0
)
VERSES_FILE = "data/parsed/MAYAMATA_COMBINED.json"
NODES_FILE = "data/nodes/KG_NODES_FULL.json"
OUTPUT_FILE = "data/kg/KG_RELATIONS_FINAL.json"
PARTIAL_FILE = "data/kg/KG_RELATIONS_PARTIAL.json"
os.makedirs("data/kg", exist_ok=True)
BATCH_SIZE = 10
extractor_agent = Agent(
    role='Senior Vastu Architect & Ontologist',
    goal='Extract structured, logic-based relationships from architectural texts.',
    backstory="""You are the lead architect of the Mayamata. Your job is to translate ancient verses into a computable Knowledge Graph.
    CRITICAL INSTRUCTIONS:
    1. **Preserve Sanskrit**: Never translate terms like 'Adhisthana' to 'Base' in the ID. Keep the Sanskrit ID.
    2. **Classify Logic**: Don't just say "X relates to Y". Tell me HOW. Is it a measurement? A location? A hierarchy?
    3. **Contextualize**: Your 'description' field must be a clean, standalone summary of the rule, not a raw text snippet.""",
    verbose=False,
    allow_delegation=False,
    llm=llm
)
validator_agent = Agent(
    role='Structural Logic Auditor',
    goal='Validate graph integrity and physical possibility.',
    backstory="""You are a strict structural engineer and graph validator. You review the Architect's work for impossible geometry.
    YOUR CHECKS:
    1. **Physics Check**: A 'Foundation' cannot be 'ABOVE' a 'Roof'. If you see this, reverse the relation or delete it.
    2. **Entity Check**: Ensure both Source and Target entities exist in our Master Node List. If a term is "unknown", map it to the closest valid node or discard it.
    3. **Redundancy**: Remove duplicate rules.
    4. **Encoding**: Ensure all Sanskrit characters (ā, ī, ś, etc.) are preserved correctly.""",
    verbose=False,
    allow_delegation=False,
    llm=llm
)
def run_batch(verses_chunk, valid_entities):
    extraction_task = Task(
        description=f"""
        Analyze these VERSES from the Mayamata:
        {json.dumps(verses_chunk, indent=2, ensure_ascii=False)}
        VALID ENTITIES (Reference these IDs): 
        {json.dumps(valid_entities[:100], indent=2, ensure_ascii=False)}... (and others)
        YOUR TASK:
        Extract relationships in this EXACT JSON format. Return ONLY the JSON list.
        [
            {{
                "source": "entity_id", 
                "relation": "IS_A" | "PART_OF" | "LOCATED_AT" | "LOCATED_ABOVE" | "LOCATED_BELOW" | "HAS_DIMENSION_RATIO" | "SYNONYM_OF", 
                "target": "entity_id",
                "properties": {{
                    "ratio": 1.0,
                    "rule_type": "MEASUREMENT" | "SPATIAL" | "HIERARCHY" | "DEFINITION",
                    "description": "A clear, human-readable summary of the rule."
                }}
            }}
        ]
        """,
        expected_output="A JSON list of relationships.",
        agent=extractor_agent
    )

    validation_task = Task(
        description="Review the JSON list. Remove physically impossible rules. Fix UTF-8 encoding issues. Return ONLY the clean JSON list.",
        expected_output="A clean, valid JSON list.",
        agent=validator_agent,
        context=[extraction_task]
    )

    crew = Crew(
        agents=[extractor_agent, validator_agent],
        tasks=[extraction_task, validation_task],
        process=Process.sequential,
        verbose=False
    )

    return crew.kickoff()


def main():
    if not os.path.exists(VERSES_FILE) or not os.path.exists(NODES_FILE):
        print("Missing input files.")
        return

    print("Starting Knowledge Graph Pipeline")

    with open(VERSES_FILE, 'r', encoding='utf-8') as f:
        verses = json.load(f)
    
    with open(NODES_FILE, 'r', encoding='utf-8') as f:
        nodes = json.load(f)
        valid_terms = [n['term'] for n in nodes if 'term' in n]

    all_validated_relations = []
    start_index = 0

    if os.path.exists(PARTIAL_FILE):
        try:
            with open(PARTIAL_FILE, 'r', encoding='utf-8') as f:
                all_validated_relations = json.load(f)
        except:
            pass

    for i in tqdm(range(start_index, len(verses), BATCH_SIZE)):
        batch = verses[i : i + BATCH_SIZE]
        
        try:
            batch_output = run_batch(batch, valid_terms)

            result_str = str(batch_output)
            clean_output = result_str.replace("```json", "").replace("```", "").strip()

            start = clean_output.find("[")
            end = clean_output.rfind("]") + 1
            
            if start != -1 and end != -1:
                json_str = clean_output[start:end]
                relations = json.loads(json_str)
                all_validated_relations.extend(relations)
                
                if i % (BATCH_SIZE * 5) == 0:
                    with open(PARTIAL_FILE, 'w', encoding='utf-8') as f:
                        json.dump(all_validated_relations, f, indent=2, ensure_ascii=False)

        except Exception:
            continue
        
        time.sleep(5)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_validated_relations, f, indent=2, ensure_ascii=False)

    print("Pipeline Complete")
    os.remove(PARTIAL_FILE)
    print(f"Generated {len(all_validated_relations)} relationships")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()