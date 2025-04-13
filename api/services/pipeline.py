from typing import List, Dict, Any
from aimakerspace.openai_utils.prompts import SystemRolePrompt, UserRolePrompt
from aimakerspace.openai_utils.chatmodel import ChatOpenAI
from aimakerspace.vectordatabase import VectorDatabase

class RetrievalAugmentedQAPipeline:
    def __init__(self, llm: ChatOpenAI, vector_db_retriever: VectorDatabase, 
                system_template: str, 
                user_template: str) -> None:
        self.llm = llm
        self.vector_db_retriever = vector_db_retriever
        self.system_template = system_template
        self.user_template = user_template
        self.system_role_prompt = SystemRolePrompt(system_template)
        self.user_role_prompt = UserRolePrompt(user_template)

    def update_templates(self, system_template: str, user_template: str):
        """Update prompt templates"""
        self.system_template = system_template
        self.user_template = user_template
        self.system_role_prompt = SystemRolePrompt(system_template)
        self.user_role_prompt = UserRolePrompt(user_template)

    async def arun_pipeline(self, user_query: str):
        context_list = self.vector_db_retriever.search_by_text(user_query, k=4)

        context_prompt = ""
        for context in context_list:
            context_prompt += context[0] + "\n"

        formatted_system_prompt = self.system_role_prompt.create_message()
        formatted_user_prompt = self.user_role_prompt.create_message(
            question=user_query, context=context_prompt
        )

        async def generate_response():
            async for chunk in self.llm.astream([formatted_system_prompt, formatted_user_prompt]):
                yield chunk

        return {"response": generate_response(), "context": context_list} 