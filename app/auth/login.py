from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models import User
from app.database.database import get_db
from app.auth.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
    ):

    stmt = select(User).where(User.email == form_data.username)
    result = await db.execute(stmt)
    
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, 
        detail="User doesn\'t exist")
    
    is_password_correct = await verify_password(form_data.password, user.hashed_password)

    if not is_password_correct:
        raise HTTPException(status_code=401, 
        detail="Incorrect password")

    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}