from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any

class Token(BaseModel):
    """
    OAuth2 compatible token schema
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Token data schema
    """
    email: Optional[str] = None

class User(BaseModel):
    """
    User schema
    """
    email: EmailStr
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserCreate(BaseModel):
    """
    User creation schema
    """
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserInDB(User):
    """
    User in database schema
    """
    hashed_password: str