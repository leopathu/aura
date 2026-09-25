from app.models import AIProvider
from app.core.crypto import decrypt_secret
from app.models_ai.base import LLMProvider
from app.models_ai.providers import (
    OpenAICompatibleProvider,
    AnthropicProvider,
    OllamaProvider,
    MockAIProvider,
)

def get_llm_provider(provider: AIProvider) -> LLMProvider:
    provider_type = (provider.provider_type or "MOCK").upper()
    api_key = decrypt_secret(provider.encrypted_api_key) if provider.encrypted_api_key else ""

    if provider_type in ["OPENAI", "CUSTOM_OPENAI"]:
        return OpenAICompatibleProvider(api_key=api_key, base_url=provider.base_url)
    elif provider_type == "ANTHROPIC":
        return AnthropicProvider(api_key=api_key, base_url=provider.base_url)
    elif provider_type == "OLLAMA":
        return OllamaProvider(base_url=provider.base_url)
    else:
        return MockAIProvider(api_key=api_key, base_url=provider.base_url)
