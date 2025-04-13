from fastapi import APIRouter, HTTPException, Request, Response
from typing import Optional, Dict, Any, List
from uuid import uuid4
import logging

from api.models.pydantic_models import Session
from api.utils.user import get_or_create_user_id
from api.utils.session import user_sessions, initialize_session

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/sessions", response_model=Session)
async def create_session(
    request: Request,
    response: Response,
    user_id: Optional[str] = None,
    collection_name: Optional[str] = None
):
    """
    Create a new chat session
    
    Args:
        request: FastAPI request object
        response: FastAPI response object
        user_id: User ID (optional)
        collection_name: Vector store collection name (optional)
        
    Returns:
        Session: The created session
    """
    # Get or create user ID if not provided
    if not user_id:
        user_id = get_or_create_user_id(request, response)
    
    # Generate a new session ID
    session_id = str(uuid4())
    
    # Initialize the session
    try:
        initialize_session(session_id, user_id, collection_name)
        
        return Session(
            id=session_id,
            user_id=user_id,
            collection_name=collection_name or "default"
        )
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

@router.get("/sessions", response_model=List[Session])
async def get_sessions(
    request: Request,
    response: Response,
    user_id: Optional[str] = None
):
    """
    Get all sessions for a user
    
    Args:
        request: FastAPI request object
        response: FastAPI response object
        user_id: User ID (optional)
        
    Returns:
        List[Session]: List of sessions
    """
    # Get or create user ID if not provided
    if not user_id:
        user_id = get_or_create_user_id(request, response)
    
    # Filter sessions by user ID
    user_session_list = []
    for session_id, session_data in user_sessions.items():
        if session_data.get("user_id") == user_id:
            user_session_list.append(Session(
                id=session_id,
                user_id=user_id,
                collection_name=session_data.get("collection_name", "default")
            ))
    
    return user_session_list

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    request: Request,
    response: Response,
    user_id: Optional[str] = None
):
    """
    Delete a session
    
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
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    # Validate user owns the session
    if user_sessions[session_id].get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this session")
    
    # Delete the session
    try:
        del user_sessions[session_id]
        return {
            "status": "success",
            "message": f"Session {session_id} deleted successfully"
        }
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}") 