import pandas as pd
import matplotlib.pyplot as plt


file_path = "../results/evaluation_results_full.csv"
df = pd.read_csv(file_path)


def clean_status(status):
    if not isinstance(status, str):
        return "NOT_MENTIONED"

    s = status.strip().upper()

    if s in ["NOT_MENTED", "NOT MENTIONED", "NOTMENTIONED"]:
        return "NOT_MENTIONED"

    if s not in ["SUPPORTED", "CONTRADICTED", "NOT_MENTIONED"]:
        return "NOT_MENTIONED"

    return s


df["status"] = df["status"].apply(clean_status)


display_map = {
    "SUPPORTED": "Supported",
    "CONTRADICTED": "Contradicted",
    "NOT_MENTIONED": "Not Mentioned"
}
df["status_display"] = df["status"].map(display_map)

print("\nCleaned Status Counts:")
print(df["status"].value_counts())


tp = len(df[df['status'] == 'SUPPORTED'])
fp = len(df[df['status'] == 'CONTRADICTED'])
fn = len(df[df['status'] == 'NOT_MENTIONED'])
total = len(df)

precision = tp / (tp + fp) if (tp + fp) else 0
recall = tp / (tp + fn) if (tp + fn) else 0
accuracy = tp / total if total else 0
f1 = (2 * precision * recall) / (precision + recall) if precision + recall else 0

print("\n📊 METRICS:")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"Accuracy:  {accuracy:.4f}")
print(f"F1 Score:  {f1:.4f}")

plt.figure(figsize=(8, 6))

counts = df['status_display'].value_counts()
ax = counts.plot(kind='bar')

plt.xticks(rotation=20, ha='right')

# Add values on bars
for p in ax.patches:
    ax.annotate(
        str(int(p.get_height())),
        (p.get_x() + p.get_width()/2., p.get_height()),
        ha='center', va='bottom'
    )

plt.title("Status Distribution")
plt.xlabel("Status")
plt.ylabel("Count")

plt.tight_layout()
plt.savefig("../plots/status_distribution.png", bbox_inches='tight')
plt.close()


metrics_df = pd.DataFrame({
    "Metric": ["Precision", "Recall", "Accuracy", "F1 Score"],
    "Value": [precision, recall, accuracy, f1]
})

plt.figure(figsize=(8, 5))
plt.bar(metrics_df["Metric"], metrics_df["Value"])

for i, v in enumerate(metrics_df["Value"]):
    plt.text(i, v + 0.02, f"{v:.2f}", ha='center')

plt.ylim(0, 1)
plt.title("Performance Metrics")

plt.tight_layout()
plt.savefig("../plots/metrics.png", bbox_inches='tight')
plt.close()


plt.figure(figsize=(7, 7))
plt.pie(
    [tp, fp, fn],
    labels=["Supported", "Contradicted", "Not Mentioned"],
    autopct="%1.1f%%",
    startangle=140
)
plt.title("Prediction Breakdown")

plt.tight_layout()
plt.savefig("../plots/pie_chart.png", bbox_inches='tight')
plt.close()


df['supported_flag'] = (df['status'] == 'SUPPORTED').astype(int)
df['cumulative_supported'] = df['supported_flag'].cumsum()

plt.figure(figsize=(8, 5))
plt.plot(df.index, df['cumulative_supported'])

plt.title("Cumulative Supported Predictions")
plt.xlabel("Edge Index")
plt.ylabel("Cumulative Count")

plt.tight_layout()
plt.savefig("../plots/cumulative_supported.png", bbox_inches='tight')
plt.close()

df.to_csv("../results/cleaned_results.csv", index=False)

metrics_df.to_csv("../results/metrics_summary.csv", index=False)

print("\nFiles Generated:")
print("- cleaned_results.csv")
print("- metrics_summary.csv")
print("- status_distribution.png")
print("- metrics.png")
print("- pie_chart.png")
print("- cumulative_supported.png")