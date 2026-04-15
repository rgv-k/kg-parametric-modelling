import subprocess
import sys
import os

COMPONENT = input("Enter component: ").strip()

PYTHON = sys.executable


def run_script(script, args=None):
    cmd = [PYTHON, script]

    if args:
        cmd.extend(args)

    print(f"\nRunning: {script}")

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"Failed at {script}")
        exit(1)


def run_rag():
    print("\nSTEP 1: RAG")

    process = subprocess.Popen(
        [PYTHON, "rag_query.py"],
        stdin=subprocess.PIPE,
        text=True
    )

    process.communicate(input=COMPONENT)

    if process.returncode != 0:
        print("RAG failed")
        exit(1)


def run_splitter():
    print("\nSTEP 2: Knowledge Split")
    run_script("knowledge_splitter.py")


def run_measurement():
    print("\nSTEP 3: Measurement Validation")
    run_script("measurement_validation.py", [COMPONENT])


def run_profile():
    print("\nSTEP 4: Profile Decomposition")

    process = subprocess.Popen(
        [PYTHON, "profile_decomposer.py"],
        stdin=subprocess.PIPE,
        text=True
    )

    process.communicate(input=COMPONENT)

    if process.returncode != 0:
        print("Profile decomposition failed")
        exit(1)


if __name__ == "__main__":
    print(f"\n=== PIPELINE START: {COMPONENT} ===")

    run_rag()
    run_splitter()
    run_measurement()
    run_profile()

    print("\nPIPELINE COMPLETE")