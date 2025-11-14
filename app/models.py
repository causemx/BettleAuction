from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from database import Base

class Auction(Base):
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=True)
    content = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)
    create_at = Column(DateTime, default=datetime.utcnow)
    update_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
