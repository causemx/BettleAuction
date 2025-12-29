from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional
from schemas import Role


# ============================================================================
# Bid Related
# ============================================================================
class BidCreate(BaseModel):
    bidder_id: int
    amount: float

class BidResponse(BaseModel):
    id: int
    auction_id: int
    bidder_id: int
    amount: float
    bid_time: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Auction Related
# ============================================================================

class AuctionCreate(BaseModel):
    title: str
    content: str
    author: str
    start_price: float
    ends_at: datetime
    image_path: Optional[str] = None
    image_paths: Optional[str] = None
    current_price: Optional[float] = None
    is_active: Optional[bool] = True
    winner_id: Optional[int] = None

class AuctionUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    start_price: Optional[float] = None
    ends_at: Optional[float] = None
    image_path: Optional[str] = None
    image_paths: Optional[str] = None
    
class AuctionResponse(BaseModel):
    title: str
    content: str
    author: str
    start_price: float
    current_price: float
    is_active: bool
    winner_id: Optional[int]
    image_path: Optional[str] = None
    image_paths: Optional[str] = None
    ends_at: datetime
    create_at: datetime
    update_at: datetime
    
    class config:
        from_attributes = True

# ============================================================================
# Authenticate Related
# ============================================================================

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