from typing import List, Optional
from sqlalchemy.orm import Session
from auth import hash_password, verify_password
from schemas import Auction, Role, UserModel, Bid
from models import AuctionCreate, AuctionUpdate

def get_all_auctions(db: Session, skip: int = 0, limit: int = 10) -> List[Auction]:
    """Get all auctions with pagination"""
    return db.query(Auction).offset(skip).limit(limit).all()


def get_auction_by_id(db: Session, auction_id: int) -> Optional[Auction]:
    """Get auction by ID"""
    return db.query(Auction).filter(Auction.id == auction_id).first()


def create_auction(db: Session, auction: AuctionCreate) -> Auction:
    """Create a new auction"""
    auction_data = auction.model_dump()
    if auction_data.get("current_price") is None:
        auction_data['current_price'] = auction_data['start_price']
    if auction_data.get('is_active') is None:
        auction_data['is_active'] = True
    db_auction = Auction(**auction_data)
    db.add(db_auction)
    db.commit()
    db.refresh(db_auction)
    return db_auction


def update_auction(db: Session, auction_id: int, auction_update: AuctionUpdate) -> Optional[Auction]:
    """Update an auction"""
    db_auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if db_auction:
        update_data = auction_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_auction, field, value)
        db.commit()
        db.refresh(db_auction)
    return db_auction


def delete_auction(db: Session, auction_id: int) -> Optional[Auction]:
    """Delete an auction"""
    db_auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if db_auction:
        db.delete(db_auction)
        db.commit()
    return db_auction


# ============================================================================
# BID CRUD OPERATIONS
# ============================================================================

def create_bid(db: Session, auction_id: int, bidder_id: int, amount: float) -> Optional['Bid']:
    from datetime import datetime
    
    auction = get_auction_by_id(db, auction_id)
    if not auction:
        return None
    db_bid = Bid(
        auction_id=auction_id, 
        bidder_id=bidder_id, 
        amount=amount, 
        bid_time=datetime.utcnow()
    )
    db.add(db_bid)
    db.commit()
    db.refresh(db_bid)
    
    auction.current_price = amount
    auction.winner_id = bidder_id
    db.commit()
    db.refresh(auction)
    
    return db_bid

def get_auction_bids(db: Session, auction_id: int) -> List['Bid']:
    return db.query(Bid).filter(Bid.auction_id == auction_id).order_by(Bid.bid_time.desc()).all()


def get_highest_bid(db: Session, auction_id: int) -> Optional['Bid']:
    """Get the highest bid for an auction"""
    return db.query(Bid).filter(Bid.auction_id == auction_id).order_by(Bid.amount.desc()).first()


# ============================================================================
# USER CRUD OPERATIONS
# ============================================================================

def get_user_by_name(db: Session, username: str)-> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.id == user_id).first()

def get_user_by_name_and_email(db: Session, username: str, email: str) -> Optional[UserModel]:
    return db.query(UserModel).filter(
        (UserModel.username == username) | (UserModel.email == email)
    ).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[UserModel]:
    return db.query(UserModel).offset(skip).limit(limit).all()

def create_user(db: Session, username: str, email: str, password: str) -> UserModel:
    exist_user = get_user_by_name_and_email(db, username, email)
    if exist_user:
        if exist_user.username == username:
            raise ValueError("Username already taken")
        else:
            raise ValueError("Email already registered")
    
    db_user = UserModel(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role=Role.USER
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def get_user_role(db: Session, user_id: int) -> Optional[Role]:
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    return user.role

def update_user_role(db: Session, user_id: int, new_role: str) -> Optional[UserModel]:
    if new_role not in ["user", "admin"]:
        raise ValueError("Role must be 'user' or 'admin'")
    
    user = get_user_by_id(db, user_id=user_id)
    
    if not user:
        return None
    
    user.role = Role[new_role.upper()]
    db.commit()
    db.refresh(user)
    
    return user

def authenticate_user(db: Session, username: str, password: str) ->Optional[UserModel]:
    user = get_user_by_name(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def delete_user(db: Session, user_id: int) -> Optional[UserModel]:
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        return None
    db.delete(user)
    db.commit()
    return user