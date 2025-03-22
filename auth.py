from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    get_current_user,
    oauth2_scheme
)
from models.user import User, UserCreate, UserInDB, Token

# Dummy user database for demo purposes
# In a real application, you would use a proper database
fake_users_db = {
    "johndoe@example.com": {
        "email": "johndoe@example.com",
        "hashed_password": get_password_hash("password"),
        "full_name": "John Doe",
        "disabled": False,
    }
}

router = APIRouter()

@router.post("/register", response_model=User)
async def register_user(user: UserCreate = Body(...)):
    """
    Register a new user
    """
    if user.email in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    
    user_dict = user.dict()
    user_dict.pop("password")
    user_dict["hashed_password"] = hashed_password
    
    fake_users_db[user.email] = UserInDB(**user_dict)
    
    return User(**user_dict)

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    """
    return current_user

def authenticate_user(email: str, password: str):
    """
    Authenticate a user with email and password
    """
    if email not in fake_users_db:
        return False
    
    user = UserInDB(**fake_users_db[email])
    if not verify_password(password, user.hashed_password):
        return False
    
    return user