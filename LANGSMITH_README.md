# LangSmith Integration for RAG Evaluation

This project uses LangSmith to evaluate prompt quality and context relevance in the RAG pipeline.

## Setup

1. Sign up for LangSmith at [smith.langchain.com](https://smith.langchain.com/)
2. Get your API key from the LangSmith dashboard
3. Update your `.env` file with the following:

```
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=your_api_key_here
LANGSMITH_PROJECT=pythonic-rag
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

## How It Works

The app has been integrated with LangSmith to track:

1. **Context Retrieval**: When the system retrieves documents from the vector database, it logs:
   - The user query
   - The retrieved documents
   - Metadata (user ID, session ID)

2. **RAG Generation**: When generating responses, it logs:
   - The user query
   - The context used
   - The system and user prompts
   - The generated response
   - Metadata linking to the retrieval step

All traces are linked using parent-child relationships, making it easy to analyze the entire RAG pipeline.

## Viewing Traces

1. Log in to [LangSmith](https://smith.langchain.com/)
2. Navigate to the `pythonic-rag` project (or whatever you named it in the `.env` file)
3. You'll see all traces organized by type (retrieval, generation)
4. Click on any trace to see details about inputs, outputs, and metadata

## Evaluating RAG Performance

We've included a utility script to help analyze your RAG performance:

```bash
python scripts/eval_rag.py --project pythonic-rag --limit 100 --days 7
```

This will:
- Fetch the last 100 runs from the past 7 days
- Analyze retrieval and generation performance
- Save the results to CSV files for further analysis
- Print a summary of key metrics

## Metrics to Monitor

1. **Retrieval Quality**:
   - Number of documents retrieved
   - Relevance of retrieved documents to the query

2. **Generation Quality**:
   - Response length
   - Context usage (how much of the context was used)
   - Response latency

## Tips for Improving RAG Performance

1. **Prompt Engineering**:
   - Use LangSmith to A/B test different prompt templates
   - Analyze which prompts lead to better context utilization

2. **Context Optimization**:
   - Experiment with different chunk sizes and overlap
   - Adjust the number of retrieved documents (k value)

3. **Model Selection**:
   - Compare performance across different models
   - Find the optimal trade-off between quality and latency

## Additional Resources

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [RAG Evaluation Guide](https://blog.langchain.dev/evaluating-rag-pipelines-with-ragas-and-langsmith/)
- [Prompt Engineering Best Practices](https://www.langchain.com/langsmith) 