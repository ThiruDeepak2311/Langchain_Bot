from fastapi import HTTPException, status
from typing import Dict, Any, Optional

class ChatbotError(Exception):
    """
    Base exception for chatbot-related errors
    """
    def __init__(
        self, 
        message: str = "An error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        retry_allowed: bool = False
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.retry_allowed = retry_allowed
        super().__init__(self.message)

class LLMError(ChatbotError):
    """
    Exception for LLM-related errors
    """
    def __init__(
        self, 
        message: str = "An error occurred with the LLM service",
        details: Optional[Dict[str, Any]] = None,
        retry_allowed: bool = True
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
            retry_allowed=retry_allowed
        )

class KnowledgeRetrievalError(ChatbotError):
    """
    Exception for knowledge retrieval errors
    """
    def __init__(
        self, 
        message: str = "An error occurred retrieving knowledge",
        details: Optional[Dict[str, Any]] = None,
        retry_allowed: bool = True
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
            retry_allowed=retry_allowed
        )

class ConversationError(ChatbotError):
    """
    Exception for conversation-related errors
    """
    def __init__(
        self, 
        message: str = "An error occurred in the conversation",
        details: Optional[Dict[str, Any]] = None,
        retry_allowed: bool = False
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            retry_allowed=retry_allowed
        )

class RateLimitError(ChatbotError):
    """
    Exception for rate limiting
    """
    def __init__(
        self, 
        message: str = "Rate limit exceeded. Please try again later.",
        retry_after: int = 30,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after": retry_after, **(details or {})}
        )

class AuthenticationError(ChatbotError):
    """
    Exception for authentication errors
    """
    def __init__(
        self, 
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )