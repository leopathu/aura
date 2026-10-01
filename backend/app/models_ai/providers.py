import json
import httpx
from typing import List, Dict, Any, AsyncGenerator, Optional
from app.models_ai.base import LLMProvider

class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield delta
                        except Exception:
                            continue

    async def embed(
        self,
        texts: List[str],
        model: str = "text-embedding-3-small"
    ) -> List[List[float]]:
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "input": texts
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]

    async def get_available_models(self) -> List[str]:
        url = f"{self.base_url}/models"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return [m["id"] for m in data.get("data", []) if "id" in m]
        except Exception:
            pass
        return []


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = (base_url or "https://api.anthropic.com/v1").rstrip("/")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        system_prompt = ""
        user_messages = []
        for m in messages:
            if m["role"] == "system":
                system_prompt += m["content"] + "\n"
            else:
                user_messages.append({"role": m["role"], "content": m["content"]})

        payload = {
            "model": model,
            "messages": user_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            payload["system"] = system_prompt.strip()

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        # Simple stream fallback
        content = await self.chat(messages, model, temperature, max_tokens)
        chunk_size = 20
        for i in range(0, len(content), chunk_size):
            yield content[i:i + chunk_size]

    async def embed(
        self,
        texts: List[str],
        model: str = "text-embedding-3-small"
    ) -> List[List[float]]:
        # Anthropic doesn't have native embedding endpoint; fallback to mock hash embedding
        return MockAIProvider().embed(texts, model)


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or "http://localhost:11434").rstrip("/")

    async def check_health(self) -> Dict[str, Any]:
        """Checks if Ollama daemon is reachable and lists installed models."""
        url = f"{self.base_url}/api/tags"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") or m.get("model") for m in data.get("models", []) if m.get("name") or m.get("model")]
                return {"online": True, "models": models}
            return {"online": False, "models": [], "status_code": resp.status_code}

    async def get_available_models(self) -> List[str]:
        """Fetch models pulled locally into Ollama via /api/tags."""
        try:
            health = await self.check_health()
            return health.get("models", [])
        except Exception:
            return []

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature}
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                resp = await client.post(url, json=payload)
            except httpx.ConnectError:
                raise ConnectionError(f"Could not connect to Ollama at '{self.base_url}'. Ensure Ollama daemon is running (`ollama serve`).")

            if resp.status_code == 404:
                err_text = ""
                try:
                    err_text = resp.json().get("error", "")
                except Exception:
                    pass
                msg = err_text or f"Model '{model}' not found in Ollama."
                raise ValueError(f"{msg} Run `ollama pull {model}` in your terminal to download it.")
            elif resp.is_error:
                err_text = ""
                try:
                    err_text = resp.json().get("error", resp.text)
                except Exception:
                    err_text = resp.text
                raise RuntimeError(f"Ollama error ({resp.status_code}): {err_text}")

            data = resp.json()
            return data["message"]["content"]

    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": temperature}
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code == 404:
                        err_text = ""
                        try:
                            body = await response.aread()
                            err_text = json.loads(body).get("error", "")
                        except Exception:
                            pass
                        msg = err_text or f"Model '{model}' not found in Ollama."
                        raise ValueError(f"{msg} Run `ollama pull {model}` to download it.")
                    elif response.is_error:
                        raise RuntimeError(f"Ollama stream error (HTTP {response.status_code})")

                    async for line in response.aiter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                yield chunk["message"]["content"]
                            except Exception:
                                continue
            except httpx.ConnectError:
                raise ConnectionError(f"Could not connect to Ollama at '{self.base_url}'. Ensure Ollama daemon is running (`ollama serve`).")

    async def embed(
        self,
        texts: List[str],
        model: str = "nomic-embed-text"
    ) -> List[List[float]]:
        url = f"{self.base_url}/api/embeddings"
        embeddings = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            for text in texts:
                try:
                    resp = await client.post(url, json={"model": model, "prompt": text})
                except httpx.ConnectError:
                    raise ConnectionError(f"Could not connect to Ollama at '{self.base_url}'. Ensure Ollama daemon is running.")

                if resp.status_code == 404:
                    raise ValueError(f"Embedding model '{model}' not found in Ollama. Run `ollama pull {model}` first.")
                resp.raise_for_status()
                embeddings.append(resp.json()["embedding"])
        return embeddings


class MockAIProvider(LLMProvider):
    """
    Deterministic Mock AI Provider for offline testing, local dev,
    and agent verification without external API keys.
    """
    def __init__(self, api_key: str = "mock-key", base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        last_user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        # Provide helpful responses tailored to queries
        if "revenue" in last_user_msg.lower() or "sales" in last_user_msg.lower():
            return "Based on the sales database analysis, total revenue for the current fiscal period reached ₹4.82 Cr, representing a 14.3% growth over the previous period."
        elif "leave" in last_user_msg.lower() or "policy" in last_user_msg.lower():
            return "According to the employee handbook, employees are entitled to 20 days of paid annual leave, 10 days of sick leave, and standard statutory public holidays."
        elif "report" in last_user_msg.lower():
            return "# Executive Performance Report\n\n## Summary\nAll key performance metrics demonstrated positive momentum across divisions."
        return f"Processed inquiry regarding: '{last_user_msg[:60]}...'. All data has been verified against active organization security policies."

    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        full_text = await self.chat(messages, model, temperature, max_tokens)
        words = full_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")

    async def embed(
        self,
        texts: List[str],
        model: str = "mock-embedding"
    ) -> List[List[float]]:
        # Generate pseudo-embeddings based on deterministic hash vector of length 128
        import hashlib
        result = []
        for text in texts:
            seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
            # Create a 128-dim normalized vector
            vec = [((seed >> (i % 32)) & 0xFF) / 255.0 for i in range(128)]
            norm = sum(x*x for x in vec) ** 0.5 or 1.0
            result.append([round(x / norm, 5) for x in vec])
        return result
