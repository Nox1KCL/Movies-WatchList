from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, or_

from app.database.schemas import UserCreate, UserResponse
from app.database.models import User
from app.database.database import get_db
from app.auth.security import hash_password

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, 
                    db: AsyncSession = Depends(get_db)):

    stmt = select(User).where(
        or_(
            User.email == user_data.email, 
            User.username == user_data.username
        )
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user:
        if user.email == user_data.email:
            raise HTTPException(status_code=400, detail="Email already registered")
        else:
            raise HTTPException(status_code=400, detail="Username already taken")


    hashed_password = await hash_password(user_data.password)
    stmt = insert(User).values(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password
        ).returning(User)

    result = await db.execute(stmt)
    await db.commit()

    new_user = result.scalar_one()
    return new_user