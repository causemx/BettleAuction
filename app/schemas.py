from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from models import Role

class AuctionCreate(BaseModel):
    title: str
    content: str
    author: str

class AuctionUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    
class AuctionResponse(BaseModel):
    title: str
    content: str
    author: str
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
   
    class config:
        from_attributes = True
        
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
    

