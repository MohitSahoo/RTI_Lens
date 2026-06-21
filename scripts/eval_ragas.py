#!/usr/bin/env python3
"""
RAG Evaluation using official ragas library
"""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from langchain_groq import ChatGroq
from backend.config import GROQ_API_KEY, GROQ_MODEL

# Test queries for evaluation
TEST_QUERIES = [
    {
        "question": "What is the CIC?",
        "ground_truth": "The CIC is the Commonwealth Infantry Corps."
    },
    {
        "question": "How do I transfer to the CIC?",
        "ground_truth": "Transfer requires minimum 2 years service and commanding officer approval."
    },
    {
        "question": "What are the age limits for CIC enrollment?",
        "ground_truth": "Age limits vary by enrollment type; typically 17-25 for initial enrollment."
    }
]

def run_evaluation(test_data: list):
    """Run ragas evaluation on test data"""

    llm = ChatGroq(
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY
    )

    # Build dataset (ragas expects specific column names)
    dataset = Dataset.from_list([
        {
            "question": item["question"],
            "answer": item.get("answer", ""),
            "contexts": item.get("contexts", []),
            "ground_truth": item.get("ground_truth", "")
        }
        for item in test_data
    ])

    # Evaluate with selected metrics
    result = evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall
        ],
        llm=llm
    )

    return result

def main():
    print("RAG Evaluation with Official RAGAS")
    print("=" * 50)

    # Check if we have actual answers to evaluate
    # For now, test with sample structure
    sample_data = [
        {
            "question": "What is the CIC?",
            "answer": "The Commonwealth Infantry Corps is a military formation.",
            "contexts": ["The CIC stands for Commonwealth Infantry Corps."],
            "ground_truth": "The CIC is the Commonwealth Infantry Corps."
        }
    ]

    print(f"\nRunning evaluation on {len(sample_data)} sample...")
    result = run_evaluation(sample_data)

    print("\nResults:")
    print(result)

    # Save results
    output_path = Path(__file__).parent.parent / "data" / "eval_results.json"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(result.to_pandas().to_dict(orient="records"), f, indent=2)

    print(f"\nResults saved to {output_path}")

if __name__ == "__main__":
    main()