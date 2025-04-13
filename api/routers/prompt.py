from fastapi import APIRouter, Request, Response
from typing import Optional

from api.models.pydantic_models import PromptTemplate
from api.utils.user import get_or_create_user_id
from api.utils.prompts import get_user_prompts, user_prompts, DEFAULT_SYSTEM_TEMPLATE, DEFAULT_USER_TEMPLATE

router = APIRouter()

@router.get("/prompts")
async def get_prompts(
    request: Request,
    response: Response,
    user_id: Optional[str] = None
):
    """
    Get the user's prompt templates
    
    Args:
        request: FastAPI request object
        response: FastAPI response object
        user_id: User ID (optional)
        
    Returns:
        Dictionary with user ID and prompt templates
    """
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

@router.post("/prompts")
async def update_prompts(
    prompt_template: PromptTemplate,
    request: Request,
    response: Response,
    user_id: Optional[str] = None
):
    """
    Update the user's prompt templates
    
    Args:
        prompt_template: New prompt templates
        request: FastAPI request object
        response: FastAPI response object
        user_id: User ID (optional)
        
    Returns:
        Dictionary with status, user ID, and message
    """
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

@router.post("/prompts/reset")
async def reset_prompts(
    request: Request,
    response: Response,
    user_id: Optional[str] = None
):
    """
    Reset the user's prompt templates to default
    
    Args:
        request: FastAPI request object
        response: FastAPI response object
        user_id: User ID (optional)
        
    Returns:
        Dictionary with status, user ID, and message
    """
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