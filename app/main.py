from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete, update

from database import init_db, get_db
from logger import setup_logger
from schemas import MovieStatus, MovieCreate
from models import Movie
from datetime import datetime



@asynccontextmanager
async def lifespan(app: FastAPI):
    
    await init_db()
    app_logger.info(f"{section} | Application started")
    yield
    app_logger.info(f"{section} | Application shutting down")


app = FastAPI(title="Movie Watchlist", lifespan=lifespan)
section = "APP"
app_logger = setup_logger()



@app.get('/movies/')
async def show_all_movies(db: AsyncSession = Depends(get_db)):
    
    stmt = select(Movie)
    result = await db.execute(stmt)
    movies = result.scalars().all()

    return movies


@app.post("/movies/")
async def add_movie(append_movie: MovieCreate, db: AsyncSession = Depends(get_db)):
    
    data = append_movie.model_dump()
    if isinstance(data.get('year'), datetime):
        data['year'] = data['year'].year
    

    stmt = insert(Movie).values(**data)
    await db.execute(stmt)
    await db.commit()
    app_logger.info(f"{section} | {append_movie.title} has appended to database")

    return data
