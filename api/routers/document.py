import os
import tempfile
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Response
from typing import Dict, List

from aimakerspace.text_utils import CharacterTextSplitter, TextFileLoader, PDFLoader
from aimakerspace.openai_utils.chatmodel import ChatOpenAI
from aimakerspace.vectordatabase import VectorDatabase

from api.models.pydantic_models import DocumentSummaryRequest, DocumentSummaryResponse
from api.services.pipeline import RetrievalAugmentedQAPipeline
from api.utils.user import get_or_create_user_id
from api.utils.prompts import get_user_prompts

# Storage for user sessions
user_sessions = {}

# Initialize text splitter
text_splitter = CharacterTextSplitter()

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...), 
    session_id: str = Form(...),
    request: Request = None,
    response: Response = None
):
    """
    Upload and process a document file
    
    Args:
        file: Uploaded file
        session_id: Session ID for this document
        request: FastAPI request object
        response: FastAPI response object
    
    Returns:
        Dictionary with file processing results
    """
    if file.content_type not in ["text/plain", "application/pdf"]:
        raise HTTPException(status_code=400, detail="Only text and PDF files are supported")
    
    # Get or create user ID
    user_id = get_or_create_user_id(request, response) if request and response else None
    
    # Create a temporary file
    suffix = f".{file.filename.split('.')[-1]}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        # Copy the uploaded file content to the temporary file
        file_content = await file.read()
        temp_file.write(file_content)
        temp_file.flush()
        
        # Create appropriate loader
        if file.filename.lower().endswith('.pdf'):
            loader = PDFLoader(temp_file.name)
        else:
            loader = TextFileLoader(temp_file.name)
        
        try:
            # Load and process the documents
            documents = loader.load_documents()
            texts = text_splitter.split_texts(documents)
            
            # Create vector database
            vector_db = VectorDatabase()
            vector_db = await vector_db.abuild_from_list(texts)
            
            # Create chat model
            chat_openai = ChatOpenAI()
            
            # Get user prompts
            user_prompt_templates = get_user_prompts(user_id) if user_id else {
                "system_template": DEFAULT_SYSTEM_TEMPLATE,
                "user_template": DEFAULT_USER_TEMPLATE
            }
            
            # Create the retrieval pipeline with user-specific prompts
            retrieval_pipeline = RetrievalAugmentedQAPipeline(
                vector_db_retriever=vector_db,
                llm=chat_openai,
                system_template=user_prompt_templates["system_template"],
                user_template=user_prompt_templates["user_template"]
            )
            
            # Store the retrieval pipeline in the user session
            user_sessions[session_id] = retrieval_pipeline
            
            # Generate document description and suggested questions
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
            description_response = await chat_openai.acreate_single_response(description_prompt)
            document_description = description_response.strip()
            
            # Get suggested questions
            questions_response = await chat_openai.acreate_single_response(questions_prompt)
            
            # Try to parse the questions as JSON, or extract them as best as possible
            try:
                import json
                suggested_questions = json.loads(questions_response)
            except:
                # Extract questions with a fallback method
                import re
                questions = re.findall(r'["\']([^"\']+)["\']', questions_response)
                if not questions or len(questions) < 3:
                    questions = [q.strip() for q in questions_response.split("\n") if "?" in q]
                if not questions or len(questions) < 3:
                    questions = ["What is the main topic of this document?", 
                                "What are the key points discussed in the document?", 
                                "How can I apply the information in this document?"]
                suggested_questions = questions[:3]
            
            result = {
                "status": "success", 
                "message": f"Processed {file.filename}", 
                "session_id": session_id,
                "document_description": document_description,
                "suggested_questions": suggested_questions
            }
            
            # Add user_id to result if available
            if user_id:
                result["user_id"] = user_id
                
            return result
            
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                print(f"Error cleaning up temporary file: {e}")

@router.post("/document-summary", response_model=DocumentSummaryResponse)
async def get_document_summary(request: DocumentSummaryRequest):
    """
    Get a summary of the document
    
    Args:
        request: Request containing session_id and optional user_id
        
    Returns:
        DocumentSummaryResponse with topics, entities, word cloud data, and structure
    """
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
        response = await llm.acreate_single_response(summary_prompt)
        
        # Parse the JSON
        # Find JSON content (sometimes the LLM adds extra text)
        import re
        import json
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