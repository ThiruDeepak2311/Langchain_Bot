import cohere
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from functools import lru_cache
import traceback
import time
from datetime import datetime

from config import settings
from core.errors import LLMError

logger = logging.getLogger(__name__)

# Enhanced response cache with TTL
class ResponseCache:
    def __init__(self, max_size=500, ttl_seconds=3600):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.access_times = {}  # For LRU eviction
        self.lock = asyncio.Lock()  # For thread safety
    
    async def get(self, key):
        async with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if time.time() < entry["expires"]:
                    # Update access time for LRU
                    self.access_times[key] = time.time()
                    return entry["value"]
                else:
                    # Expired entry
                    del self.cache[key]
                    if key in self.access_times:
                        del self.access_times[key]
            return None
    
    async def set(self, key, value, ttl=None):
        async with self.lock:
            # Evict if we're at capacity
            if len(self.cache) >= self.max_size:
                self._evict_lru()
                
            ttl = ttl or self.ttl
            self.cache[key] = {
                "value": value,
                "expires": time.time() + ttl
            }
            self.access_times[key] = time.time()
    
    def _evict_lru(self):
        if not self.access_times:
            return
            
        # Find least recently used item
        lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
        del self.cache[lru_key]
        del self.access_times[lru_key]
    
    async def clear(self):
        async with self.lock:
            self.cache = {}
            self.access_times = {}

class RateLimiter:
    """
    Advanced rate limiter with token bucket algorithm
    """
    def __init__(self, rate=10, per=60, burst=20):
        self.rate = rate  # Tokens per period
        self.per = per    # Period in seconds
        self.burst = burst  # Max tokens at once
        self.tokens = burst  # Current tokens
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self, tokens=1):
        """
        Acquire tokens from the bucket, waiting if necessary
        """
        async with self.lock:
            # Refill tokens based on time elapsed
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.burst, self.tokens + elapsed * (self.rate / self.per))
            self.last_refill = now
            
            # If we don't have enough tokens, calculate wait time
            if self.tokens < tokens:
                # Calculate how long to wait for required tokens
                wait_time = (tokens - self.tokens) * (self.per / self.rate)
                logger.info(f"Rate limit hit, waiting {wait_time:.2f}s")
                
                # Return the wait time for the caller to handle
                return wait_time
            
            # We have enough tokens, consume them
            self.tokens -= tokens
            return 0  # No wait needed

class CohereClient:
    """
    Enhanced client for interacting with Cohere's LLM APIs
    """
    def __init__(self, api_key: str = settings.COHERE_API_KEY):
        self.client = cohere.Client(api_key)
        self.rate_limiter = RateLimiter(rate=20, per=60, burst=30)  # Adjust based on API limits
        self.cache = ResponseCache(max_size=500)
        self.retry_backoff = [1, 2, 4, 8]  # Exponential backoff for retries
        self.health_check()

    def health_check(self):
        """
        Perform a health check on startup to verify API connectivity
        """
        try:
            logger.info("Performing Cohere API health check...")
            # Simple ping to verify API key and connectivity
            start_time = time.time()
            self.client.chat(message="ping", model="command")
            duration = time.time() - start_time
            logger.info(f"Cohere API health check successful ({duration:.2f}s)")
        except Exception as e:
            logger.error(f"Cohere API health check failed: {str(e)}")
            logger.error("Proceeding with caution, API calls may fail")

    async def generate_text(
        self,
        prompt: str,
        model: str = "command",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        k: int = 0,
        stop_sequences: Optional[List[str]] = None,
        return_likelihoods: str = "NONE",
        truncate: str = "END",
        retry_on_error: bool = True,
        **kwargs
    ) -> str:
        """
        Generate text using Cohere's API with improved error handling and rate limiting
        """
        # Calculate rate limiting tokens (more complex prompts cost more)
        tokens = 1 + (len(prompt) // 1000)  # 1 token base + 1 per 1000 chars
        
        # Apply rate limiting
        wait_time = await self.rate_limiter.acquire(tokens)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
            
        # Check cache
        cache_key = f"gen_{prompt[:100]}_{model}_{max_tokens}_{temperature}"
        cached_response = await self.cache.get(cache_key)
        if cached_response:
            logger.info("Using cached response for text generation")
            return cached_response
        
        # Initialize retry counter
        retries = 0
        max_retries = len(self.retry_backoff) if retry_on_error else 0
        
        while True:
            try:
                # Run in a thread pool because Cohere's client is synchronous
                loop = asyncio.get_event_loop()
                logger.info(f"Generating text with Cohere model: {model}")
                start_time = time.time()
                
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.generate(
                        prompt=prompt,
                        model=model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        k=k,
                        stop_sequences=stop_sequences,
                        return_likelihoods=return_likelihoods,
                        truncate=truncate,
                        **kwargs
                    )
                )
                
                duration = time.time() - start_time
                logger.info(f"Cohere text generation completed in {duration:.2f}s")
                
                generated_text = response.generations[0].text
                
                # Cache the result - shorter TTL for high temperature
                ttl = 86400 if temperature < 0.4 else 3600  # 24h for deterministic, 1h for creative
                await self.cache.set(cache_key, generated_text, ttl)
                
                return generated_text
                
            except Exception as e:
                logger.error(f"Error calling Cohere API: {str(e)}")
                
                # Check if we should retry
                if retries < max_retries:
                    # Get backoff time for this retry
                    backoff = self.retry_backoff[retries]
                    retries += 1
                    
                    logger.info(f"Retrying after {backoff}s delay (attempt {retries}/{max_retries})...")
                    await asyncio.sleep(backoff)
                else:
                    # We've exhausted retries or retry was disabled
                    logger.error(f"All retries failed or retry disabled: {str(e)}")
                    logger.error(traceback.format_exc())
                    raise LLMError(message=f"Error generating text: {str(e)}")

    async def embed_text(
        self,
        texts: List[str],
        model: str = "embed-english-v3.0",
        truncate: str = "END"
    ) -> List[List[float]]:
        """
        Embed text using Cohere's API with improved error handling
        """
        # Calculate rate limiting tokens
        tokens = max(1, len(texts) // 5)  # 1 token per 5 texts
        
        # Apply rate limiting
        wait_time = await self.rate_limiter.acquire(tokens)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        
        # No caching for embeddings as they're usually used immediately
        
        try:
            # Run in a thread pool because Cohere's client is synchronous
            loop = asyncio.get_event_loop()
            logger.info(f"Embedding {len(texts)} texts with Cohere model: {model}")
            start_time = time.time()
            
            response = await loop.run_in_executor(
                None,
                lambda: self.client.embed(
                    texts=texts,
                    model=model,
                    truncate=truncate
                )
            )
            
            duration = time.time() - start_time
            logger.info(f"Cohere embedding completed in {duration:.2f}s")
            
            return response.embeddings
            
        except Exception as e:
            logger.error(f"Error calling Cohere API for embeddings: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Retry once for embeddings
            try:
                logger.info("Retrying embedding operation once...")
                await asyncio.sleep(2)  # Brief delay
                
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.embed(
                        texts=texts,
                        model=model,
                        truncate=truncate
                    )
                )
                
                return response.embeddings
                
            except Exception as retry_error:
                logger.error(f"Retry failed: {str(retry_error)}")
                raise LLMError(message=f"Error embedding text: {str(e)}")

    async def chat(
        self,
        message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        model: str = "command",
        temperature: float = 0.7,
        preamble: Optional[str] = None,
        connectors: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
        retry_on_error: bool = True,
        **kwargs
    ) -> str:
        """
        Enhanced chat with Cohere's chat API with improved error handling and streaming support
        """
        # Calculate rate limiting tokens (more complex messages and history cost more)
        message_tokens = 1 + (len(message) // 500)  # 1 token base + 1 per 500 chars
        history_tokens = 0
        if chat_history:
            history_chars = sum(len(msg.get('content', '')) for msg in chat_history)
            history_tokens = history_chars // 1000  # 1 token per 1000 chars of history
        
        tokens = message_tokens + history_tokens
        
        # Apply rate limiting
        wait_time = await self.rate_limiter.acquire(tokens)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        
        # Skip cache for streaming responses
        if not stream:
            # Create a cache key from the message and context
            history_str = ""
            if chat_history:
                for msg in chat_history[-3:]:  # Only use last 3 messages for cache key
                    history_str += f"{msg.get('role', '')}:{msg.get('content', '')[:20]};"
                    
            cache_key = f"chat_{message[:50]}_{history_str}_{model}_{temperature}"
            
            cached_response = await self.cache.get(cache_key)
            if cached_response:
                logger.info("Using cached response for chat")
                return cached_response
        
        # Prepare conversation history in Cohere format
        conversation = []
        if chat_history:
            for msg in chat_history:
                role = msg.get("role", "USER")
                conversation.append({
                    "role": role.upper(),
                    "message": msg.get("content", "")
                })
        
        # Initialize retry counter
        retries = 0
        max_retries = len(self.retry_backoff) if retry_on_error else 0
        
        while True:
            try:
                # Run in a thread pool because Cohere's client is synchronous
                loop = asyncio.get_event_loop()
                logger.info(f"Sending chat message to Cohere model: {model}")
                start_time = time.time()
                
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat(
                        message=message,
                        model=model,
                        temperature=temperature,
                        chat_history=conversation if conversation else None,
                        preamble=preamble,
                        connectors=connectors,
                        stream=stream,
                        **kwargs
                    )
                )
                
                duration = time.time() - start_time
                logger.info(f"Cohere chat completed in {duration:.2f}s")
                
                # For streaming responses
                if stream:
                    return response  # Return the stream object
                
                # For regular responses
                result = response.text
                
                # Cache the result only if not streaming
                if not stream:
                    # Lower TTL for higher temperatures
                    ttl = 86400 if temperature < 0.5 else 3600
                    await self.cache.set(cache_key, result, ttl)
                
                return result
                
            except Exception as e:
                logger.error(f"Error calling Cohere Chat API: {str(e)}")
                
                # Check if we should retry
                if retries < max_retries:
                    # Get backoff time for this retry
                    backoff = self.retry_backoff[retries]
                    retries += 1
                    
                    logger.info(f"Retrying chat after {backoff}s delay (attempt {retries}/{max_retries})...")
                    await asyncio.sleep(backoff)
                else:
                    # We've exhausted retries
                    logger.error(f"All retries failed: {str(e)}")
                    logger.error(traceback.format_exc())
                    
                    # Generate a generic fallback response based on message content
                    message_lower = message.lower()
                    for key, fallback in self._get_fallback_responses().items():
                        if key in message_lower:
                            return fallback
                    
                    # Default fallback
                    raise LLMError(message=f"Error in chat response: {str(e)}")

    def _get_fallback_responses(self) -> Dict[str, str]:
        """
        Generate contextual fallback responses for different topic areas
        """
        return {
            "sport": (
                "I know that sports are a popular topic. However, I'm having trouble accessing my knowledge "
                "services right now. Sports include activities like football, basketball, cricket, tennis, "
                "and many others with different rules, competitions, and famous athletes."
            ),
            "health": (
                "Health is an important topic, but I'm having trouble accessing my knowledge services right now. "
                "For health-related questions, it's always best to consult with qualified healthcare professionals "
                "for personalized advice."
            ),
            "technology": (
                "Technology is evolving rapidly across areas like AI, software development, hardware, and digital "
                "services. While I'm having trouble connecting to my knowledge services right now, I'd be happy "
                "to try answering a more specific question about technology."
            ),
            "history": (
                "Historical topics span thousands of years of human civilization, covering people, events, and "
                "societal developments. I'm having trouble accessing detailed historical information right now, "
                "but I'd be happy to try again in a moment."
            ),
            "science": (
                "Science encompasses fields like physics, chemistry, biology, astronomy, and more. I'm having "
                "trouble connecting to my knowledge services right now, but I'd be happy to try a more specific "
                "scientific question shortly."
            ),
            "code": (
                "Programming involves creating instructions for computers using languages like Python, JavaScript, "
                "Java, and many others. I'm having trouble accessing my coding knowledge right now, but I'd be "
                "happy to help with a specific coding problem in a moment."
            ),
            "music": (
                "Music spans countless genres, artists, and traditions from around the world. I'm having trouble "
                "accessing my detailed music knowledge right now, but I'd be happy to try again with a more "
                "specific question shortly."
            ),
            "movie": (
                "Films and cinema encompass a vast variety of genres, directors, actors, and storytelling techniques. "
                "I'm having trouble connecting to my knowledge services right now, but I'd be happy to discuss "
                "movies again in a moment."
            ),
            "game": (
                "Games include video games, board games, card games, and many other forms of interactive entertainment. "
                "I'm having trouble accessing my gaming knowledge right now, but I'd be happy to try again shortly."
            )
        }


@lru_cache()
def get_cohere_client() -> CohereClient:
    """
    Get a cached Cohere client
    """
    return CohereClient(api_key=settings.COHERE_API_KEY)