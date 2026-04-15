import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import time

load_dotenv()

llm = ChatOpenAI(
    openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    model="deepseek/deepseek-v3.2",
    temperature=0,
    max_tokens=20000,
    response_format={"type": "json_object"}
)

RAG_PROMPT = """
You are an expert system extracting structured architectural knowledge.

INPUT:
A semantic graph of an architectural component.

GOAL:
Extract ALL useful information about the component.

IMPORTANT:
You are NOT building geometry.
You are building a KNOWLEDGE REPRESENTATION.

---

EXTRACT THE FOLLOWING:

1. core_structure:
   - Direct subcomponents of the component

2. subcomponents:
   - All structural parts

3. variants:
   - Different types/forms of the component

4. materials:
   - Materials used

5. measurements:
   - ALL dimension rules (even contextual ones)

6. relationships:
   - Important structural or semantic relationships

7. contextual_info:
   - Any additional useful insights

---

RULES:

- DO NOT invent
- DO NOT omit useful information
- KEEP EVERYTHING RELEVANT
- KEEP descriptions SHORT (1 line max)
- Use component names (not IDs)

---

OUTPUT STRICT JSON:

{
  "component": "<name>",
  "core_structure": [],
  "subcomponents": [],
  "variants": [],
  "materials": [],
  "measurements": [],
  "relationships": [],
  "contextual_info": []
}
"""

class Neo4jRAG:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
        )

    def close(self):
        self.driver.close()

    def fetch(self, component):
        query = """
        MATCH (n)
        WHERE 
            (n.term IS NOT NULL AND toLower(n.term) CONTAINS toLower($component))
            OR (n.is_a IS NOT NULL AND toLower(n.is_a) CONTAINS toLower($component))
            OR (n.part_of IS NOT NULL AND toLower(n.part_of) CONTAINS toLower($component))

        WITH collect(n) AS seeds
        UNWIND seeds AS s

        CALL apoc.path.expand(s, "", "", 0, 2) YIELD path

        RETURN nodes(path) AS nodes, relationships(path) AS rels
        """

        with self.driver.session(database="mayamata-kg") as session:
            result = session.run(query, component=component)

            nodes, rels = [], []
            for r in result:
                nodes.extend(r["nodes"])
                rels.extend(r["rels"])

            return nodes, rels


def normalize(nodes, rels):
    node_map, rel_list, seen = {}, [], set()

    for n in nodes:
        nid = str(n.element_id)
        if nid not in node_map:
            node_map[nid] = {
                "id": nid,
                "term": dict(n).get("term"),
                "labels": list(n.labels)
            }

    for r in rels:
        sid = str(r.start_node.element_id)
        tid = str(r.end_node.element_id)
        key = (sid, tid, r.type)

        if key in seen:
            continue
        seen.add(key)

        rel_list.append({
            "from": sid,
            "to": tid,
            "type": r.type,
            "description": dict(r).get("description", "")[:120]
        })

    return list(node_map.values()), rel_list


def rank_relationships(rels, component):
    component = component.lower()

    def score(r):
        d = r["description"].lower()
        s = 0

        if component in d:
            s += 5
        if r["type"] in ["HAS_PART", "PART_OF"]:
            s += 3
        if any(k in d for k in ["height", "width", "diameter"]):
            s += 2
        if len(d) < 120:
            s += 1

        return s

    return sorted(rels, key=score, reverse=True)


def prepare(nodes, rels, top_k=80):
    rels = rels[:top_k]

    ids = {r["from"] for r in rels} | {r["to"] for r in rels}

    nodes = [n for n in nodes if n["id"] in ids]

    return {
        "nodes": nodes,
        "relationships": rels
    }


def call_llm(data, component):
    prompt = f"Component: {component}\nData:\n{json.dumps(data)}"

    res = llm.invoke([
        {"role": "system", "content": RAG_PROMPT},
        {"role": "user", "content": prompt}
    ])

    try:
        return json.loads(res.content)
    except:
        print("\nJSON ERROR:\n", res.content)
        return None


def save_rag_output(component, data):
    import os, json

    os.makedirs("rag_outputs", exist_ok=True)


    path = os.path.join("rag_outputs", f"{component}_{int(time.time())}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nSaved RAG output → {path}")




if __name__ == "__main__":
    rag = Neo4jRAG()

    component = input("Component: ")

    nodes, rels = rag.fetch(component)
    nodes, rels = normalize(nodes, rels)

    print(f"\nRaw: {len(nodes)} nodes, {len(rels)} rels")

    rels = rank_relationships(rels, component)

    data = prepare(nodes, rels, top_k=200)

    print(f"After ranking: {len(data['relationships'])}")

    result = call_llm(data, component)

    print("\n=== FINAL RAG OUTPUT ===")
    print(json.dumps(result, indent=2))

    if result:
        save_rag_output(component, result)

    rag.close()