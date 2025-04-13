from fastapi import APIRouter, HTTPException, Request, Response, Depends, status
from typing import Optional, List, Dict, Any
import logging
import time
from pydantic import BaseModel
from uuid import uuid4

from api.models.pydantic_models import ChatRequest, ChatResponse
from api.utils.user import get_or_create_user_id
from api.utils.prompts import get_user_prompts
from api.utils.session import (
    get_session, 
    update_chat_history, 
    create_rag_chain
)

logger = logging.getLogger(__name__)
chat_router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    session_id: str
    message: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    response: str
    chat_history: List[Dict[str, str]]

@chat_router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    """
    Process a user chat message and return AI response
    
    Args:
        request: Chat request with session_id and message
        
    Returns:
        ChatResponse: Response with session_id, AI response, and chat history
    """
    session_id = request.session_id
    user_message = request.message
    
    # Validate session exists
    session = get_session(session_id)
    if not session:
        logger.error(f"Session {session_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    logger.info(f"Processing message for session {session_id}")
    
    # Create RAG chain if not exists
    if not session.get("rag_chain"):
        try:
            rag_chain = create_rag_chain(session_id)
        except Exception as e:
            logger.error(f"Failed to create RAG chain: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create conversation chain"
            )
    else:
        rag_chain = session["rag_chain"]
    
    # Process the message with the RAG chain
    try:
        # This is a placeholder - actual implementation would use the RAG chain
        ai_response = f"This is a response to: {user_message}"
        
        # Update chat history
        update_chat_history(session_id, user_message, ai_response)
        
        return ChatResponse(
            session_id=session_id,
            response=ai_response,
            chat_history=session["chat_history"]
        )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )

@chat_router.get("/{session_id}/history", response_model=List[Dict[str, str]])
async def get_chat_history(session_id: str):
    """
    Get chat history for a session
    
    Args:
        session_id: Session ID
        
    Returns:
        List: Chat history
    """
    session = get_session(session_id)
    if not session:
        logger.error(f"Session {session_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    return session.get("chat_history", [])

@chat_router.post("/reset-chat")
async def reset_chat(
    session_id: str,
    request: Request,
    response: Response,
    user_id: Optional[str] = None
):
    """
    Reset the chat history for a session
    
    Args:
        session_id: Session ID
        request: FastAPI request object
        response: FastAPI response object
        user_id: User ID (optional)
        
    Returns:
        Dictionary with status and message
    """
    # Get or create user ID if not provided
    if not user_id:
        user_id = get_or_create_user_id(request, response)
    
    # Validate session exists
    session = get_session(session_id)
    if not session:
        logger.error(f"Session {session_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Clear chat history
    session["chat_history"] = []
    
    return {
        "status": "success",
        "message": "Chat history reset successfully"
    } 