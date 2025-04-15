import time
import uuid
from fastapi import Request, Response
from .prompts import user_prompts, DEFAULT_SYSTEM_TEMPLATE, DEFAULT_USER_TEMPLATE

def get_or_create_user_id(request: Request, response: Response) -> str:
    """
    Get or create a user ID without using cookies to support HuggingFace deployments
    
    Args:
        request: FastAPI request object
        response: FastAPI response object
        
    Returns:
        User ID (either existing or newly created)
    """
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