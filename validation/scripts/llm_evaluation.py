import json
import os
import time
import pandas as pd
import matplotlib.pyplot as plt
from neo4j import GraphDatabase
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
load_dotenv()
NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
class EvaluationResult(BaseModel):
    status: str = Field(description="Must be 'SUPPORTED', 'CONTRADICTED', or 'NOT_MENTIONED'")
    reason: str = Field(description="Brief quote or explanation supporting the status")
class GemmaKGEvaluator:
    def __init__(self, neo4j_uri, user, password, book_json_path):
        print("Initializing Advanced Evaluation Suite (Gemma 4)...")
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(user, password))
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self._setup_vector_store(book_json_path)
        self.llm = ChatOpenAI(
            model=os.getenv("MODEL_NAME"),
            temperature=1.0, 
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            max_tokens=1000,
            model_kwargs={
                "response_format": {"type": "json_object"},
                "extra_body": {"include_reasoning": True}
            }
        )
        self.chain = self._build_evaluation_chain()
    def _setup_vector_store(self, book_json_path):
        persist_directory = "../chroma_langchain_db"
        if os.path.exists(persist_directory):
            self.vector_store = Chroma(embedding_function=self.embeddings, persist_directory=persist_directory)
        else:
            with open(book_json_path, 'r', encoding='utf-8') as f:
                book_data = json.load(f)
            docs = [Document(page_content=item['text'], metadata={"verse": item['verse']}) for item in book_data]
            self.vector_store = Chroma.from_documents(documents=docs, embedding=self.embeddings, persist_directory=persist_directory)
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 1})
    def _build_evaluation_chain(self):
        parser = JsonOutputParser(pydantic_object=EvaluationResult)
        system_instructions = (
            "<|think|> You are a Vastu Shastra auditor. Verify the claim strictly against the evidence. \n"
            "Rules: SUPPORTED, CONTRADICTED, or NOT_MENTIONED. Output ONLY JSON.\n"
            "{format_instructions}"
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_instructions),
            ("user", "CLAIM:\n{claim}\n\nEVIDENCE:\n{context}")
        ]).partial(format_instructions=parser.get_format_instructions())
        return prompt | self.llm | parser
    def fetch_graph_edges(self, limit=200, seed=42):
        """Fetches edges with reproducible randomization."""
        query = """
        MATCH (source)-[r]->(target)
        WHERE r.description IS NOT NULL 
        RETURN source.term AS src_term, type(r) AS rel_type, 
               r.description AS edge_desc, target.term AS tgt_term
        ORDER BY rand()
        LIMIT $limit
        """
        with self.neo4j_driver.session(database='mayamata-kg') as session:
            result = session.run(query, limit=limit, seed=str(seed))
            return [record.data() for record in result]
    def evaluate(self, edges):
        results = []
        for i, edge in enumerate(edges):
            claim = f"{edge['src_term']} -> {edge['rel_type']} -> {edge['tgt_term']}"
            search_query = f"{edge['src_term']} {edge['tgt_term']} {edge['edge_desc']}"
            try:
                docs = self.retriever.invoke(search_query)
                context = "\n\n".join([f"[Verse {d.metadata['verse']}]: {d.page_content}" for d in docs])
                res = self.chain.invoke({"claim": claim, "context": context})
                res['edge'] = claim
                results.append(res)
                print(f"[{i+1}/{len(edges)}] {claim} | {res['status']}")
                time.sleep(0.5)
            except Exception as e:
                print(f"Error on edge {claim}: {e}")
        return pd.DataFrame(results)



def generate_visualizations(df):
    tp = len(df[df['status'] == 'SUPPORTED'])
    fp = len(df[df['status'] == 'CONTRADICTED'])
    fn = len(df[df['status'] == 'NOT_MENTIONED'])
    total = len(df)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    accuracy = tp / total if total > 0 else 0 # Your requested Accuracy line
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    print(f"\n--- PERFORMANCE METRICS ---")
    print(f"Precision (S / S+C): {precision:.2%}")
    print(f"Recall (S / S+N):    {recall:.2%}")
    print(f"Accuracy (S / Total): {accuracy:.2%}")
    print(f"F1-Score:            {f1:.2%}")


    plt.figure(figsize=(8, 5))
    df['status'].value_counts().plot(kind='bar', color=['#4CAF50', '#9E9E9E', '#F44336'])
    plt.title('Knowledge Graph Validation Distribution')
    plt.ylabel('Number of Edges')
    plt.xticks(rotation=0)
    plt.savefig('../plots/status_distribution.png')
    plt.close()
    plt.figure(figsize=(7, 7))
    plt.pie([tp, fp, fn], labels=['Supported', 'Contradicted', 'Not Mentioned'], 
            autopct='%1.1f%%', colors=['#4CAF50', '#F44336', '#9E9E9E'], startangle=140)
    plt.title('Overall KG Grounding')
    plt.savefig('../plots/reliability_pie.png')
    plt.close()


    df.to_csv("../results/evaluation_results_full.csv", index=False)
    metrics_summary = pd.DataFrame({
        "Metric": ["Precision", "Recall", "Accuracy", "F1-Score"],
        "Value": [precision, recall, accuracy, f1]
    })
    metrics_summary.to_csv("../results/performance_metrics.csv", index=False)



def run_k_experiment(evaluator, edges):
    """Runs evaluation for k=1 to 10 on SAME edge set AND saves full dataset."""

    metrics_results = []
    full_dataset = []

    for k in range(1, 11):
        print(f"\nRunning evaluation for k = {k}")

        evaluator.retriever = evaluator.vector_store.as_retriever(
            search_kwargs={"k": k}
        )

        df = evaluator.evaluate(edges)

        df["k"] = k


        full_dataset.append(df)

        tp = len(df[df['status'] == 'SUPPORTED'])
        fp = len(df[df['status'] == 'CONTRADICTED'])
        fn = len(df[df['status'] == 'NOT_MENTIONED'])

        precision = tp / (tp + fp) if (tp + fp) else 0
        recall = tp / (tp + fn) if (tp + fn) else 0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0

        metrics_results.append({
            "k": k,
            "precision": precision,
            "recall": recall,
            "f1": f1
        })

    full_df = pd.concat(full_dataset, ignore_index=True)

    if "edge" in full_df.columns:
        full_df = full_df[["k", "edge", "status", "reason"]]

    full_df.to_csv("../plots/k_experiment_full.csv", index=False)

    print("\nFull dataset saved to ../plots/k_experiment_full.csv")

    results_df = pd.DataFrame(metrics_results)

    print("\nK experiment results:")
    print(results_df)

    plt.figure(figsize=(8, 5))
    plt.plot(results_df['k'], results_df['precision'], marker='o', label='Precision')
    plt.plot(results_df['k'], results_df['recall'], marker='o', label='Recall')
    plt.plot(results_df['k'], results_df['f1'], marker='o', label='F1')

    plt.xlabel("k (Retriever Depth)")
    plt.ylabel("Score")
    plt.title("Performance vs K")
    plt.legend()

    plt.savefig("../plots/k_experiment.png", bbox_inches='tight')
    plt.close()

    results_df.to_csv("../plots/k_experiment_results.csv", index=False)

    print("\nMetrics saved to ../plots/k_experiment_results.csv")


if __name__ == "__main__":
    evaluator = GemmaKGEvaluator(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, "MAYAMATA_COMBINED.json")
    
    edges = evaluator.fetch_graph_edges(limit=200, seed=42)

    print("\nChoose Mode:")
    print("1. Single Evaluation")
    print("2. K Experiment (1–10 on same dataset)")

    choice = input("Enter choice: ")

    if choice == "1":
        results_df = evaluator.evaluate(edges)
        generate_visualizations(results_df)

    elif choice == "2":
        run_k_experiment(evaluator, edges)

    else:
        print("Invalid choice")

    evaluator.neo4j_driver.close()