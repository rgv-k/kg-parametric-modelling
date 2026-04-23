# Knowledge Graph-Driven Parametric Modeling of Nagara Style Hindu Temples: An Agent-Based Computational Framework for Vastu Shastra Digital Preservation

This project presents a complete pipeline for extracting structured knowledge from the *Mayamatam* text, constructing a knowledge graph, and generating temple components using Retrieval-Augmented Generation (RAG) and Blender scripts.

The system integrates:
- OCR and text parsing
- Knowledge graph construction using Neo4j
- Retrieval-Augmented Generation (RAG)
- Blender-based 3D model generation
- Multi-layer validation (embedding-based and LLM-based)

---

## Project Overview

The pipeline is divided into three main components:

### 1. Knowledge Graph Pipeline
Extracts structured triplets from textual data:
OCR → Parsing → Node/Edge Extraction → Neo4j Import

### 2. RAG Pipeline
Generates structured outputs and Blender scripts:
Query → Retrieval → Decomposition → Script Generation

### 3. Validation Pipeline
Evaluates semantic correctness using:
- Embedding-based evaluation
- LLM-based evaluation with retrieval

---

## Project Structure

MAYAMATAM_RAG/

├── knowledge_graph_builder/    # KG construction pipeline

├── rag_model_builder/          # RAG + Blender generation

├── validation/                 # Evaluation framework

├── neo4j_dump/                 # CSVs for Neo4j import

├── blender_outputs/            # Final 3D outputs


## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/rgv-k/kg-parametric-modelling

cd MAYAMATAM_RAG
```
---

### 2. Create Virtual Environment

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```
Linux/Mac:
```bash
python -m venv venv
source venv/bin/activate
```
---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```
---

### 4. Environment Variables

Create a `.env` file in each of the following directories:

- knowledge_graph_builder/
  
- rag_model_builder/
  
- validation/

Each `.env` file should contain:

OPENROUTER_API_KEY=your_api_key
NEO4J_URI= instance_uri
NEO4J_USER=neo4j  
NEO4J_PASSWORD=your_password 
DATABASE_NAME=database_name
MODEL_NAME=your_model_name


---

## Neo4j Setup

1. Install Neo4j Desktop or Neo4j Server  
2. Create a database named:

mayamata-kg

3. Copy the CSV files from:

neo4j_dump/

into Neo4j's import directory.

4. Run the following queries in Neo4j Browser:

LOAD CSV WITH HEADERS FROM 'file:///import_nodes.csv' AS row  
CREATE (:Node {term: row.term});

LOAD CSV WITH HEADERS FROM 'file:///import_edges_master.csv' AS row  
MATCH (a:Node {term: row.source})  
MATCH (b:Node {term: row.target})  
CREATE (a)-[:REL {description: row.description}]->(b);

---

## Important Setup Notes

- Neo4j must be running before executing any validation or RAG scripts  
- Ensure credentials in `.env` match your Neo4j instance


## Running the Pipeline

### 1. Knowledge Graph Construction

```bash
cd knowledge_graph_builder
python run_pipeline.py <input_pdf>
```

This step performs:
- OCR extraction
- Text parsing
- Triplet extraction (source, relation, target)
- CSV generation for Neo4j import

Outputs are stored in:

knowledge_graph_builder/data/

---

### 2. RAG + Blender Generation

```bash
cd rag_model_builder
python pipeline_runner.py
```

This step performs:
- Retrieval of knowledge graph context
- Semantic decomposition of components
- Geometry and profile generation

Run blender_agent.py to generate component script
Outputs are stored in:

rag_model_builder/
├── outputs/
├── generated_scripts/
├── rag_outputs/
├── split_outputs/

---

### 3. Blender Execution

Blender execution is manual.

Steps:
1. Open Blender
2. Navigate to the scripting workspace
3. Load scripts from:

rag_model_builder/generated_scripts/

4. Execute the scripts

Final outputs are saved in:

blender_outputs/

---

## Notes on Blender Execution

- Multiple iterations may be required to obtain optimal geometry
- Some scripts may require refinement
- In certain cases, external LLM assistance may be used to improve script quality
- Generated models include individual components (base, pillar, roof, garbha) and assembled structures



## Validation Pipeline

All validation scripts are located in:

validation/scripts/

---

### 1. Embedding-Based Evaluation (Baseline)

cd validation/scripts
python nn_evaluation.py

This method:
- Converts triplets into text format
- Computes cosine similarity between:
  - generated knowledge graph triplets
  - manually annotated triplets
- Uses threshold-based matching
- Outputs precision, recall, and F1-score

---

### 2. LLM-Based Evaluation

python llm_evaluation.py

This method:
- Retrieves relevant passages from source text using a vector database
- Uses a language model to evaluate each triplet
- Classifies relationships into:
  - SUPPORTED
  - CONTRADICTED
  - NOT_MENTIONED
- Stores results along with reasoning

---

### 3. K-Sensitivity Analysis

python k_experiment_visualise.py

This experiment:
- Evaluates performance for k = 1 to 10
- Uses the same dataset across all runs
- Measures:
  - Precision
  - Recall
  - F1-score
  - Accuracy

Outputs:
- Performance vs k plot
- Elbow plot for optimal k
- Dataset containing all predictions across k values

---

### 4. Visualization

python validation_visualise.py

Generates:
- Status distribution plots
- Cumulative supported predictions plot
- Metric summaries

---

## Validation Data

Located in:

validation/datasets/

Includes:
- golden_annotation_c14.json (manual ground truth)
- glossary.json (term mappings)
- filtered_base_kg.json (subset of KG)
- MAYAMATA_COMBINED.json (source text)

---

## Validation Results

Stored in:

validation/results/

Includes:
- evaluation_results_full.csv
- k_experiment_full.csv
- k_experiment_results.csv
- k_metrics_summary.csv
- performance_metrics.csv

Plots are stored in:

validation/plots/



## Evaluation Strategy

The system uses a two-stage external validation framework:

### 1. Embedding-Based Evaluation
- Uses cosine similarity between triplets
- Serves as a baseline method
- Does not incorporate context or reasoning
- Limited in handling:
  - linguistic differences (Sanskrit vs English)
  - abstraction differences (fine-grained vs conceptual)

### 2. LLM-Based Evaluation
- Uses retrieval-augmented reasoning
- Evaluates relationships in the context of source text
- Performs classification into:
  - SUPPORTED
  - CONTRADICTED
  - NOT_MENTIONED
- Handles:
  - cross-lingual equivalence
  - semantic abstraction
  - contextual grounding

---

## Key Observations

- Embedding-based methods are insufficient for evaluating semantically rich knowledge graphs
- LLM-based evaluation provides significantly improved semantic alignment
- The system achieves high precision with controlled recall
- Optimal retrieval depth observed at:

k = 1

- Increasing k introduces additional context but also increases noise

---

## Important Notes

- Blender execution is not fully automated
- Neo4j must be running before validation or RAG execution
- Chroma vector database is created automatically during evaluation
- Retrieval quality directly impacts evaluation performance
- Some outputs may require iterative refinement

---

## Known Limitations

- Dependence on retrieval quality
- Sensitivity to irrelevant context at higher k values
- Variability in LLM responses
- Subjectivity in manual annotations
- Partial coverage of source text in evaluation dataset

---

## Reproducibility Checklist

- Install all dependencies from requirements.txt
- Configure environment variables in all modules
- Start Neo4j database (mayamata-kg)
- Import nodes and edges into Neo4j
- Run knowledge graph pipeline
- Run RAG pipeline
- Run validation scripts

---


## Authors

Raghavendra A, Student, REVA University

Dr. Sindhu P. Menon, Professor, REVA University
