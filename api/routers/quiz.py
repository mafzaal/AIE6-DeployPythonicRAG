import uuid
import json
import re
from fastapi import APIRouter, HTTPException

from api.models.pydantic_models import GenerateQuizRequest, GenerateQuizResponse, QuizQuestion
from api.utils.prompts import get_user_prompts
from api.utils.quiz import generate_fallback_questions
from api.routers.document import user_sessions

router = APIRouter()

@router.post("/generate-quiz", response_model=GenerateQuizResponse)
async def generate_quiz(request: GenerateQuizRequest):
    """
    Generate a quiz based on the document content
    
    Args:
        request: Request containing session_id, num_questions, and optional user_id
        
    Returns:
        GenerateQuizResponse with quiz questions
    """
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
        response = await llm.acreate_single_response(quiz_prompt)
        
        # Parse the JSON
        # Find JSON content (sometimes the LLM adds extra text)
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