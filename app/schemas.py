from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional
from models import Role

class AuctionCreate(BaseModel):
    title: str
    content: str
    author: str
    image_path: Optional[str] = None
    image_paths: Optional[str] = None

class AuctionUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    image_path: Optional[str] = None
    image_paths: Optional[str] = None
    
class AuctionResponse(BaseModel):
    title: str
    content: str
    author: str
    image_path: Optional[str] = None
    image_paths: Optional[str] = None
    create_at: datetime
    update_at: datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    create_at: datetime
    
    # pydantic V2 formation
    model_config = {
        'from_attributes': True
    }

    @field_validator('role')
    @classmethod
    def serialize_role(cls, v):
        """Convert Role enum to string"""
        if isinstance(v, Role):
            return v.value  # Returns 'user' or 'admin'
        return v
    
        
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None 
    
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str