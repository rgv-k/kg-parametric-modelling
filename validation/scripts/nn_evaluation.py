import json
import numpy as np
import matplotlib.pyplot as plt
import unicodedata
from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity



with open("../datasets/filtered_base_kg.json", "r", encoding="utf-8") as f:
    kg_data = json.load(f)
with open("../datasets/golden_annotation_c14.json", "r", encoding="utf-8") as f:
    gold_data = json.load(f)


kg_triplets = kg_data[0]["relationships"]
gold_triplets = []


for v in gold_data:
    gold_triplets.extend(v["relationships"])
def remove_diacritics(text):
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    )

def normalize(text):
    text = remove_diacritics(text)
    return " ".join(text.lower().strip().split())


def normalize_relation(t):
    if t["type"] == "PART_OF":
        return {
            "type": "HAS_PART",
            "source": t["target"],
            "target": t["source"]
        }
    return t


def normalize_base_names(t):
    if "bandha" in t["source"] and "base" not in t["source"]:
        t["source"] += " base"
    if "bandha" in t["target"] and "base" not in t["target"]:
        t["target"] += " base"
    return t


kg_triplets = [
    normalize_base_names(normalize_relation(t))
    for t in kg_triplets
]
gold_triplets = [
    {
        "type": t["type"].upper(),
        "source": normalize(t["source"]),
        "target": normalize(t["target"])
    }
    for t in gold_triplets
]
def rel_to_text(r):
    return normalize(
        f"{r['source']} is connected to {r['target']} via {r['type']}"
    )


kg_texts = [rel_to_text(r) for r in kg_triplets]
gold_texts = [rel_to_text(r) for r in gold_triplets]

print(" Loading model...")
model = SentenceTransformer("all-MiniLM-L6-v2")


print(" Encoding KG text...")
kg_emb = model.encode(kg_texts, convert_to_tensor=True)


print(" Encoding GOLD text...")
gold_emb = model.encode(gold_texts, convert_to_tensor=True)


print(" Encoding components...")
kg_source_emb = model.encode([t["source"] for t in kg_triplets], convert_to_tensor=True)
kg_target_emb = model.encode([t["target"] for t in kg_triplets], convert_to_tensor=True)
kg_type_emb   = model.encode([t["type"]   for t in kg_triplets], convert_to_tensor=True)
gold_source_emb = model.encode([t["source"] for t in gold_triplets], convert_to_tensor=True)
gold_target_emb = model.encode([t["target"] for t in gold_triplets], convert_to_tensor=True)
gold_type_emb   = model.encode([t["type"]   for t in gold_triplets], convert_to_tensor=True)
sim_matrix = cosine_similarity(
    kg_emb.cpu().numpy(),
    gold_emb.cpu().numpy()
)


def weighted_similarity(i, j):
    s_sim = util.cos_sim(kg_source_emb[i], gold_source_emb[j]).item()
    t_sim = util.cos_sim(kg_target_emb[i], gold_target_emb[j]).item()
    r_sim = util.cos_sim(kg_type_emb[i], gold_type_emb[j]).item()
    return 0.4 * s_sim + 0.4 * t_sim + 0.2 * r_sim




threshold = 0.5
matches = 0
for i in range(len(kg_triplets)):
    best_score = 0
    for j in range(len(gold_triplets)):
        score = weighted_similarity(i, j)
        if score > best_score:
            best_score = score
    if best_score >= threshold:
        matches += 1
tp = matches
fp = len(kg_triplets) - tp
fn = len(gold_triplets) - tp
precision = tp / (tp + fp) if tp + fp else 0
recall = tp / (tp + fn) if tp + fn else 0
f1 = (2 * precision * recall) / (precision + recall) if precision + recall else 0



print("\n RESULTS:")
print(f"Precision: {precision:.3f}")
print(f"Recall:    {recall:.3f}")
print(f"F1 Score:  {f1:.3f}")
plt.figure()
plt.imshow(sim_matrix, aspect='auto')
plt.colorbar()
plt.title("Similarity Matrix (KG vs Manual)")
plt.xlabel("Manual Triplets")
plt.ylabel("KG Triplets")
plt.show()



scores = sim_matrix.flatten()
plt.figure()
plt.hist(scores, bins=50)
plt.title("Similarity Score Distribution")
plt.xlabel("Cosine Similarity")
plt.ylabel("Frequency")
plt.show()



thresholds = np.linspace(0.4, 0.9, 20)
precisions = []
recalls = []
for t in thresholds:
    tp_temp = sum(np.max(sim_matrix, axis=1) >= t)
    fp_temp = len(kg_triplets) - tp_temp
    fn_temp = len(gold_triplets) - tp_temp
    p = tp_temp / (tp_temp + fp_temp) if tp_temp + fp_temp else 0
    r = tp_temp / (tp_temp + fn_temp) if tp_temp + fn_temp else 0
    precisions.append(p)
    recalls.append(r)


plt.figure()
plt.plot(recalls, precisions)
plt.xlabel("Recall")
plt.ylabel("Precision")
plt.title("Precision-Recall Curve")
plt.show()