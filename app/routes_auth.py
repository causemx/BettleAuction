from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import UserModel, Role
from schemas import (
    UserResponse, 
    UserCreate, 
    UserLogin,
    Token, 
    TokenData
)
from auth import (
    hash_password,
    authenticate_user,
    create_access_token,
    require_role,
)


router_auth = APIRouter(prefix="/auth", tags=["auth"])

@router_auth.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    exist_user = db.query(UserModel).filter(
        (UserModel.username == user.username) | (UserModel.email == user.email)
    ).first()
    if exist_user: 
        raise HTTPException(
           status_code=status.HTTP_400_BAD_REQUEST,
           detail="User has register" 
        )
    db_user = UserModel(
        username = user.username, 
        email = user.email,
        hashed_password = hash_password(user.password),
        role = Role.USER
        )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router_auth.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    "Login and get JWT token"
    db_user = authenticate_user(user.username, user.password, db)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={
            "sub": db_user.username,
            "role": db_user.role.value,
            "user_id": db_user.id
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(db_user)
    } 

@router_auth.get("/users", response_model=UserResponse)
def list_all_users(token_data: TokenData=Depends(require_role("admin")), db: Session=Depends(get_db)):
    users = db.query(UserModel).all()
    return users

@router_auth.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int, 
    new_role: str, 
    token_data: TokenData=Depends(require_role("admin")), 
    db: Session=Depends(get_db)):
    if new_role not in ["user", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be user or admin"
        )
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    user.role = Role[new_role.upper()]
    db.commit()
    db.refresh(user)
    return user

@router_auth.delete("/users/{user_id}")
def delete_user(
    user_id: int, 
    token_data: TokenData=Depends(require_role("admin")), 
    db: Session=Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    return user