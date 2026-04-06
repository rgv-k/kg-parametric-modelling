# Mayamatam Knowledge Graph Pipeline

## Overview

This project implements a fully automated pipeline to transform architectural knowledge from the *Mayamatam* into a structured Knowledge Graph.

The system processes raw PDF input and produces:

* Structured verses
* Cleaned glossary ontology
* Knowledge graph nodes
* Knowledge graph relationships

The pipeline uses:

* OCR for text extraction
* LLM-based parsing and validation (via OpenRouter)
* CrewAI multi-agent system for ontology and relationship construction

---

## Pipeline Architecture

```
PDF
 → OCR Extraction
 → Verse Parsing
 → Glossary Extraction (Batch OCR)
 → Glossary Validation (LLM)
 → Glossary Combination
 → Node Extraction (CrewAI)
 → Relationship Extraction (CrewAI)
 → Knowledge Graph JSON
```

---

## Project Structure

```
MayamatamRAG/
│
├── data/                      # Auto-generated (not tracked)
│   ├── ocr/
│   ├── parsed/
│   ├── glossary_batches/
│   ├── glossary_clean/
│   ├── glossary_final/
│   ├── nodes/
│   └── kg/
│
├── ocr_extract.py
├── pass_verses.py
├── combined_parsed.py
├── ocr_batch_glossary.py
├── validate_batches.py
├── combine_glossary.py
├── extract_nodes_full.py
├── kg_pipeline.py
├── run_pipeline.py
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup Instructions

### 1. Clone the repository

```
git clone https://github.com/YOUR_USERNAME/mayamatam-kg-pipeline.git
cd mayamatam-kg-pipeline
```

---

### 2. Create virtual environment

```
python -m venv .venv
.\.venv\Scripts\activate
```

---

### 3. Install dependencies

```
pip install -r requirements.txt
```

---

### 4. Configure environment variables

Create a `.env` file:

```
OPENROUTER_API_KEY=your_api_key_here
```

---

## How to Run the Pipeline

### Single command execution

```
python run_pipeline.py <input_pdf>
```

Example:

```
python run_pipeline.py mayamata_chapter5.pdf
```

---

## Step-by-Step Execution (Optional)

If you want to run manually:

### 1. OCR Extraction

```
python ocr_extract.py input.pdf
```

Output:

```
data/ocr/<file>_text.json
```

---

### 2. Verse Parsing (LLM)

```
python pass_verses.py
```

Output:

```
data/parsed/<file>_parsed.json
```

---

### 3. Combine Parsed Verses

```
python combined_parsed.py
```

Output:

```
data/parsed/MAYAMATA_COMBINED.json
```

---

### 4. Glossary OCR (Automated Batching)

```
python ocr_batch_glossary.py
```

Output:

```
data/glossary_batches/GLOSSARY_BATCH_X.json
```

---

### 5. Glossary Validation (LLM)

```
python validate_batches.py
```

Output:

```
data/glossary_clean/GLOSSARY_BATCH_X_CLEAN.json
```

---

### 6. Combine Glossary

```
python combine_glossary.py
```

Output:

```
data/glossary_final/GLOSSARY_FINAL.json
```

---

### 7. Node Extraction (CrewAI)

```
python extract_nodes_full.py
```

Output:

```
data/nodes/KG_NODES_FULL.json
```

---

### 8. Relationship Extraction (CrewAI)

```
python kg_pipeline.py
```

Output:

```
data/kg/KG_RELATIONS_FINAL.json
```

---

## Output Files

| File                      | Description                            |
| ------------------------- | -------------------------------------- |
| `KG_NODES_FULL.json`      | Ontology nodes extracted from glossary |
| `KG_RELATIONS_FINAL.json` | Relationships extracted from verses    |
| `MAYAMATA_COMBINED.json`  | Structured verse dataset               |

---

## Notes

* The `data/` directory is generated automatically and is excluded from version control.
* The pipeline is deterministic (`temperature=0`) for reproducibility.
* OpenRouter is used as the unified LLM backend.
* CrewAI enables multi-agent reasoning for structured knowledge extraction.

---

## Troubleshooting

### 1. `ModuleNotFoundError`

Ensure virtual environment is activated and dependencies are installed.

### 2. `crewai not found`

Install inside venv:

```
pip install crewai
```

### 3. LLM errors

Check:

* API key in `.env`
* internet connection
* OpenRouter model availability

---

## Reproducibility

The pipeline is fully automated and can be reproduced using:

```
python run_pipeline.py <input_pdf>
```

All intermediate stages are stored and can be inspected independently.

---

## License

Add your preferred license here.
