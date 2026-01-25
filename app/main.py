# region Модулі для БД / Веба
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete, update
# endregion

# region Python / Mine модулі
from database import init_db, get_db
from logger import setup_logger
from schemas import MovieResponse, MovieCreate
from models import Movie
from datetime import datetime
# endregion

"""
СПІЛКУВАННЯ з БД оформленно в підході SQLAlchemy Core 
        Бо працює з асинхронністю, швидше 
"""

# Життєвий цикл для керування ресурсами (Асинхронність)
@asynccontextmanager
async def lifespan(app: FastAPI):
    
    await init_db()
    app_logger.info(f"{section} | Application started")
    yield
    app_logger.info(f"{section} | Application shutting down")


app = FastAPI(title="Movie Watchlist", lifespan=lifespan) # Створення екземляра FastAPI
app_logger = setup_logger()
section = "APP" # Для зрозумілості звідки логи

# Точка GET для отримання списку фільмів
@app.get('/movies/', response_model=list[MovieResponse]) # (Pydantic) response_model відповідає за структуру відповіді ендпоїнта
async def show_all_movies(db: AsyncSession = Depends(get_db)): # (FastAPI) Dependency injection для використання БД

    stmt = select(Movie) # Створюємо SELECT запит
    result = await db.execute(stmt) # Виконуєм + забираєм результат
    movies = result.scalars().all() # Обробляєм результат

    return movies

# Точка POST для додавання нових фільмів
@app.post("/movies/", response_model=MovieResponse)
async def add_movie(append_movie: MovieCreate, db: AsyncSession = Depends(get_db)):
    
    data = append_movie.model_dump()
    # При відповіді береться datetime.now(), беремо з нього тільки рік
    if isinstance(data.get('year'), datetime):
        data['year'] = data['year'].year
    
    stmt = insert(Movie).values(**data) # Створюємо команду INSERT
    await db.execute(stmt) # Виконуємо
    await db.commit() # Відправляємо зміни на БД
    app_logger.info(f"{section} | {append_movie.title} has appended to database")

    return data
