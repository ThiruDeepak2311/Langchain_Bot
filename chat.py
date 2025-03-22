from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    """
    A chat message model
    """
    id: Optional[str] = None
    role: str
    content: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

class ChatResponse(BaseModel):
    """
    A response from the chatbot
    """
    message: str
    success: bool = True
    metadata: Optional[Dict[str, Any]] = None

class ChatHistory(BaseModel):
    """
    A collection of chat messages
    """
    messages: List[Dict[str, Any]] = []