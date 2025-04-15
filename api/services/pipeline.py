from typing import List, Dict, Any
import logging
import time
import json
from aimakerspace.openai_utils.prompts import SystemRolePrompt, UserRolePrompt
from aimakerspace.openai_utils.chatmodel import ChatOpenAI
from aimakerspace.qdrant_vectordb import QdrantVectorDatabase

# Create logger
logger = logging.getLogger(__name__)

class RetrievalAugmentedQAPipeline:
    def __init__(self, llm: ChatOpenAI, vector_db_retriever: QdrantVectorDatabase, 
                system_template: str, 
                user_template: str) -> None:
        self.llm = llm
        self.vector_db_retriever = vector_db_retriever
        self.system_template = system_template
        self.user_template = user_template
        self.system_role_prompt = SystemRolePrompt(system_template)
        self.user_role_prompt = UserRolePrompt(user_template)
        logger.info(f"RetrievalAugmentedQAPipeline initialized with vector DB: {self.vector_db_retriever.__class__.__name__}")
        
    def update_templates(self, system_template: str, user_template: str):
        """Update prompt templates"""
        logger.info("Updating prompt templates")
        self.system_template = system_template
        self.user_template = user_template
        self.system_role_prompt = SystemRolePrompt(system_template)
        self.user_role_prompt = UserRolePrompt(user_template)
        logger.info("Prompt templates updated successfully")

    async def arun_pipeline(self, user_query: str, user_id: str = None):
        """
        Run the RAG pipeline to answer a user query
        
        Args:
            user_query: The user's question
            user_id: Optional user ID for tracking in HuggingFace deployment
            
        Returns:
            Dictionary containing response generator and context
        """
        request_id = id(user_query)[:8] if id(user_query) else "unknown"
        logger.info(f"[Request:{request_id}] Starting RAG pipeline for user_id={user_id}, query='{user_query}'")
        
        # Time the vector search
        start_time = time.time()
        logger.info(f"[Request:{request_id}] Executing vector search with k=4")
        
        try:
            context_list = self.vector_db_retriever.search_by_text(user_query, k=4)
            search_time = time.time() - start_time
            
            # Log the search results
            logger.info(f"[Request:{request_id}] Vector search completed in {search_time:.4f} seconds")
            logger.info(f"[Request:{request_id}] Retrieved {len(context_list)} context chunks")
            
            # Log details about each retrieved chunk
            for i, (text, score) in enumerate(context_list):
                # Limit the logged text length for readability
                text_preview = text[:100] + "..." if len(text) > 100 else text
                text_preview = text_preview.replace("\n", " ")
                logger.info(f"[Request:{request_id}] Chunk {i+1}: score={score:.4f}, text='{text_preview}'")
            
            # Format context for prompt
            context_prompt = ""
            for context in context_list:
                context_prompt += context[0] + "\n"
            
            context_length = len(context_prompt)
            logger.info(f"[Request:{request_id}] Total context length: {context_length} characters")
            
            # Format prompts
            formatted_system_prompt = self.system_role_prompt.create_message()
            formatted_user_prompt = self.user_role_prompt.create_message(
                question=user_query, context=context_prompt
            )
            
            logger.info(f"[Request:{request_id}] Prompts formatted, generating response")
            
            # Create streaming response generator
            async def generate_response():
                response_start_time = time.time()
                token_count = 0
                async for chunk in self.llm.astream([formatted_system_prompt, formatted_user_prompt]):
                    token_count += 1
                    yield chunk
                response_time = time.time() - response_start_time
                logger.info(f"[Request:{request_id}] Response generation completed in {response_time:.4f} seconds, {token_count} tokens")
            
            # Create result object
            result = {
                "response": generate_response(), 
                "context": context_list,
                "search_time": search_time,
                "context_length": context_length
            }
            
            # Include user_id in result if provided (for HuggingFace deployment)
            if user_id:
                result["user_id"] = user_id
                
            logger.info(f"[Request:{request_id}] RAG pipeline execution successful")
            return result
            
        except Exception as e:
            error_time = time.time() - start_time
            logger.error(f"[Request:{request_id}] Error in RAG pipeline after {error_time:.4f} seconds: {str(e)}")
            raise 