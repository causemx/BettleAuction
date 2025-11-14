from sqlalchemy.orm import Session
from models import Auction
from schemas import AuctionCreate, AuctionUpdate

def get_all(db: Session, skip:int=0, limit:int=10):
    return db.query(Auction).offset(skip).limit(limit).all()

def get_by_id(db: Session, auction_id:int):
    return db.query(Auction).filter(Auction.id == auction_id).first()

def create(db: Session, auction:AuctionCreate) -> Auction:
    db_post = Auction(**auction.model_dump())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def update(db:Session, auction_id:int, auction_update:AuctionUpdate):
    db_post = db.query(Auction).filter(Auction.id == auction_id).first()
    if db_post:
        update_data = auction_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_post, field, value)
        db.commit()
        db.refresh(db_post)
    return db_post

def delete(db: Session, auction_id:int):
    db_post = db.query(Auction).filter(Auction.id == auction_id).first()
    if db_post:
        db.delete(db_post)
        db.commit()
    return db_post