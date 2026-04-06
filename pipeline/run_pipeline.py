import subprocess
import sys
import os


def run_step(command, step_name):
    print(f"\n--- Running: {step_name} ---")

    result = subprocess.run(command, shell=True)

    if result.returncode != 0:
        print(f"\nError in step: {step_name}")
        sys.exit(1)

    print(f"Completed: {step_name}")


def main(input_pdf):

    # Ensure required directories exist
    required_dirs = [
        "data/ocr",
        "data/parsed",
        "data/glossary_batches",
        "data/glossary_clean",
        "data/glossary_final",
        "data/nodes",
        "data/kg"
    ]

    for d in required_dirs:
        os.makedirs(d, exist_ok=True)

    # 1. OCR main text
    run_step(
        f"python ocr_extract.py {input_pdf}",
        "OCR Extraction"
    )

    # 2. Parse verses
    run_step(
        "python pass_verses.py",
        "Verse Parsing"
    )

    # 3. Combine parsed verses
    run_step(
        "python combine_parsed.py",
        "Combine Parsed Verses"
    )

    # 4. Glossary OCR (auto batch)
    run_step(
        "python ocr_batch_glossary.py",
        "Glossary OCR"
    )

    # 5. Validate glossary batches
    run_step(
        "python validate_batches.py",
        "Glossary Validation"
    )

    # 6. Combine glossary
    run_step(
        "python combine_glossary.py",
        "Combine Glossary"
    )

    # 7. Extract nodes (CrewAI)
    run_step(
        "python extract_nodes_full.py",
        "Node Extraction"
    )

    # 8. Knowledge graph relations (CrewAI)
    run_step(
        "python kg_pipeline.py",
        "KG Relation Extraction"
    )

    #9. Generate Neo4j CSVs
    run_step(
        "python generate_neo4j_csvs.py",
        "Generate Neo4j CSVs"
    )

    print("\n--- Pipeline Completed Successfully ---")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_pipeline.py <input_pdf>")
        sys.exit(1)

    main(sys.argv[1])