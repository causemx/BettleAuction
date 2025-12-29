import os
import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPBasicCredentials 
from sqlalchemy.orm import Session
from database import get_db
from schemas import UserModel
from models import TokenData
from dotenv import load_dotenv


load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta]=None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))
    return encoded_jwt
    
def verify_token(credentials: HTTPBasicCredentials = Depends(security)) -> TokenData:
    """Verify JWT token and extract user data"""
    try:
        payload = jwt.decode(credentials.credentials, os.getenv("SECRET_KEY"), algorithms=os.getenv("ALGORITHM"))
        username: str = payload.get("sub")
        role: str = payload.get("role")
        user_id: int = payload.get("user_id")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return TokenData(username=username, role=role, user_id=user_id)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def get_current_user(token_data: TokenData = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == token_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
            
        )
    return user

def require_role(required_role: str):
    async def check_role(token_data: TokenData = Depends(verify_token)):
        if token_data.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied, Required role: {required_role}"
            )
        return token_data
    return check_role

def authenticate_user(username: str, password: str, db: Session = Depends(get_db)) -> Optional[UserModel]:
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
