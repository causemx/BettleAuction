from typing import List, Optional
from sqlalchemy.orm import Session
from auth import hash_password, verify_password
from models import Auction, Role, UserModel
from schemas import AuctionCreate, AuctionUpdate

def get_all_auctions(db: Session, skip: int = 0, limit: int = 10) -> List[Auction]:
    """Get all auctions with pagination"""
    return db.query(Auction).offset(skip).limit(limit).all()


def get_auction_by_id(db: Session, auction_id: int) -> Optional[Auction]:
    """Get auction by ID"""
    return db.query(Auction).filter(Auction.id == auction_id).first()


def create_auction(db: Session, auction: AuctionCreate) -> Auction:
    """Create a new auction"""
    db_auction = Auction(**auction.model_dump())
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