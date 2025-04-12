# RAG Chat Application - Hugging Face Deployment

This document provides instructions for deploying the RAG Chat Application on Hugging Face Spaces.

## Overview

This RAG (Retrieval-Augmented Generation) Chat application allows users to:
- Upload documents (PDF/text)
- Ask questions about the uploaded documents
- View a document summary dashboard with key topics, word cloud, and document structure
- Take quizzes to test knowledge about the document content

## Features

- **Document Summary Dashboard:** Visual summaries of document content
- **Interactive Chat:** Ask questions about the uploaded documents
- **Knowledge Quiz:** Test your understanding with automatically generated quizzes
- **Thinking/Answer Format:** See the AI's reasoning process with expandable "thinking" sections

## Deployment Instructions

### Option 1: Deploy with Docker (Recommended)

1. Create a new Hugging Face Space:
   - Go to [huggingface.co/spaces](https://huggingface.co/spaces)
   - Click "Create new Space"
   - Select "Docker" as the Space SDK
   - Name your space and configure visibility settings

2. Upload the application files:
   - Use Git to push the code to your Hugging Face Space repository
   - Make sure to include the Dockerfile, which is already configured for Hugging Face

3. Set environment variables:
   - Go to your Space settings
   - Add the following environment variable:
     - `OPENAI_API_KEY`: Your OpenAI API key

4. Hugging Face will automatically build and deploy the Docker container.

### Option 2: Manual Deployment

If you prefer to customize the deployment:

1. Fork this repository
2. Create a new Hugging Face Space with Docker SDK
3. Connect your GitHub repository to the Hugging Face Space
4. Add your OpenAI API key in the Space settings
5. Hugging Face will build and deploy your application

## Usage

1. Open your deployed application in Hugging Face Spaces
2. Upload a document (PDF or text)
3. Ask questions about the document content
4. Explore the document summary dashboard
5. After asking a few questions, try the quiz feature

## Configuration

You can customize your deployment by modifying:
- `Dockerfile` - Container configuration
- `api/main.py` - Backend API endpoints
- `app/frontend/src/` - Frontend React components

## Troubleshooting

If you encounter issues:
1. Check that your OpenAI API key is valid and properly set in the Space settings
2. Verify that your Space has sufficient resources allocated
3. Check the Space logs for any errors
4. For larger documents, you may need to increase the Space's resource allocation

## Contributing

Contributions are welcome! Feel free to submit pull requests or issues. 