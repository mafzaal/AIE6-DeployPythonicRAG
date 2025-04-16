"""
RAG Evaluation Script using LangSmith

This script fetches and analyzes RAG runs from LangSmith to evaluate
context relevance and response quality.

Usage:
    python scripts/eval_rag.py --project pythonic-rag --limit 100
"""

import os
import sys
import argparse
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from langsmith import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if LangSmith API key is set
if not os.getenv("LANGSMITH_API_KEY"):
    print("Error: LANGSMITH_API_KEY environment variable not set.")
    print("Please set it in your .env file or environment.")
    sys.exit(1)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Evaluate RAG performance using LangSmith")
    parser.add_argument("--project", type=str, default="pythonic-rag", 
                        help="LangSmith project name")
    parser.add_argument("--limit", type=int, default=100, 
                        help="Maximum number of runs to evaluate")
    parser.add_argument("--days", type=int, default=7, 
                        help="Number of days to look back")
    parser.add_argument("--output", type=str, default="rag_evaluation.csv",
                        help="Output file for evaluation results")
    return parser.parse_args()

def get_runs(client: Client, project_name: str, limit: int, days: int):
    """Fetch RAG runs from LangSmith."""
    # Calculate start time
    start_time = datetime.now() - timedelta(days=days)
    
    # Fetch retrieval runs
    retrieval_runs = list(client.list_runs(
        project_name=project_name,
        start_time=start_time,
        tags=["retrieval"],
        limit=limit
    ))
    print(f"Found {len(retrieval_runs)} retrieval runs")
    
    # Fetch generation runs
    generation_runs = list(client.list_runs(
        project_name=project_name,
        start_time=start_time,
        tags=["generation"],
        limit=limit
    ))
    print(f"Found {len(generation_runs)} generation runs")
    
    return retrieval_runs, generation_runs

def analyze_retrieval_run(run: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a retrieval run."""
    run_id = run.id
    query = run.inputs.get("query", "")
    
    # Get retrieved documents
    try:
        documents = run.outputs.get("retrieved_documents", [])
        doc_count = len(documents)
    except:
        documents = []
        doc_count = 0
    
    # Get metadata
    metadata = run.metadata or {}
    user_id = metadata.get("user_id", "unknown")
    session_id = metadata.get("session_id", "unknown")
    
    return {
        "run_id": run_id,
        "query": query,
        "doc_count": doc_count,
        "user_id": user_id,
        "session_id": session_id,
        "timestamp": run.start_time,
    }

def analyze_generation_run(run: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a generation run."""
    run_id = run.id
    query = run.inputs.get("query", "")
    context = run.inputs.get("context", "")
    response = run.outputs.get("response", "")
    
    # Get metadata
    metadata = run.metadata or {}
    user_id = metadata.get("user_id", "unknown")
    session_id = metadata.get("session_id", "unknown")
    parent_run_id = metadata.get("parent_run_id", None)
    
    # Calculate metrics
    context_length = len(context)
    response_length = len(response)
    
    return {
        "run_id": run_id,
        "parent_run_id": parent_run_id,
        "query": query,
        "context_length": context_length,
        "response_length": response_length,
        "user_id": user_id,
        "session_id": session_id,
        "timestamp": run.start_time,
    }

def evaluate_rag_performance(retrieval_runs, generation_runs):
    """Evaluate RAG performance using the fetched runs."""
    # Analyze retrieval runs
    retrieval_data = [analyze_retrieval_run(run) for run in retrieval_runs]
    retrieval_df = pd.DataFrame(retrieval_data)
    
    # Analyze generation runs
    generation_data = [analyze_generation_run(run) for run in generation_runs]
    generation_df = pd.DataFrame(generation_data)
    
    # Match retrieval and generation runs
    if not generation_df.empty and not retrieval_df.empty and 'parent_run_id' in generation_df.columns:
        # Create a dictionary mapping run_id to row index
        retrieval_idx = {run_id: i for i, run_id in enumerate(retrieval_df['run_id'])}
        
        # Add a column for matched flag
        generation_df['has_retrieval'] = False
        
        # For each generation run, find the matching retrieval run
        for i, row in generation_df.iterrows():
            if row['parent_run_id'] in retrieval_idx:
                generation_df.at[i, 'has_retrieval'] = True
                # Add more metrics here as needed
    
    # Print summary statistics
    print("\n--- RAG Performance Summary ---")
    print(f"Total Retrieval Runs: {len(retrieval_df)}")
    print(f"Total Generation Runs: {len(generation_df)}")
    
    if not retrieval_df.empty and 'doc_count' in retrieval_df.columns:
        print(f"Average Documents Retrieved: {retrieval_df['doc_count'].mean():.2f}")
    
    if not generation_df.empty:
        if 'context_length' in generation_df.columns:
            print(f"Average Context Length: {generation_df['context_length'].mean():.2f} characters")
        if 'response_length' in generation_df.columns:
            print(f"Average Response Length: {generation_df['response_length'].mean():.2f} characters")
        if 'has_retrieval' in generation_df.columns:
            matched = generation_df['has_retrieval'].sum()
            print(f"Generation Runs with Matched Retrieval: {matched} ({matched/len(generation_df)*100:.2f}%)")
    
    return retrieval_df, generation_df

def main():
    """Main function."""
    args = parse_args()
    
    # Initialize LangSmith client
    client = Client()
    
    print(f"Fetching runs from project '{args.project}' (limit: {args.limit}, days: {args.days})...")
    retrieval_runs, generation_runs = get_runs(client, args.project, args.limit, args.days)
    
    if not retrieval_runs and not generation_runs:
        print("No runs found. Check your project name and timeframe.")
        sys.exit(0)
    
    # Evaluate RAG performance
    retrieval_df, generation_df = evaluate_rag_performance(retrieval_runs, generation_runs)
    
    # Save to CSV
    if not retrieval_df.empty:
        retrieval_df.to_csv(f"retrieval_{args.output}", index=False)
        print(f"Saved retrieval data to retrieval_{args.output}")
    
    if not generation_df.empty:
        generation_df.to_csv(f"generation_{args.output}", index=False)
        print(f"Saved generation data to generation_{args.output}")
    
    print("\nEvaluation complete!")
    print("\nNext steps:")
    print("1. Review the CSV files for detailed analysis")
    print("2. Set up LangSmith feedback datasets for systematic evaluation")
    print("3. Use the data to improve prompts and retrieval performance")

if __name__ == "__main__":
    main() 