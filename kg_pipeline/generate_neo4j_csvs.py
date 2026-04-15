import json
import csv
import os

NODES_FILE = "data/nodes/KG_NODES_FULL.json"
RELATIONS_FILE = "data/kg/KG_RELATIONS_FINAL.json"
OUTPUT_NODES = "import_nodes.csv"
OUTPUT_EDGES = "import_edges.csv"
MAX_CHAR_LIMIT = 30000 

def clean_text(text):
    """Cleans text for CSV compatibility."""
    if text is None: return ""
    text = str(text)
    if len(text) > MAX_CHAR_LIMIT:
        text = text[:MAX_CHAR_LIMIT] + "...(TRUNCATED)"
    text = text.replace('"', "'") 
    text = text.replace('\n', ' ') 
    text = text.replace('\\', '') 
    return text

def main():
    print("Starting Robust Graph Generation")

    if not os.path.exists(NODES_FILE) or not os.path.exists(RELATIONS_FILE):
        print(f"Error: Input files not found.")
        return


    print(f"Reading {NODES_FILE}...")
    with open(NODES_FILE, 'r', encoding='utf-8') as f:
        raw_nodes = json.load(f)


    valid_nodes = {}
    
    for n in raw_nodes:
        original_id = n.get('id')
        if not original_id: continue
        

        final_id = original_id
        counter = 2
        while final_id in valid_nodes:
            final_id = f"{original_id}_{counter}"
            counter += 1
            
        n['id'] = final_id
        valid_nodes[final_id] = n

    print(f"   - Loaded {len(valid_nodes)} unique nodes from Glossary.")


    print(f"Reading {RELATIONS_FILE}...")
    with open(RELATIONS_FILE, 'r', encoding='utf-8') as f:
        raw_relations = json.load(f)

    final_edges = []
    created_placeholder_count = 0


    term_lookup = {}
    for nid, node in valid_nodes.items():
        term = node.get('term', '').lower().strip()
        if term:
            if term not in term_lookup: term_lookup[term] = []
            term_lookup[term].append(nid)

    for r in raw_relations:
        src_raw = r.get('source', '').strip()
        tgt_raw = r.get('target', '').strip()
        
        if not src_raw or not tgt_raw: continue


        src_id = src_raw

        if src_raw not in valid_nodes:

            found_ids = term_lookup.get(src_raw.lower())
            if found_ids:
                src_id = found_ids[0] 
            else:

                valid_nodes[src_raw] = {
                    "id": src_raw,
                    "term": src_raw,
                    "category": "Derived_Node",
                    "definition_summary": "Entity extracted from verses, not found in glossary."
                }
                created_placeholder_count += 1


        tgt_id = tgt_raw
        if tgt_raw not in valid_nodes:
            found_ids = term_lookup.get(tgt_raw.lower())
            if found_ids:
                tgt_id = found_ids[0]
            else:
                valid_nodes[tgt_raw] = {
                    "id": tgt_raw,
                    "term": tgt_raw,
                    "category": "Derived_Node",
                    "definition_summary": "Entity extracted from verses, not found in glossary."
                }
                created_placeholder_count += 1


        props = r.get('properties', {})
        ratio_val = props.get('ratio', '')
        if ratio_val is None: ratio_val = ""
        
        final_edges.append({
            ':START_ID': src_id,
            ':END_ID': tgt_id,
            ':TYPE': clean_text(r['relation']).upper().replace(" ", "_"),
            'ratio': ratio_val,
            'rule_type': clean_text(props.get('rule_type', '')),
            'description': clean_text(props.get('description', ''))
        })

    print(f"   - Created {created_placeholder_count} new placeholder nodes for missing terms.")
    print(f"   - Final Total Nodes: {len(valid_nodes)}")
    print(f"   - Final Total Edges: {len(final_edges)}")


    print(f"Writing CSVs...")


    all_attr_keys = set()
    for n in valid_nodes.values():
        if 'attributes' in n:
            all_attr_keys.update(n['attributes'].keys())
    sorted_attr_keys = sorted(list(all_attr_keys))
    
    node_headers = ['nodeId:ID', 'term', 'definition', ':LABEL'] + sorted_attr_keys

    with open(OUTPUT_NODES, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(node_headers)
        for n in valid_nodes.values():
            row = [
                n.get('id'),
                clean_text(n.get('term', '')),
                clean_text(n.get('definition_summary', '')),
                clean_text(n.get('category', 'Concept')).upper().replace(" ", "_")
            ]
            attrs = n.get('attributes', {})
            for key in sorted_attr_keys:
                row.append(clean_text(attrs.get(key, '')))
            writer.writerow(row)


    edge_headers = [':START_ID', ':END_ID', ':TYPE', 'ratio', 'rule_type', 'description']
    with open(OUTPUT_EDGES, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=edge_headers)
        writer.writeheader()
        writer.writerows(final_edges)

    print(f"\nSUCCESS")
    print("All data preserved. Placeholders created for missing terms.")
    print("Copy 'import_nodes.csv' and 'import_edges.csv' to Neo4j.")

if __name__ == "__main__":
    main()