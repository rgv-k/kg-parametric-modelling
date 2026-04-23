from neo4j import GraphDatabase
import json
from dotenv import load_dotenv
import os
load_dotenv()
URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")
DB_NAME = os.getenv("DATABASE_NAME")
OUTPUT_FILE = "../datasets/filtered_base_kg"
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
QUERY = """
MATCH (b:Concept)
WHERE toLower(b.term) IN ["adhiṣṭhāna", "base"]
MATCH (b)-[r1]-(n1)
RETURN DISTINCT
    toLower(startNode(r1).term) AS source,
    type(r1) AS type,
    toLower(endNode(r1).term) AS target
UNION
MATCH (b:Concept)
WHERE toLower(b.term) IN ["adhiṣṭhāna", "base"]
MATCH (b)-[r1]-(n1)-[r2]-(n2)
RETURN DISTINCT
    toLower(startNode(r2).term) AS source,
    type(r2) AS type,
    toLower(endNode(r2).term) AS target
"""


def run_query():
    with driver.session(database=DB_NAME) as session:
        result = session.run(QUERY)
        return [record.data() for record in result]


def normalize(text):
    return " ".join(text.lower().strip().split())


def normalize_triplet(t):
    return {
        "type": t["type"].upper().strip(),
        "source": normalize(t["source"]),
        "target": normalize(t["target"])
    }



ALLOWED_CORE = set([
    "adhiṣṭhāna", "base",
    "uragabandha", "padmakesara", "pādabandha", "pratikrama",
    "upāna", "kumuda", "paṭṭikā", "kaṇṭha", "kampa",
    "upapīṭha", "pādukā", "prati"
])

ALLOWED_RELATIONS = set([
    "IS_A",
    "PART_OF",
    "HAS_PART",
    "HAS_DIMENSION_RATIO",
    "LOCATED_ABOVE",
    "LOCATED_BELOW",
    "LOCATED_AT"
])


def is_valid(triple):
    return (
        triple["type"] in ALLOWED_RELATIONS and
        (
            triple["source"] in ALLOWED_CORE or
            triple["target"] in ALLOWED_CORE
        )
    )


def deduplicate(triples):
    return list({
        (t["type"], t["source"], t["target"]): t
        for t in triples
    }.values())

def wrap_as_gold_format(triples):
    return [
        {
            "verse": "KG",
            "relationships": triples
        }
    ]


def main():
    print("Running Neo4j query...")
    raw = run_query()
    print(f"Total extracted: {len(raw)}")

    print("Normalizing...")
    normalized = [normalize_triplet(t) for t in raw]

    print("Filtering...")
    filtered = [t for t in normalized if is_valid(t)]

    print("Deduplicating...")
    final = deduplicate(filtered)

    print(f"\nFinal Triples: {len(final)}")

    structured_output = wrap_as_gold_format(final)

    # Save
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(structured_output, f, indent=2, ensure_ascii=False)

    print(f"Saved to {OUTPUT_FILE}")



if __name__ == "__main__":
    main()