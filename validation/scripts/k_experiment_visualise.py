import pandas as pd
import matplotlib.pyplot as plt
df = pd.read_csv("../results/k_experiment_full.csv")
results = []
for k in sorted(df['k'].unique()):
    subset = df[df['k'] == k]
    tp = len(subset[subset['status'] == 'SUPPORTED'])
    fp = len(subset[subset['status'] == 'CONTRADICTED'])
    fn = len(subset[subset['status'] == 'NOT_MENTIONED'])
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = (2 * precision * recall) / (precision + recall) if precision + recall else 0
    accuracy = tp / len(subset) if len(subset) else 0
    results.append({
        "k": k,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy
    })
metrics_df = pd.DataFrame(results)



print("\n Metrics per k:")
print(metrics_df)


plt.figure(figsize=(8, 5))
plt.plot(metrics_df['k'], metrics_df['precision'], marker='o', label='Precision')
plt.plot(metrics_df['k'], metrics_df['recall'], marker='o', label='Recall')
plt.plot(metrics_df['k'], metrics_df['f1'], marker='o', label='F1')
plt.plot(metrics_df['k'], metrics_df['accuracy'], marker='o', label='Accuracy')
plt.xlabel("k")
plt.ylabel("Score")
plt.title("Performance vs k")
plt.legend()
plt.grid(True)
plt.savefig("../plots/k_vs_metrics.png", bbox_inches='tight')
plt.close()


plt.figure(figsize=(8, 5))
plt.plot(metrics_df['k'], metrics_df['f1'], marker='o')
best_k = metrics_df.loc[metrics_df['f1'].idxmax(), 'k']
best_f1 = metrics_df['f1'].max()
plt.scatter(best_k, best_f1)
plt.text(best_k, best_f1, f"  best k={best_k}")
plt.xlabel("k")
plt.ylabel("F1 Score")
plt.title("Curve for Optimal k")
plt.grid(True)
plt.savefig("../plots/best_k_elbow.png", bbox_inches='tight')
plt.close()


print(f"\n Best k based on F1: {best_k}")

status_counts = df.groupby(['k', 'status']).size().unstack(fill_value=0)
status_counts.plot(kind='bar', stacked=True, figsize=(10,6))


plt.title("Status Distribution Across k")
plt.xlabel("k")
plt.ylabel("Count")
plt.savefig("../plots/status_shift.png", bbox_inches='tight')
plt.close()
plt.figure(figsize=(8, 5))
plt.plot(metrics_df['k'], metrics_df['precision'], marker='o')
plt.title("Precision Stability Across k")
plt.xlabel("k")
plt.ylabel("Precision")
plt.grid(True)
plt.savefig("../plots/precision_stability.png", bbox_inches='tight')
plt.close()


metrics_df.to_csv("k_metrics_summary.csv", index=False)

print("\n Files Generated:")
print("- ../plots/k_vs_metrics.png")
print("- ../plots/best_k_elbow.png")
print("- ../plots/k_status_shift.png")
print("- ../plots/k_precision_stability.png")
print("- ../plots/k_metrics_summary.csv")