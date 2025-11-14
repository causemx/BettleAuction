from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import AuctionCreate, AuctionUpdate, AuctionResponse
import crud


router = APIRouter(prefix="/posts", tags=["posts"])

@router.get("", response_model=List[AuctionResponse])
def get_all_posts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Get all blog posts with pagination"""
    posts = crud.get_all(db, skip, limit)
    return posts

@router.post("", response_model=AuctionResponse)
def create_auction(auction: AuctionCreate, db: Session = Depends(get_db)):
    return crud.create(db, auction)

@router.get("/{auction_id}", response_model=AuctionResponse)
def get_auction(auction_id: int, db: Session=Depends(get_db)):
    return crud.get_by_id(db, auction_id)

@router.put("/{auction_id}", response_model=AuctionResponse)
def update_auction(auction_id: int, auction: AuctionUpdate, db: Session=Depends(get_db)):
    return crud.update(db, auction_id)

@router.delete("/{auction_id}", response_model=AuctionResponse)
def delete_auction(auction_id: int, db: Session=Depends(get_db)):
    return crud.delete(db, auction_id)