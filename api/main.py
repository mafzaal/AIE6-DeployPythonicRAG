import os
import tempfile
import shutil
import json
import uuid
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
Use the following context to answer a users question. If you cannot find the answer in the context, say you don't know the answer.

IMPORTANT: Format your response with your thinking process and final answer as follows:
1. First provide your reasoning process inside <think>...</think> tags
2. Then provide your final answer, either:
   - Using <answer>...</answer> tags (preferred)
   - Or simply provide the answer directly after your thinking section

For example:
<think>
I'm analyzing the question in relation to the context. The question asks about X, and in the context I see information about Y and Z, which relates to X in the following way...
</think>
<answer>
Based on the context, the answer is...
</answer>

Or alternatively:
<think>
I'm analyzing the question in relation to the context. The question asks about X, and in the context I see information about Y and Z, which relates to X in the following way...
</think>
Based on the context, the answer is...
"""
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

class DocumentSummaryRequest(BaseModel):
    session_id: str

class DocumentSummaryResponse(BaseModel):
    keyTopics: List[str]
    entities: List[str]
    wordCloudData: List[dict]
    documentStructure: List[dict]

class QuizQuestion(BaseModel):
    id: str
    text: str
    options: List[str]
    correctAnswer: str

class GenerateQuizRequest(BaseModel):
    session_id: str
    num_questions: int = 5

class GenerateQuizResponse(BaseModel):
    questions: List[QuizQuestion]

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

@app.post("/document-summary", response_model=DocumentSummaryResponse)
async def get_document_summary(request: DocumentSummaryRequest):
    session_id = request.session_id
    
    # Check if session exists
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found. Please upload a document first.")
    
    # Get the retrieval pipeline from the session
    retrieval_pipeline = user_sessions[session_id]
    
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
    
    # Check if session exists
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found. Please upload a document first.")
    
    # Get the retrieval pipeline from the session
    retrieval_pipeline = user_sessions[session_id]
    
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
        response = await llm.acreate_single_response(quiz_prompt)
        
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