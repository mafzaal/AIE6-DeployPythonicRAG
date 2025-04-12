import os
import tempfile
import shutil
from typing import List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from aimakerspace.text_utils import CharacterTextSplitter, TextFileLoader, PDFLoader
from aimakerspace.openai_utils.prompts import (
    UserRolePrompt,
    SystemRolePrompt
)
from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.openai_utils.chatmodel import ChatOpenAI

app = FastAPI()

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

# Define prompt templates (same as in the original app)
system_template = """\
Use the following context to answer a users question. If you cannot find the answer in the context, say you don't know the answer."""
system_role_prompt = SystemRolePrompt(system_template)

user_prompt_template = """\
Context:
{context}

Question:
{question}
"""
user_role_prompt = UserRolePrompt(user_prompt_template)

class QueryRequest(BaseModel):
    session_id: str
    query: str

class QueryResponse(BaseModel):
    response: str
    session_id: str

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), session_id: str = Form(...)):
    if file.content_type not in ["text/plain", "application/pdf"]:
        raise HTTPException(status_code=400, detail="Only text and PDF files are supported")
    
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
            
            # Create the retrieval pipeline
            retrieval_pipeline = RetrievalAugmentedQAPipeline(
                vector_db_retriever=vector_db,
                llm=chat_openai
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
            
            return {
                "status": "success", 
                "message": f"Processed {file.filename}", 
                "session_id": session_id,
                "document_description": document_description,
                "suggested_questions": suggested_questions
            }
            
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                print(f"Error cleaning up temporary file: {e}")

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    session_id = request.session_id
    
    # Check if session exists
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found. Please upload a document first.")
    
    # Get the retrieval pipeline from the session
    retrieval_pipeline = user_sessions[session_id]
    
    # Run the query
    result = await retrieval_pipeline.arun_pipeline(request.query)
    
    # Process the result and return the response
    response_text = ""
    async for chunk in result["response"]:
        response_text += chunk
    
    return {"response": response_text, "session_id": session_id}

# Serve the frontend
@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.get("/{path:path}")
async def catch_all(path: str):
    if os.path.exists(f"static/{path}"):
        return FileResponse(f"static/{path}")
    return FileResponse("static/index.html")

class RetrievalAugmentedQAPipeline:
    def __init__(self, llm: ChatOpenAI, vector_db_retriever: VectorDatabase) -> None:
        self.llm = llm
        self.vector_db_retriever = vector_db_retriever

    async def arun_pipeline(self, user_query: str):
        context_list = self.vector_db_retriever.search_by_text(user_query, k=4)

        context_prompt = ""
        for context in context_list:
            context_prompt += context[0] + "\n"

        formatted_system_prompt = system_role_prompt.create_message()
        formatted_user_prompt = user_role_prompt.create_message(
            question=user_query, context=context_prompt
        )

        async def generate_response():
            async for chunk in self.llm.astream([formatted_system_prompt, formatted_user_prompt]):
                yield chunk

        return {"response": generate_response(), "context": context_list}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 