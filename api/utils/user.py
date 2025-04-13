import time
import uuid
from fastapi import Request, Response
from .prompts import user_prompts, DEFAULT_SYSTEM_TEMPLATE, DEFAULT_USER_TEMPLATE

def get_or_create_user_id(request: Request, response: Response) -> str:
    """
    Get or create a user ID
    
    Args:
        request: FastAPI request object
        response: FastAPI response object
        
    Returns:
        User ID (either existing or newly created)
    """
    # Try to get user ID from cookie
    user_id = request.cookies.get("user_id")
    
    # If no user ID exists, create a new one
    if not user_id:
        user_id = str(uuid.uuid4())
        # Set cookie with long expiration (1 year)
        expires = int(time.time()) + 31536000  # 1 year in seconds
        response.set_cookie(
            key="user_id",
            value=user_id,
            expires=expires,
            path="/",
            httponly=True,
            samesite="lax"
        )
        
        # Initialize with default prompts
        user_prompts[user_id] = {
            "system_template": DEFAULT_SYSTEM_TEMPLATE,
            "user_template": DEFAULT_USER_TEMPLATE
        }
    
    return user_id 