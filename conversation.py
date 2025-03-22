import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
import json
from datetime import datetime, timedelta
import time
import traceback
from functools import lru_cache

# Imports for LLM services
from services.llm import get_cohere_client
from services.knowledge import get_wikipedia_service, get_knowledge_base
from core.errors import ConversationError, LLMError, KnowledgeRetrievalError

logger = logging.getLogger(__name__)

# Advanced cache with TTL
class TTLCache:
    def __init__(self, ttl_seconds=3600):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, key):
        if key in self.cache:
            entry = self.cache[key]
            if time.time() < entry["expires"]:
                return entry["value"]
            else:
                # Expired entry
                del self.cache[key]
        return None
    
    def set(self, key, value, ttl=None):
        ttl = ttl or self.ttl
        self.cache[key] = {
            "value": value,
            "expires": time.time() + ttl
        }
    
    def clear(self):
        self.cache = {}

class ChatManager:
    """
    Enhanced chat manager with parallel processing and improved knowledge retrieval
    """
    def __init__(self):
        self.cohere_client = get_cohere_client()
        self.wikipedia_service = get_wikipedia_service()
        self.knowledge_base = get_knowledge_base()
        self.history = []
        self._query_cache = TTLCache(3600)  # 1 hour cache TTL
        self._search_semaphore = asyncio.Semaphore(5)  # Limit concurrent searches
        
    async def process_message(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> str:
        """
        Process a user message and return a response
        """
        try:
            logger.info(f"Processing message: {message}")
            start_time = time.time()
            
            # Clean and normalize message for better caching
            normalized_message = self._normalize_message(message)
            
            # Check cache for identical questions
            cache_key = normalized_message
            cached_response = self._query_cache.get(cache_key)
            if cached_response:
                logger.info("Using cached response")
                # Still update history
                self.history.append({"role": "user", "content": message})
                self.history.append({"role": "assistant", "content": cached_response})
                return cached_response
            
            # Get chat history context (last 6 messages instead of 4)
            chat_history = []
            for msg in self.history[-6:]:  # Increased context window
                chat_history.append({
                    "role": msg.get("role", "USER"),
                    "content": msg.get("content", "")
                })
            
            # Step 1: Launch knowledge retrieval asynchronously to save time
            knowledge_task = asyncio.create_task(self._retrieve_knowledge(normalized_message))
            
            # Step 2: While knowledge is being retrieved, analyze the question type
            question_type = self._analyze_question_type(normalized_message)
            logger.info(f"Question type detected: {question_type}")
            
            # Step 3: Wait for knowledge retrieval to complete
            try:
                title, retrieved_info = await asyncio.wait_for(knowledge_task, timeout=10.0)
                knowledge_source = "wikipedia" if title else ""
            except asyncio.TimeoutError:
                logger.warning("Knowledge retrieval timed out, proceeding with generation")
                title, retrieved_info = "", ""
                knowledge_source = "timeout"
            
            # Step 4: Prepare enhanced prompt based on available information
            system_prompt = self._build_system_prompt(
                message, 
                title, 
                retrieved_info, 
                question_type,
                knowledge_source
            )
            
            # Step 5: Generate response using Cohere with improved error handling
            response_start = time.time()
            max_retries = 2
            current_retry = 0
            
            while current_retry <= max_retries:
                try:
                    # Set a generous but reasonable timeout
                    response = await asyncio.wait_for(
                        self.cohere_client.chat(
                            message=message,
                            chat_history=chat_history,
                            preamble=system_prompt,
                            temperature=0.6,  # Slightly lower temperature for more accurate responses
                            stream=stream,    # Support streaming if requested
                        ),
                        timeout=15.0
                    )
                    
                    response_duration = time.time() - response_start
                    logger.info(f"Response generation took {response_duration:.2f}s")
                    
                    # Break out of retry loop on success
                    break
                
                except (asyncio.TimeoutError, Exception) as e:
                    current_retry += 1
                    logger.error(f"Error generating response (attempt {current_retry}): {str(e)}")
                    
                    if current_retry <= max_retries:
                        # Exponential backoff
                        wait_time = 2 ** current_retry
                        logger.info(f"Retrying in {wait_time} seconds")
                        await asyncio.sleep(wait_time)
                    else:
                        # All retries failed, use fallback
                        logger.error(f"All retries failed: {str(e)}")
                        logger.error(traceback.format_exc())
                        
                        # Create fallback response
                        response = self._create_fallback_response(message, title, retrieved_info)
            
            # Step 6: Post-process the response for accuracy and consistency
            final_response = self._post_process_response(response, message, title)
            
            # Step 7: Update history and cache
            total_duration = time.time() - start_time
            logger.info(f"Total processing time: {total_duration:.2f}s")
            
            # Update history
            self.history.append({"role": "user", "content": message})
            self.history.append({"role": "assistant", "content": final_response})
            
            # Cache response with smart TTL - longer for factual questions, shorter for opinion/dynamic
            ttl = 86400 if question_type in ["factual", "knowledge"] else 3600
            self._query_cache.set(cache_key, final_response, ttl)
            
            return final_response
            
        except Exception as e:
            logger.error(f"Critical error processing message: {str(e)}")
            logger.error(traceback.format_exc())
            return "I'm sorry, but I encountered an unexpected error. Please try asking a different question."

    async def _retrieve_knowledge(self, message: str) -> Tuple[str, str]:
        """
        Enhanced knowledge retrieval that tries multiple sources in parallel
        """
        # Prevent too many concurrent searches to avoid overloading
        async with self._search_semaphore:
            try:
                # Create tasks for Wikipedia and knowledge base searches
                wiki_task = asyncio.create_task(self.wikipedia_service.get_knowledge(message))
                kb_task = asyncio.create_task(self.knowledge_base.search(message))
                
                # Wait for both to complete or 8 seconds to pass
                done, pending = await asyncio.wait(
                    [wiki_task, kb_task], 
                    timeout=8.0,
                    return_when=asyncio.ALL_COMPLETED
                )
                
                # Cancel any pending tasks to avoid resource leaks
                for task in pending:
                    task.cancel()
                
                # Process results from completed tasks
                wiki_title, wiki_info = "", ""
                kb_title, kb_info = "", ""
                
                for task in done:
                    try:
                        result = await task
                        if task == wiki_task:
                            wiki_title, wiki_info = result
                        elif task == kb_task:
                            kb_title, kb_info = result
                    except Exception as e:
                        logger.error(f"Error retrieving from knowledge source: {str(e)}")
                
                # Use the best information available (prefer knowledge base if available)
                if kb_info:
                    return kb_title, kb_info
                elif wiki_info:
                    return wiki_title, wiki_info
                else:
                    return "", ""
                
            except Exception as e:
                logger.error(f"Error in knowledge retrieval: {str(e)}")
                logger.error(traceback.format_exc())
                return "", ""

    def _normalize_message(self, message: str) -> str:
        """
        Normalize message for better caching by removing extra spaces,
        converting to lowercase, and removing punctuation
        """
        if not message:
            return ""
            
        import re
        # Remove extra spaces and lowercase
        normalized = " ".join(message.lower().split())
        # Remove punctuation except question marks (which can be semantically important)
        normalized = re.sub(r'[^\w\s\?]', '', normalized)
        return normalized

    def _analyze_question_type(self, message: str) -> str:
        """
        Analyze the type of question to better tailor the response
        """
        message = message.lower()
        
        # Define patterns for different question types
        factual_patterns = ['what is', 'who is', 'when did', 'where is', 'how many', 'define']
        opinion_patterns = ['what do you think', 'opinion', 'believe', 'feel about']
        procedural_patterns = ['how to', 'how do i', 'steps', 'process', 'procedure']
        comparison_patterns = ['difference between', 'compare', 'better', 'versus', 'vs']
        
        # Check for matches
        for pattern in factual_patterns:
            if pattern in message:
                return "factual"
                
        for pattern in opinion_patterns:
            if pattern in message:
                return "opinion"
                
        for pattern in procedural_patterns:
            if pattern in message:
                return "procedural"
                
        for pattern in comparison_patterns:
            if pattern in message:
                return "comparison"
                
        # Default to general knowledge
        return "knowledge"

    def _build_system_prompt(
        self, 
        message: str, 
        title: str, 
        retrieved_info: str, 
        question_type: str,
        knowledge_source: str
    ) -> str:
        """
        Build an enhanced system prompt based on question type and available information
        """
        base_prompt = "You are an intelligent and helpful AI assistant. "
        
        # Different instructions based on question type
        type_instructions = {
            "factual": "Provide accurate factual information. Be precise and cite sources when possible.",
            "opinion": "Provide a balanced perspective. Consider different viewpoints and explain your reasoning.",
            "procedural": "Provide clear step-by-step instructions. Be thorough but concise.",
            "comparison": "Compare the items carefully, highlighting similarities and differences. Consider multiple aspects.",
            "knowledge": "Provide comprehensive information on the topic. Cover key points and be educational."
        }
        
        # Add question-type specific instructions
        prompt = base_prompt + type_instructions.get(question_type, type_instructions["knowledge"]) + " "
        
        # Add retrieved information if available
        if retrieved_info:
            prompt += (
                f"\n\nRetrieved information about {title} from {knowledge_source}: {retrieved_info}\n\n"
                f"Use this information to help answer the question, but also draw on your general knowledge "
                f"to provide a complete response. If the information doesn't fully address the question, "
                f"be honest about what you know and don't know."
            )
        else:
            prompt += (
                "\n\nAnswer based on your general knowledge. If you don't know the specific answer, "
                "be honest about it and provide related information that might be helpful."
            )
            
        return prompt

    def _create_fallback_response(self, message: str, title: str, retrieved_info: str) -> str:
        """
        Create a fallback response when LLM generation fails
        """
        if retrieved_info:
            return f"Based on what I found about {title}: {retrieved_info}\n\nThis should help answer your question about {message.strip()}."
        
        # Check for common topics in the fallback knowledge
        normalized_message = message.lower()
        for key, info in self.knowledge_base.fallback_knowledge.items():
            if key in normalized_message:
                return info
                
        return (
            "I'm sorry, but I'm having trouble generating a complete response right now. "
            "Here's what I know about your question: " + 
            "The topic appears to be about " + (title or "something I don't have specific information on") + ". " +
            "Could you try rephrasing your question or asking about something else?"
        )

    def _post_process_response(self, response: str, message: str, title: str) -> str:
        """
        Post-process the response for better quality
        """
        if not response:
            return "I apologize, but I couldn't generate a response. Please try asking again."
            
        # Add source attribution if we used Wikipedia
        if title and "wikipedia" not in response.lower() and len(response) > 100:
            response += f"\n\nInformation about {title} was retrieved from Wikipedia and other knowledge sources."
            
        return response

    def get_history(self) -> List[Dict[str, str]]:
        """
        Get the conversation history
        """
        return self.history

    def clear_history(self) -> None:
        """
        Clear the conversation history
        """
        self.history = []
        # Don't clear the cache as it might be useful for other users