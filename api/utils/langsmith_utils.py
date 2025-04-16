import os
from typing import Dict, List, Any, Optional
from langsmith import Client
import logging
import traceback
import sys
import re
import requests
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

logger = logging.getLogger(__name__)

def validate_api_key(api_key):
    """Validate if the provided API key follows LangSmith format and can connect"""
    if not api_key:
        return False, "API key is empty or None"
    
    # Check format - LangSmith API keys typically start with "lsv2_"
    if not api_key.startswith("lsv2_"):
        return False, f"API key does not match expected format (should start with 'lsv2_'): {api_key[:5]}..."
    
    # Try a simple API call to validate
    try:
        endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(f"{endpoint}/projects", headers=headers, timeout=5)
        
        if response.status_code == 200:
            return True, "API key is valid"
        elif response.status_code == 401:
            return False, f"API key is invalid (401 Unauthorized): {api_key[:5]}..."
        else:
            return False, f"API error (status code {response.status_code})"
    except Exception as e:
        return False, f"Error validating API key: {str(e)}"

class LangSmithTracer:
    def __init__(self):
        """Initialize LangSmith tracer for evaluating context quality and prompts."""
        # Default to disabled for safety
        self.tracing_enabled = False
        self.client = None
        self.project_name = os.getenv("LANGSMITH_PROJECT", "pythonic-rag")
        
        # Initialize LangSmith client
        try:
            # Debug environment variables
            api_key = os.getenv("LANGSMITH_API_KEY")
            tracing_v2 = os.getenv("LANGCHAIN_TRACING_V2")
            tracing = os.getenv("LANGSMITH_TRACING")
            project = os.getenv("LANGSMITH_PROJECT")
            endpoint = os.getenv("LANGSMITH_ENDPOINT")
            
            logger.info(f"LangSmith Environment: LANGSMITH_API_KEY={'present' if api_key else 'missing'}, "
                        f"LANGCHAIN_TRACING_V2={tracing_v2}, LANGSMITH_TRACING={tracing}, "
                        f"LANGSMITH_PROJECT={project}, LANGSMITH_ENDPOINT={endpoint}")
            
            # Force-enable tracing if LANGSMITH_TRACING is true
            if tracing and tracing.lower() == "true":
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                tracing_v2 = "true"
            
            # Quick validation to avoid API calls if key is obviously invalid
            if not api_key or len(api_key) < 10:
                logger.warning("LangSmith API key missing or invalid. Tracing will be disabled.")
                return
                
            # Initialize client with explicit parameters
            self.client = Client()
            self.project_name = project or "pythonic-rag"
            self.tracing_enabled = tracing_v2 and tracing_v2.lower() == "true"
            
            # Try a test API call to confirm it works
            try:
                self.client.list_projects(limit=1)
                logger.info(f"LangSmith client initialized successfully with tracing_enabled={self.tracing_enabled}")
            except Exception as e:
                logger.error(f"LangSmith API test failed, disabling tracing: {str(e)}")
                self.tracing_enabled = False
                self.client = None
                
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger.error(f"Error initializing LangSmith client in {fname}, line {exc_tb.tb_lineno}: {str(e)}")
            logger.error(f"Exception type: {exc_type}, Traceback: {traceback.format_exc()}")
    
    def log_retrieval(self, 
                      query: str, 
                      retrieved_documents: List[Any], 
                      user_id: Optional[str] = None, 
                      session_id: Optional[str] = None) -> Optional[str]:
        """
        Log document retrieval to LangSmith for evaluation.
        
        Args:
            query: User query
            retrieved_documents: List of retrieved documents/contexts
            user_id: User identifier (optional)
            session_id: Session identifier (optional)
            
        Returns:
            run_id: The LangSmith run ID if tracing is enabled, None otherwise
        """
        if not self.tracing_enabled:
            return None
            
        try:
            # Create metadata
            metadata = {
                "user_id": user_id or "anonymous",
                "session_id": session_id or "unknown"
            }
            
            # Format retrieved documents for logging
            context_texts = []
            for doc in retrieved_documents:
                if isinstance(doc, tuple) and len(doc) > 0:
                    context_texts.append(doc[0])
                elif hasattr(doc, "page_content"):
                    context_texts.append(doc.page_content)
                else:
                    context_texts.append(str(doc))
            
            # Log the run
            run = self.client.run_create(
                name="Document Retrieval",
                inputs={"query": query},
                outputs={"retrieved_documents": context_texts},
                runtime={
                    "total_tokens": sum(len(text.split()) for text in context_texts)
                },
                project_name=self.project_name,
                tags=["retrieval"],
                metadata=metadata
            )
            
            logger.info(f"Logged retrieval run to LangSmith with ID: {run.id}")
            return run.id
            
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger.error(f"Error logging retrieval to LangSmith in {fname}, line {exc_tb.tb_lineno}: {str(e)}")
            return None
    
    def log_rag_generation(self, 
                          query: str, 
                          context: str, 
                          response: str,
                          system_prompt: str,
                          user_prompt: str,
                          user_id: Optional[str] = None,
                          session_id: Optional[str] = None,
                          parent_run_id: Optional[str] = None) -> Optional[str]:
        """
        Log RAG generation to LangSmith for evaluation.
        
        Args:
            query: User query
            context: Retrieved context
            response: Generated response
            system_prompt: System prompt template
            user_prompt: User prompt template
            user_id: User identifier (optional)
            session_id: Session identifier (optional)
            parent_run_id: Parent run ID for linking retrieval and generation (optional)
            
        Returns:
            run_id: The LangSmith run ID if tracing is enabled, None otherwise
        """
        if not self.tracing_enabled:
            return None
            
        try:
            # Create metadata
            metadata = {
                "user_id": user_id or "anonymous",
                "session_id": session_id or "unknown",
                "parent_run_id": parent_run_id
            }
            
            # Log the run
            run = self.client.run_create(
                name="RAG Generation",
                inputs={
                    "query": query,
                    "context": context,
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt
                },
                outputs={"response": response},
                project_name=self.project_name,
                tags=["generation"],
                metadata=metadata
            )
            
            logger.info(f"Logged generation run to LangSmith with ID: {run.id}")
            return run.id
            
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger.error(f"Error logging generation to LangSmith in {fname}, line {exc_tb.tb_lineno}: {str(e)}")
            return None

# Singleton instance for use throughout the app
langsmith_tracer = LangSmithTracer() 