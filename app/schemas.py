import enum
from sqlalchemy import (
    Column,
    Boolean,
    Float, 
    Integer, 
    String, 
    Text, 
    DateTime, 
    Enum
    )
from datetime import datetime
from database import Base


class Role(str, enum.Enum):
    USER = 'user'
    ADMIN = 'admin'
    
class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(Role), default=Role.USER)
    create_at = Column(DateTime, default=datetime.utcnow)
    update_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Auction(Base):
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True, index=True)
    winner_id = Column(Integer, nullable=True)
    title = Column(String(255), index=True, nullable=True)
    content = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)
    start_price = Column(Float)
    current_price = Column(Float)
    is_active = Column(Boolean)
    image_path = Column(String(500), nullable=True)
    image_paths = Column(Text, nullable=True)
    ends_at = Column(DateTime)
    create_at = Column(DateTime, default=datetime.utcnow)
    update_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Bid(Base):
    __tablename__ = "bids"
    
    id = Column(Integer, index=True, primary_key=True)
    auction_id = Column(Integer, index=True)
    bidder_id = Column(Integer)
    amount = Column(Float)
    bid_time = Column(DateTime)
    