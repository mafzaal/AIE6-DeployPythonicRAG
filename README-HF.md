# 🧠 RAG Chat with Document Dashboard & Quiz

This application combines document analysis with interactive Q&A and knowledge quizzes.

## 📑 Features

- **Document Analysis:** Upload any PDF or text file
- **Interactive Q&A:** Ask questions about your document content
- **Document Dashboard:** View key topics, entities, word cloud and document structure
- **Knowledge Quiz:** Test your understanding with auto-generated quizzes
- **AI Reasoning:** See the AI's thinking process with expandable sections

## 🚀 Getting Started

1. **Upload a Document:** Click the upload button and select a PDF or text file
2. **Ask Questions:** Type questions about the document in the chat
3. **Explore Dashboard:** Browse the document summary dashboard to see insights
4. **Take a Quiz:** After asking a few questions, try the quiz feature (or type "quiz me")

## 💡 Example Questions

- "What are the main topics in this document?"
- "Can you summarize the key points?"
- "Explain the relationship between X and Y mentioned in the document."
- "Quiz me about this document's content."

## 🔧 Settings

- Toggle the dashboard visibility in the settings (gear icon)
- Switch between light and dark mode (sun/moon icon)

## 🛠️ Technical Details

This application uses a Retrieval-Augmented Generation (RAG) system with:
- Document chunking and vector embeddings
- Semantic search for relevant context
- LLM for generating detailed, accurate responses
- Separate AI reasoning and answer sections

Created with FastAPI, React, and OpenAI. 