from typing import List, Dict, Optional
from pydantic import BaseModel

# Model for prompt templates
class PromptTemplate(BaseModel):
    system_template: str
    user_template: str

# Model for user identification
class UserIdentification(BaseModel):
    user_id: str

# Extended query request with optional user ID
class QueryRequest(BaseModel):
    session_id: str
    query: str
    user_id: Optional[str] = None

class QueryResponse(BaseModel):
    response: str
    session_id: str

# Document summary models
class DocumentSummaryRequest(BaseModel):
    session_id: str
    user_id: Optional[str] = None

class DocumentSummaryResponse(BaseModel):
    keyTopics: List[str]
    entities: List[str]
    wordCloudData: List[dict]
    documentStructure: List[dict]

# Quiz models
class QuizQuestion(BaseModel):
    id: str
    text: str
    options: List[str]
    correctAnswer: str

class GenerateQuizRequest(BaseModel):
    session_id: str
    num_questions: int = 5
    user_id: Optional[str] = None

class GenerateQuizResponse(BaseModel):
    questions: List[QuizQuestion] 