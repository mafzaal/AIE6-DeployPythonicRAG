import os
import tempfile
import shutil
import json
import uuid
import time
import logging
import sys
import traceback
from typing import List, Dict, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Cookie, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
from langsmith.wrappers import wrap_openai

# Import and setup logging
from aimakerspace.vectordatabase import VectorDatabase
from api.logging_config import setup_logging
logger = setup_logging(level=logging.INFO)

from aimakerspace.text_utils import CharacterTextSplitter, TextFileLoader, PDFLoader
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from aimakerspace.qdrant_vectordb import QdrantVectorDatabase
from langchain_openai import ChatOpenAI
#from aimakerspace.openai_utils.chatmodel import ChatOpenAI

# API Version information
API_VERSION = "0.2.0"
BUILD_DATE = "2024-06-14"  # Update this when making significant changes

from .config import QDRANT_HOST, QDRANT_PORT, QDRANT_GRPC_PORT, QDRANT_PREFER_GRPC, QDRANT_COLLECTION, QDRANT_IN_MEMORY 

app = FastAPI(
    title="Quick Understand API",
    description="RAG-based question answering API for document understanding",
    version=API_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize text splitter
text_splitter = CharacterTextSplitter()

# Dictionary to store user sessions
user_sessions = {}

# Dictionary to store user-specific prompts
user_prompts = {}

# Import default prompt templates from prompts.py
from .utils.prompts import DEFAULT_SYSTEM_TEMPLATE, DEFAULT_USER_TEMPLATE

from api.models.pydantic_models import (
    PromptTemplate,
    QueryRequest,
    QueryResponse,
    DocumentSummaryRequest,
    DocumentSummaryResponse,
    QuizQuestion,
    GenerateQuizRequest,
    GenerateQuizResponse
)

# Helper function to get or create a user ID
def get_or_create_user_id(request: Request, response: Response) -> str:
    # Try to get user ID from header first
    user_id = request.headers.get("X-User-ID")
    
    # Then try to get from query parameter
    if not user_id:
        user_id = request.query_params.get("user_id")
    
    # If no user ID exists, create a new one
    if not user_id:
        user_id = str(uuid.uuid4())
        # Initialize with default prompts
        if user_id not in user_prompts:
            user_prompts[user_id] = {
                "system_template": DEFAULT_SYSTEM_TEMPLATE,
                "user_template": DEFAULT_USER_TEMPLATE
            }
    
    return user_id

# Get prompts for a specific user
def get_user_prompts(user_id: str) -> Dict[str, str]:
    if user_id not in user_prompts:
        # Initialize with default prompts if not exists
        user_prompts[user_id] = {
            "system_template": DEFAULT_SYSTEM_TEMPLATE,
            "user_template": DEFAULT_USER_TEMPLATE
        }
    
    return user_prompts[user_id]

# Helper function to extend OpenAI client with needed methods
async def acreate_single_response(client, prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content

# Helper function to provide streaming capability for OpenAI client
async def astream_openai(client, messages):
    # Convert LangChain message format to OpenAI format
    openai_messages = []
    for message in messages:
        role = "user"
        if hasattr(message, "type"):
            if message.type == "system":
                role = "system"
            elif message.type == "human":
                role = "user"
            elif message.type == "ai":
                role = "assistant"
        
        openai_messages.append({
            "role": role,
            "content": message.content
        })
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=openai_messages,
        temperature=0.7,
        stream=True,
    )
    
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...), 
    session_id: str = Form(...),
    request: Request = None,
    response: Response = None
):
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[Request:{request_id}] Upload request received - session_id={session_id}, file={file.filename}")
    
    if file.content_type not in ["text/plain", "application/pdf"]:
        logger.warning(f"[Request:{request_id}] Unsupported file type: {file.content_type}")
        raise HTTPException(status_code=400, detail="Only text and PDF files are supported")
    
    # Get or create user ID
    user_id = get_or_create_user_id(request, response) if request and response else None
    if user_id:
        logger.info(f"[Request:{request_id}] User ID: {user_id}")
    
    # Track overall processing time
    upload_start_time = time.time()
    
    # Create a temporary file
    suffix = f".{file.filename.split('.')[-1]}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        # Copy the uploaded file content to the temporary file
        logger.info(f"[Request:{request_id}] Reading file content")
        file_content = await file.read()
        file_size = len(file_content)
        temp_file.write(file_content)
        temp_file.flush()
        logger.info(f"[Request:{request_id}] File saved to temp location, size: {file_size} bytes")
        
        # Create appropriate loader
        if file.filename.lower().endswith('.pdf'):
            logger.info(f"[Request:{request_id}] Using PDF loader")
            loader = PDFLoader(temp_file.name)
        else:
            logger.info(f"[Request:{request_id}] Using text loader")
            loader = TextFileLoader(temp_file.name)
        
        try:
            # Load and process the documents
            logger.info(f"[Request:{request_id}] Loading documents")
            doc_load_start = time.time()
            documents = loader.load_documents()
            doc_load_time = time.time() - doc_load_start
            logger.info(f"[Request:{request_id}] Documents loaded in {doc_load_time:.4f} seconds, count: {len(documents)}")
            
            # Split documents into chunks
            logger.info(f"[Request:{request_id}] Splitting documents into chunks")
            split_start = time.time()
            texts = text_splitter.split_texts(documents)
            split_time = time.time() - split_start
            logger.info(f"[Request:{request_id}] Document splitting completed in {split_time:.4f} seconds, chunk count: {len(texts)}")
            
            # Log information about chunk lengths
            if texts:
                chunk_lengths = [len(t) for t in texts]
                logger.info(f"[Request:{request_id}] Chunk statistics: min={min(chunk_lengths)}, max={max(chunk_lengths)}, avg={sum(chunk_lengths)/len(chunk_lengths):.2f} chars")
            
            # Create vector database
            logger.info(f"[Request:{request_id}] Creating vector database: {QDRANT_COLLECTION}_{session_id}")
            vector_start = time.time()
            vector_db = VectorDatabase()
            
            # Build the vector database
            logger.info(f"[Request:{request_id}] Building vector database with {len(texts)} chunks")
            vector_db = await vector_db.abuild_from_list(texts)
            vector_time = time.time() - vector_start
            logger.info(f"[Request:{request_id}] Vector database creation completed in {vector_time:.4f} seconds")
            
            # Create chat model
            logger.info(f"[Request:{request_id}] Creating chat model")
            

            openai_client = wrap_openai(OpenAI())
            
            # Get user prompts
            user_prompt_templates = get_user_prompts(user_id) if user_id else {
                "system_template": DEFAULT_SYSTEM_TEMPLATE,
                "user_template": DEFAULT_USER_TEMPLATE
            }
            
            # Create the retrieval pipeline with user-specific prompts
            pipeline_start = time.time()
            logger.info(f"[Request:{request_id}] Creating retrieval pipeline")
            retrieval_pipeline = RetrievalAugmentedQAPipeline(
                vector_db_retriever=vector_db,
                llm=openai_client,
                system_template=user_prompt_templates["system_template"],
                user_template=user_prompt_templates["user_template"]
            )
            pipeline_time = time.time() - pipeline_start
            logger.info(f"[Request:{request_id}] Retrieval pipeline created in {pipeline_time:.4f} seconds")
            
            # Store the retrieval pipeline in the user session
            user_sessions[session_id] = retrieval_pipeline
            logger.info(f"[Request:{request_id}] Retrieval pipeline stored in session {session_id}")
            
            # Generate document description and suggested questions
            logger.info(f"[Request:{request_id}] Generating document description and questions")
            summary_start = time.time()
            doc_content = "\n".join(texts[:5])  # Use first few chunks for summary
            
            description_prompt = f"""
            Please provide a brief description of this document in 2-3 sentences:
            {doc_content}
            """
            
            questions_prompt = f"""
            Based on this document content, please suggest 3 specific questions that would be informative to ask:
            {doc_content}
            
            Format your response as a JSON array with 3 question strings.
            """
            
            # Get document description
            logger.info(f"[Request:{request_id}] Generating document description")
            description_response = await acreate_single_response(openai_client, description_prompt)
            document_description = description_response.strip()
            
            # Get suggested questions
            logger.info(f"[Request:{request_id}] Generating suggested questions")
            questions_response = await acreate_single_response(openai_client, questions_prompt)
            
            # Try to parse the questions as JSON, or extract them as best as possible
            try:
                import json
                suggested_questions = json.loads(questions_response)
                logger.info(f"[Request:{request_id}] Successfully parsed suggested questions as JSON")
            except:
                # Extract questions with a fallback method
                logger.info(f"[Request:{request_id}] Parsing JSON failed, using fallback method")
                import re
                questions = re.findall(r'["\']([^"\']+)["\']', questions_response)
                if not questions or len(questions) < 3:
                    questions = [q.strip() for q in questions_response.split("\n") if "?" in q]
                    logger.info(f"[Request:{request_id}] Extracted questions using line splitting: {len(questions)} found")
                if not questions or len(questions) < 3:
                    logger.info(f"[Request:{request_id}] No questions found, using default questions")
                    questions = ["What is the main topic of this document?", 
                                "What are the key points discussed in the document?", 
                                "How can I apply the information in this document?"]
                suggested_questions = questions[:3]
            
            summary_time = time.time() - summary_start
            logger.info(f"[Request:{request_id}] Document summary generation completed in {summary_time:.4f} seconds")
            
            total_time = time.time() - upload_start_time
            logger.info(f"[Request:{request_id}] Total processing time: {total_time:.4f} seconds")
            
            result = {
                "status": "success", 
                "message": f"Processed {file.filename}", 
                "session_id": session_id,
                "document_description": document_description,
                "suggested_questions": suggested_questions,
                "processing_stats": {
                    "total_time": total_time,
                    "doc_load_time": doc_load_time,
                    "split_time": split_time,
                    "vector_time": vector_time,
                    "chunk_count": len(texts)
                }
            }
            
            # Add user_id to result if available
            if user_id:
                result["user_id"] = user_id
            
            logger.info(f"[Request:{request_id}] Upload processing completed successfully")    
            return result
            
        except Exception as e:
            error_time = time.time() - upload_start_time
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            error_location = f"{fname}:{exc_tb.tb_lineno}"
            error_traceback = "".join(traceback.format_tb(exc_tb))
            logger.error(f"[Request:{request_id}] Error processing upload after {error_time:.4f} seconds at {error_location}: {str(e)}")
            logger.error(f"[Request:{request_id}] Traceback: {error_traceback}")
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)} at {error_location}")
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file.name)
                logger.info(f"[Request:{request_id}] Temp file cleaned up")
            except Exception as e:
                logger.error(f"[Request:{request_id}] Error cleaning up temporary file: {e}")

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    session_id = request.session_id
    user_id = request.user_id
    request_id = str(uuid.uuid4())[:8]
    
    logger.info(f"[Request:{request_id}] Query request received - session_id={session_id}, user_id={user_id}, query='{request.query}'")
    
    # Check if session exists
    if session_id not in user_sessions:
        logger.warning(f"[Request:{request_id}] Session not found: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found. Please upload a document first.")
    
    # Get the retrieval pipeline from the session
    retrieval_pipeline = user_sessions[session_id]
    logger.info(f"[Request:{request_id}] Retrieved pipeline for session {session_id}")
    
    # Update prompts if user_id is provided and different from current
    if user_id and retrieval_pipeline.system_template != get_user_prompts(user_id)["system_template"]:
        logger.info(f"[Request:{request_id}] Updating prompt templates for user {user_id}")
        user_prompt_templates = get_user_prompts(user_id)
        retrieval_pipeline.update_templates(
            user_prompt_templates["system_template"],
            user_prompt_templates["user_template"]
        )
    
    # Run the query
    start_time = time.time()
    logger.info(f"[Request:{request_id}] Executing RAG pipeline")
    result = await retrieval_pipeline.arun_pipeline(request.query, user_id, session_id)
    
    # Process the result and return the response
    response_text = ""
    token_count = 0
    async for chunk in result["response"]:
        response_text += chunk
        token_count += 1
    
    process_time = time.time() - start_time
    
    # Log detailed information about the response
    logger.info(f"[Request:{request_id}] Request processed in {process_time:.4f} seconds, response length: {len(response_text)} chars, {token_count} tokens")
    
    # Extract and log metrics from result
    if "search_time" in result:
        logger.info(f"[Request:{request_id}] Vector search time: {result['search_time']:.4f} seconds")
    if "context_length" in result:
        logger.info(f"[Request:{request_id}] Context length: {result['context_length']} characters")
    
    # Log context scores information
    context_list = result.get("context", [])
    if context_list:
        scores = [score for _, score in context_list]
        logger.info(f"[Request:{request_id}] Context similarity scores: min={min(scores):.4f}, max={max(scores):.4f}, avg={sum(scores)/len(scores):.4f}")
    
    return {"response": response_text, "session_id": session_id}

@app.post("/stream")
async def stream_query(request: QueryRequest):
    session_id = request.session_id
    user_id = request.user_id
    request_id = str(uuid.uuid4())[:8]
    
    logger.info(f"[Request:{request_id}] Stream query request received - session_id={session_id}, user_id={user_id}, query='{request.query}'")
    
    # Check if session exists
    if session_id not in user_sessions:
        logger.warning(f"[Request:{request_id}] Session not found: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found. Please upload a document first.")
    
    # Get the retrieval pipeline from the session
    retrieval_pipeline = user_sessions[session_id]
    logger.info(f"[Request:{request_id}] Retrieved pipeline for session {session_id}")
    
    # Update prompts if user_id is provided and different from current
    if user_id and retrieval_pipeline.system_template != get_user_prompts(user_id)["system_template"]:
        logger.info(f"[Request:{request_id}] Updating prompt templates for user {user_id}")
        user_prompt_templates = get_user_prompts(user_id)
        retrieval_pipeline.update_templates(
            user_prompt_templates["system_template"],
            user_prompt_templates["user_template"]
        )
    
    # Run the query
    start_time = time.time()
    logger.info(f"[Request:{request_id}] Executing RAG pipeline for streaming")
    result = await retrieval_pipeline.arun_pipeline(request.query, user_id, session_id)
    
    # Extract context for logging
    context_list = result.get("context", [])
    scores = [score for _, score in context_list] if context_list else []
    if scores:
        logger.info(f"[Request:{request_id}] Context similarity scores: min={min(scores):.4f}, max={max(scores):.4f}, avg={sum(scores)/len(scores):.4f}")
    
    async def generate():
        token_count = 0
        chunk_count = 0
        response_buffer = ""
        async for chunk in result["response"]:
            token_count += 1
            chunk_count += 1
            response_buffer += chunk
            
            # Collect 5 tokens before sending or at the end of the stream
            if token_count % 5 == 0 or chunk == "":
                yield f"data: {json.dumps({'text': response_buffer})}\n\n"
                response_buffer = ""
        
        # Send any remaining text
        if response_buffer:
            yield f"data: {json.dumps({'text': response_buffer})}\n\n"
        
        # Send end of stream marker
        completion_time = time.time() - start_time
        logger.info(f"[Request:{request_id}] Streaming completed in {completion_time:.4f} seconds, sent {token_count} tokens in {chunk_count} chunks")
        yield f"data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/stream")
async def stream_query_get(
    session_id: str, 
    query: str, 
    user_id: Optional[str] = None,
    request: Request = None,
    response: Response = None
):
    request_id = str(uuid.uuid4())[:8]
    
    # Get or create user ID if not provided
    if request and response and not user_id:
        user_id = get_or_create_user_id(request, response)
    
    logger.info(f"[Request:{request_id}] Stream GET query received - session_id={session_id}, user_id={user_id}, query='{query}'")
    
    # Check if session exists
    if session_id not in user_sessions:
        logger.warning(f"[Request:{request_id}] Session not found: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found. Please upload a document first.")
    
    # Get the retrieval pipeline from the session
    retrieval_pipeline = user_sessions[session_id]
    logger.info(f"[Request:{request_id}] Retrieved pipeline for session {session_id}")
    
    # Update prompts if user_id is provided and different from current
    if user_id and retrieval_pipeline.system_template != get_user_prompts(user_id)["system_template"]:
        logger.info(f"[Request:{request_id}] Updating prompt templates for user {user_id}")
        user_prompt_templates = get_user_prompts(user_id)
        retrieval_pipeline.update_templates(
            user_prompt_templates["system_template"],
            user_prompt_templates["user_template"]
        )
    
    # Run the query
    start_time = time.time()
    logger.info(f"[Request:{request_id}] Executing RAG pipeline for streaming (GET)")
    result = await retrieval_pipeline.arun_pipeline(query, user_id, session_id)
    
    # Extract context for logging
    context_list = result.get("context", [])
    scores = [score for _, score in context_list] if context_list else []
    if scores:
        logger.info(f"[Request:{request_id}] Context similarity scores: min={min(scores):.4f}, max={max(scores):.4f}, avg={sum(scores)/len(scores):.4f}")
    
    async def generate():
        token_count = 0
        chunk_count = 0
        response_buffer = ""
        async for chunk in result["response"]:
            token_count += 1
            chunk_count += 1
            response_buffer += chunk
            
            # Collect 5 tokens before sending or at the end of the stream
            if token_count % 5 == 0 or chunk == "":
                yield f"data: {json.dumps({'text': response_buffer})}\n\n"
                response_buffer = ""
        
        # Send any remaining text
        if response_buffer:
            yield f"data: {json.dumps({'text': response_buffer})}\n\n"
        
        # Send end of stream marker
        completion_time = time.time() - start_time
        logger.info(f"[Request:{request_id}] Streaming completed in {completion_time:.4f} seconds, sent {token_count} tokens in {chunk_count} chunks")
        yield f"data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/document-summary", response_model=DocumentSummaryResponse)
async def get_document_summary(request: DocumentSummaryRequest):
    session_id = request.session_id
    user_id = request.user_id
    
    # Check if session exists
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found. Please upload a document first.")
    
    # Get the retrieval pipeline from the session
    retrieval_pipeline = user_sessions[session_id]
    
    # Update prompts if user_id is provided and different from current
    if user_id and retrieval_pipeline.system_template != get_user_prompts(user_id)["system_template"]:
        user_prompt_templates = get_user_prompts(user_id)
        retrieval_pipeline.update_templates(
            user_prompt_templates["system_template"],
            user_prompt_templates["user_template"]
        )
    
    # Get access to the document content
    vector_db = retrieval_pipeline.vector_db_retriever
    
    # We'll use all the text chunks to create a comprehensive summary
    # Get all text chunks from the vector store
    all_texts = vector_db.get_all_texts()
    
    # Combine a sample of the texts (to avoid hitting token limits)
    sample_texts = all_texts[:10] if len(all_texts) > 10 else all_texts
    doc_content = "\n".join(sample_texts)
    
    # Create the LLM summary prompt
    summary_prompt = f"""
    Analyze the following document content and generate a structured summary in JSON format:
    
    ```
    {doc_content}
    ```
    
    Return ONLY a JSON object with the following structure:
    
    {{
      "keyTopics": [list of 5-7 key topics in the document],
      "entities": [list of 5-8 important named entities such as organizations, technologies, or people],
      "wordCloudData": [
        {{ "text": "word1", "value": frequency_score }},
        {{ "text": "word2", "value": frequency_score }},
        ...
      ],
      "documentStructure": [
        {{ 
          "title": "Section title",
          "subsections": ["Subsection1", "Subsection2", ...] 
        }},
        ...
      ]
    }}
    
    The wordCloudData should contain 15-20 important terms with their relative frequency scores (higher numbers = more important/frequent).
    The documentStructure should reflect the hierarchical organization of the document with main sections and their subsections.
    """
    
    # Get LLM response
    try:
        llm = retrieval_pipeline.llm
        response = await acreate_single_response(llm, summary_prompt)
        
        # Parse the JSON
        # Find JSON content (sometimes the LLM adds extra text)
        import re
        json_match = re.search(r'({[\s\S]*})', response)
        
        if json_match:
            json_str = json_match.group(1)
            summary_data = json.loads(json_str)
        else:
            # If no JSON found, create a basic structure with an error message
            summary_data = {
                "keyTopics": ["Error parsing document structure"],
                "entities": ["Please try again"],
                "wordCloudData": [{"text": "Error", "value": 50}],
                "documentStructure": [{"title": "Document structure unavailable", "subsections": []}]
            }
            
        # Ensure the response has all required fields
        if "keyTopics" not in summary_data:
            summary_data["keyTopics"] = ["Topic extraction failed"]
        if "entities" not in summary_data:
            summary_data["entities"] = ["Entity extraction failed"]
        if "wordCloudData" not in summary_data:
            summary_data["wordCloudData"] = [{"text": "Data", "value": 50}]
        if "documentStructure" not in summary_data:
            summary_data["documentStructure"] = [{"title": "Structure unavailable", "subsections": []}]
            
        return summary_data
        
    except Exception as e:
        # Return a fallback summary on error
        return {
            "keyTopics": ["Error analyzing document"],
            "entities": ["Try refreshing the page"],
            "wordCloudData": [
                {"text": "Error", "value": 60},
                {"text": "Document", "value": 40},
                {"text": "Analysis", "value": 30}
            ],
            "documentStructure": [
                {"title": "Error in document analysis", "subsections": ["Please try again"]}
            ]
        }

@app.post("/generate-quiz", response_model=GenerateQuizResponse)
async def generate_quiz(request: GenerateQuizRequest):
    session_id = request.session_id
    num_questions = min(request.num_questions, 10)  # Limit to max 10 questions
    user_id = request.user_id
    
    # Check if session exists
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found. Please upload a document first.")
    
    # Get the retrieval pipeline from the session
    retrieval_pipeline = user_sessions[session_id]
    
    # Update prompts if user_id is provided and different from current
    if user_id and retrieval_pipeline.system_template != get_user_prompts(user_id)["system_template"]:
        user_prompt_templates = get_user_prompts(user_id)
        retrieval_pipeline.update_templates(
            user_prompt_templates["system_template"],
            user_prompt_templates["user_template"]
        )
    
    # Get access to the document content
    vector_db = retrieval_pipeline.vector_db_retriever
    
    # We'll use all the text chunks to create comprehensive quiz questions
    # Get all text chunks from the vector store
    all_texts = vector_db.get_all_texts()
    
    # Combine a sample of the texts (to avoid hitting token limits)
    sample_texts = all_texts[:15] if len(all_texts) > 15 else all_texts
    doc_content = "\n".join(sample_texts)
    
    # Create the LLM quiz generation prompt
    quiz_prompt = f"""
    Based on the following document content, generate {num_questions} multiple-choice quiz questions to test the reader's understanding:
    
    ```
    {doc_content}
    ```
    
    For each question:
    1. Create a clear, specific question about key information in the document
    2. Provide exactly 4 answer options (A, B, C, D)
    3. Clearly indicate which option is correct
    4. Make sure distractors (wrong answers) are plausible but clearly incorrect
    
    Return ONLY a JSON object with the following structure:
    
    {{
      "questions": [
        {{
          "id": "unique_id",
          "text": "question text",
          "options": ["option A", "option B", "option C", "option D"],
          "correctAnswer": "correct option text"
        }},
        ...
      ]
    }}
    
    The questions should cover different aspects of the document and test genuine understanding.
    """
    
    # Get LLM response
    try:
        llm = retrieval_pipeline.llm
        response = await acreate_single_response(llm, quiz_prompt)
        
        # Parse the JSON
        # Find JSON content (sometimes the LLM adds extra text)
        import re
        json_match = re.search(r'({[\s\S]*})', response)
        
        if json_match:
            json_str = json_match.group(1)
            quiz_data = json.loads(json_str)
            
            # Validate and clean the questions
            questions = []
            for q in quiz_data.get("questions", []):
                # Ensure each question has a unique ID
                if "id" not in q or not q["id"]:
                    q["id"] = str(uuid.uuid4())
                
                # Verify the question has all required fields
                if "text" in q and "options" in q and "correctAnswer" in q:
                    # Verify correctAnswer is in options
                    if q["correctAnswer"] in q["options"]:
                        questions.append(QuizQuestion(
                            id=q["id"],
                            text=q["text"],
                            options=q["options"],
                            correctAnswer=q["correctAnswer"]
                        ))
            
            # If no valid questions were found or not enough questions, create fallback
            if len(questions) < min(3, num_questions):
                questions = generate_fallback_questions(num_questions)
                
            return {"questions": questions[:num_questions]}
        else:
            # If no JSON found, return fallback questions
            return {"questions": generate_fallback_questions(num_questions)}
            
    except Exception as e:
        print(f"Error generating quiz: {e}")
        # Return fallback questions on error
        return {"questions": generate_fallback_questions(num_questions)}

def generate_fallback_questions(num_questions: int) -> List[QuizQuestion]:
    """Generate generic fallback questions when LLM fails"""
    fallback_questions = [
        QuizQuestion(
            id=str(uuid.uuid4()),
            text="What is the main purpose of a RAG (Retrieval-Augmented Generation) system?",
            options=[
                "To generate random text without meaning",
                "To retrieve documents from a database only",
                "To combine document retrieval with language model generation",
                "To replace human writing entirely"
            ],
            correctAnswer="To combine document retrieval with language model generation"
        ),
        QuizQuestion(
            id=str(uuid.uuid4()),
            text="Which component is NOT typically part of a RAG system?",
            options=[
                "Vector database",
                "Language model",
                "Blockchain ledger",
                "Text splitter"
            ],
            correctAnswer="Blockchain ledger"
        ),
        QuizQuestion(
            id=str(uuid.uuid4()),
            text="What is the benefit of using RAG over a standalone language model?",
            options=[
                "It's always faster",
                "It provides more up-to-date and accurate information",
                "It uses less computational resources",
                "It requires no training data"
            ],
            correctAnswer="It provides more up-to-date and accurate information"
        ),
        QuizQuestion(
            id=str(uuid.uuid4()),
            text="What is a vector embedding in the context of RAG?",
            options=[
                "A mathematical representation of text in multidimensional space",
                "A form of data compression",
                "A type of encryption",
                "A physical server component"
            ],
            correctAnswer="A mathematical representation of text in multidimensional space"
        ),
        QuizQuestion(
            id=str(uuid.uuid4()),
            text="How does a RAG system determine which text chunks are relevant to a query?",
            options=[
                "Random selection",
                "Semantic similarity between query and text embeddings",
                "Alphabetical ordering",
                "Document recency only"
            ],
            correctAnswer="Semantic similarity between query and text embeddings"
        )
    ]
    return fallback_questions[:num_questions]

# New endpoint to get user prompts
@app.get("/prompts")
async def get_prompts(
    request: Request,
    response: Response,
    user_id: Optional[str] = None
):
    # Get or create user ID if not provided
    if not user_id:
        user_id = get_or_create_user_id(request, response)
    
    # Get user prompts
    prompts = get_user_prompts(user_id)
    
    return {
        "user_id": user_id,
        "system_template": prompts["system_template"],
        "user_template": prompts["user_template"]
    }

# New endpoint to update user prompts
@app.post("/prompts")
async def update_prompts(
    prompt_template: PromptTemplate,
    request: Request,
    response: Response,
    user_id: Optional[str] = None
):
    # Get or create user ID if not provided
    if not user_id:
        user_id = get_or_create_user_id(request, response)
    
    # Update prompts
    user_prompts[user_id] = {
        "system_template": prompt_template.system_template,
        "user_template": prompt_template.user_template
    }
    
    return {
        "status": "success",
        "user_id": user_id,
        "message": "Prompts updated successfully"
    }

# Reset user prompts to default
@app.post("/prompts/reset")
async def reset_prompts(
    request: Request,
    response: Response,
    user_id: Optional[str] = None
):
    # Get or create user ID if not provided
    if not user_id:
        user_id = get_or_create_user_id(request, response)
    
    # Reset to defaults
    user_prompts[user_id] = {
        "system_template": DEFAULT_SYSTEM_TEMPLATE,
        "user_template": DEFAULT_USER_TEMPLATE
    }
    
    return {
        "status": "success",
        "user_id": user_id,
        "message": "Prompts reset to default successfully"
    }

@app.get("/identify")
async def identify_user(request: Request, response: Response):
    user_id = get_or_create_user_id(request, response)
    return {"user_id": user_id}

# Serve the frontend
@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.get("/version")
async def get_version():
    return {
        "api_version": API_VERSION,
        "build_date": BUILD_DATE,
        "status": "operational"
    }

@app.get("/{path:path}")
async def catch_all(path: str):
    if os.path.exists(f"static/{path}"):
        return FileResponse(f"static/{path}")
    return FileResponse("static/index.html")

class RetrievalAugmentedQAPipeline:
    def __init__(self, llm: ChatOpenAI, vector_db_retriever: QdrantVectorDatabase, 
                system_template: str = DEFAULT_SYSTEM_TEMPLATE, 
                user_template: str = DEFAULT_USER_TEMPLATE) -> None:
        self.llm = llm
        self.vector_db_retriever = vector_db_retriever
        self.system_template = system_template
        self.user_template = user_template
        self.system_prompt_template = SystemMessagePromptTemplate.from_template(system_template)
        self.human_prompt_template = HumanMessagePromptTemplate.from_template(user_template)
        self.chat_prompt_template = ChatPromptTemplate.from_messages([
            self.system_prompt_template,
            self.human_prompt_template
        ])
        
        # Import LangSmith utilities
        try:
            from api.utils.langsmith_utils import langsmith_tracer
            self.langsmith_tracer = langsmith_tracer
            logger.info("LangSmith tracer initialized in RAG pipeline")
        except ImportError:
            logger.warning("LangSmith utils not available, tracing disabled")
            self.langsmith_tracer = None

    def update_templates(self, system_template: str, user_template: str):
        """Update prompt templates"""
        self.system_template = system_template
        self.user_template = user_template
        self.system_prompt_template = SystemMessagePromptTemplate.from_template(system_template)
        self.human_prompt_template = HumanMessagePromptTemplate.from_template(user_template)
        self.chat_prompt_template = ChatPromptTemplate.from_messages([
            self.system_prompt_template,
            self.human_prompt_template
        ])

    async def arun_pipeline(self, user_query: str, user_id: str = None, session_id: str = None):
        # Get context from vector database
        context_list = self.vector_db_retriever.search_by_text(user_query, k=4)
        
        # Log context retrieval to LangSmith if available
        retrieval_run_id = None
        if self.langsmith_tracer and self.langsmith_tracer.tracing_enabled and self.langsmith_tracer.client:
            # Add debug logging
            logger.info(f"Attempting to log retrieval to LangSmith. Tracer enabled: {self.langsmith_tracer.tracing_enabled}")
            try:
                retrieval_run_id = self.langsmith_tracer.log_retrieval(
                    query=user_query,
                    retrieved_documents=context_list,
                    user_id=user_id,
                    session_id=session_id
                )
                logger.info(f"Successfully logged retrieval to LangSmith with run_id: {retrieval_run_id}")
            except Exception as e:
                logger.error(f"Failed to log retrieval to LangSmith: {str(e)}")

        # Format context for prompt
        context_prompt = ""
        for context in context_list:
            context_prompt += context[0] + "\n"

        # Create messages using LangChain prompt templates
        messages = self.chat_prompt_template.format_messages(
            question=user_query, 
            context=context_prompt
        )

        async def generate_response():
            response_chunks = []
            # Use our custom streaming function
            async for chunk in astream_openai(self.llm, messages):
                response_chunks.append(chunk)
                yield chunk
            
            # Log generation to LangSmith if available
            if self.langsmith_tracer and self.langsmith_tracer.tracing_enabled and self.langsmith_tracer.client:
                try:
                    full_response = "".join(response_chunks)
                    self.langsmith_tracer.log_rag_generation(
                        query=user_query,
                        context=context_prompt,
                        response=full_response,
                        system_prompt=self.system_template,
                        user_prompt=self.user_template,
                        user_id=user_id,
                        session_id=session_id,
                        parent_run_id=retrieval_run_id
                    )
                    logger.info("Successfully logged generation to LangSmith")
                except Exception as e:
                    logger.error(f"Failed to log generation to LangSmith: {str(e)}")

        return {"response": generate_response(), "context": context_list}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 