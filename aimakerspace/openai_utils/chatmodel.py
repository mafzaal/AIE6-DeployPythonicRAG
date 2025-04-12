from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
import os

load_dotenv()


class ChatOpenAI:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key is None:
            raise ValueError("OPENAI_API_KEY is not set")

    def run(self, messages, text_only: bool = True, **kwargs):
        if not isinstance(messages, list):
            raise ValueError("messages must be a list")

        client = OpenAI()
        response = client.chat.completions.create(
            model=self.model_name, messages=messages, **kwargs
        )

        if text_only:
            return response.choices[0].message.content

        return response
    
    async def astream(self, messages, **kwargs):
        if not isinstance(messages, list):
            raise ValueError("messages must be a list")
        
        client = AsyncOpenAI()

        stream = await client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True,
            **kwargs
        )

        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content is not None:
                yield content
                
    async def acreate_single_response(self, prompt_text, **kwargs):
        """
        Create a single non-streamed response asynchronously.
        
        :param prompt_text: Text prompt as a string
        :param kwargs: Additional parameters to pass to the completion API
        :return: The text response
        """
        messages = [{"role": "user", "content": prompt_text}]
        
        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=False,
            **kwargs
        )
        
        return response.choices[0].message.content
