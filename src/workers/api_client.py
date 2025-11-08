"""OpenRouter API client with rate limit handling."""
import asyncio
import aiohttp
import json
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RateLimitTracker:
    """Track rate limits per model."""
    
    def __init__(self):
        self.limits: Dict[str, Dict[str, Any]] = {}
        self.lock = asyncio.Lock()
    
    async def update(self, model: str, headers: Dict[str, str]):
        """Update rate limit info from API response headers."""
        async with self.lock:
            if model not in self.limits:
                self.limits[model] = {
                    "remaining": None,
                    "limit": None,
                    "reset_at": None,
                    "retry_after": None,
                }
            
            if "x-ratelimit-remaining" in headers:
                try:
                    self.limits[model]["remaining"] = int(headers["x-ratelimit-remaining"])
                except ValueError:
                    pass
            
            if "x-ratelimit-limit" in headers:
                try:
                    self.limits[model]["limit"] = int(headers["x-ratelimit-limit"])
                except ValueError:
                    pass
            
            if "retry-after" in headers:
                try:
                    retry_seconds = int(headers["retry-after"])
                    self.limits[model]["retry_after"] = datetime.now() + timedelta(seconds=retry_seconds)
                except ValueError:
                    pass
    
    async def can_make_request(self, model: str) -> bool:
        """Check if we can make a request for this model."""
        async with self.lock:
            if model not in self.limits:
                return True
            
            limit_info = self.limits[model]
            
            # Check retry-after
            if limit_info["retry_after"] and datetime.now() < limit_info["retry_after"]:
                return False
            
            # Check remaining
            if limit_info["remaining"] is not None and limit_info["remaining"] <= 0:
                return False
            
            return True
    
    async def get_wait_time(self, model: str) -> float:
        """Get wait time in seconds before next request."""
        async with self.lock:
            if model not in self.limits:
                return 0.0
            
            limit_info = self.limits[model]
            
            if limit_info["retry_after"]:
                wait = (limit_info["retry_after"] - datetime.now()).total_seconds()
                return max(0.0, wait)
            
            return 0.0


class OpenRouterClient:
    """Async OpenRouter API client."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.rate_limiter = RateLimitTracker()
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/your-repo",
                "X-Title": "Training Data Generator",
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate(
        self,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        retries: int = 3,
    ) -> Dict[str, Any]:
        """Generate completion with retry logic."""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        # Wait if rate limited
        while not await self.rate_limiter.can_make_request(model):
            wait_time = await self.rate_limiter.get_wait_time(model)
            if wait_time > 0:
                logger.warning(f"Rate limited for {model}, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        last_error = None
        for attempt in range(retries):
            try:
                async with self.session.post(url, json=payload) as response:
                    # Update rate limits
                    await self.rate_limiter.update(model, dict(response.headers))
                    
                    if response.status == 429:
                        retry_after = response.headers.get("retry-after", "5")
                        wait_time = float(retry_after)
                        logger.warning(f"Rate limited (429), waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    if "choices" not in data or not data["choices"]:
                        raise ValueError("Invalid API response: no choices")
                    
                    return data
            
            except aiohttp.ClientError as e:
                last_error = e
                if attempt < retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Request failed (attempt {attempt + 1}/{retries}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    raise
        
        raise Exception(f"Failed after {retries} attempts: {last_error}")
    
    async def extract_text(self, response: Dict[str, Any]) -> str:
        """Extract text content from API response."""
        if "choices" not in response or not response["choices"]:
            raise ValueError("No choices in response")
        
        choice = response["choices"][0]
        if "message" not in choice:
            raise ValueError("No message in choice")
        
        message = choice["message"]
        if "content" not in message:
            raise ValueError("No content in message")
        
        return message["content"].strip()

