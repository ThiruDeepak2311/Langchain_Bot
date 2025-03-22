from datetime import datetime, timedelta
from typing import Optional, Union, Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from config import settings
from models.user import User, UserInDB, TokenData

# Fake users database for demo
# In a real app, this would be a database query
fake_users_db = {
    "johndoe@example.com": {
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password
        "full_name": "John Doe",
        "disabled": False,
    }
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password for storing
    """
    return pwd_context.hash(password)

def get_user(email: str) -> Optional[UserInDB]:
    """
    Get a user by email
    """
    if email in fake_users_db:
        user_dict = fake_users_db[email]
        return UserInDB(**user_dict)
    return None

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a new access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
        
        token_data = TokenData(email=email)
    except (JWTError, ValidationError):
        raise credentials_exception
    
    user = get_user(email=token_data.email)
    
    if user is None:
        raise credentials_exception
    
    return User(**user.dict())

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user