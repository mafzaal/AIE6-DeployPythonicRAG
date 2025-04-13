import uuid
from typing import List
from api.models.pydantic_models import QuizQuestion

def generate_fallback_questions(num_questions: int) -> List[QuizQuestion]:
    """
    Generate generic fallback questions when LLM fails
    
    Args:
        num_questions: Number of questions to generate
        
    Returns:
        List of fallback QuizQuestion objects
    """
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