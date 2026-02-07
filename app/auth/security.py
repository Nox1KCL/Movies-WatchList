from bcrypt import gensalt, hashpw, checkpw
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.database.models import User

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def hash_password(password: str) -> str:
    byte_password = password.encode('utf-8')
    salt = gensalt()
    hashed_password = hashpw(byte_password, salt)
    return hashed_password.decode('utf-8')


async def verify_password(plain_password: str, hashed_password_from_db: str) -> bool:
    byte_password = plain_password.encode('utf-8')
    byte_hash = hashed_password_from_db.encode('utf-8')

    return checkpw(byte_password, byte_hash)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    
    # Додаємо час закінчення дії токена
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Створюємо токен
    if SECRET_KEY:
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return token
    else:
        raise HTTPException(status_code=400, 
        detail="Token unavaible")


def verify_token(token: str) -> dict | None:
    try:
        if SECRET_KEY:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
    except JWTError:
        return None  # Токен невалідний або протермінований


async def get_current_user(
        token: str = Depends(oauth2_scheme), 
        db: AsyncSession = Depends(get_db)
    ) -> User:
    
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, 
        detail="Invalid token")
    
    email: str | None = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, 
        detail="Invalid token")

    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=401, 
        detail="User not found") 
    
    return user