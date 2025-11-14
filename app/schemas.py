from pydantic import BaseModel
from datetime import datetime
from typing import Optional

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