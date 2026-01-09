"""
LLM Service using LiteLLM for multi-model support
"""
from typing import List, Dict, Any, Optional
import litellm
from app.core.encryption import encryption_service

class LLMService:
    """Service for interacting with various LLM providers via LiteLLM."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Any:
        """Get chat completion from LLM."""
        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=messages,
                api_key=self.api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            return response
        except Exception as e:
            raise Exception(f"LLM request failed: {str(e)}")
    
    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ):
        """Stream chat completion from LLM."""
        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=messages,
                api_key=self.api_key,
                temperature=temperature,
                stream=True
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise Exception(f"LLM streaming failed: {str(e)}")
    
    @staticmethod
    def create_from_credential(encrypted_key: str, credential_type: str) -> "LLMService":
        """Create LLM service from encrypted credential."""
        api_key = encryption_service.decrypt(encrypted_key)
        
        # Map credential type to model
        model_map = {
            "openai": "gpt-4",
            "anthropic": "claude-3-sonnet-20240229",
            "gemini": "gemini/gemini-pro"
        }
        
        model = model_map.get(credential_type, "gpt-4")
        return LLMService(api_key=api_key, model=model)
