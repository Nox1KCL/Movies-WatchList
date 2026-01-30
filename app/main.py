# region Модулі для БД / Веба
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete, update
from .mytools import is_none_filter
# endregion

# region Python / Mine модулі
from .database import init_db, get_db
from .logger import setup_logger
from .schemas import MovieResponse, MovieCreate, MovieUpdate
from .models import Movie, MovieStatus
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app_logger = setup_logger()
section = "APP" # Для зрозумілості звідки логи

# Точка GET для отримання списку фільмів ПО ФІЛЬТРАМ
@app.get('/movies/', response_model=list[MovieResponse]) # (Pydantic) response_model відповідає за структуру відповіді ендпоїнта
async def show_all_movies(
        genre: str | None = None,
        year: int | None = None,
        status: MovieStatus | None = None,
        # (FastAPI) Dependency injection для використання БД
        db: AsyncSession = Depends(get_db) 
    ): 

    stmt = select(Movie) # Створюємо SELECT запит

    filters = {
        "genre": genre,
        "year": year,
        "status": status
    }

    conditions = await is_none_filter(**filters)
    if conditions:
        stmt = stmt.where(*conditions)
        
    result = await db.execute(stmt) # Виконуєм + забираєм результат
    movies = result.scalars().all() # Обробляєм результат

    return movies

# Точка GET для отримання фільму по АЙДІ
@app.get("/movies/{movie_id}", response_model=MovieResponse)
async def show_one_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Movie).where(Movie.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().one()

    return movie

# Точка POST для ДОДАВАННЯ нових фільмів
@app.post("/movies/", response_model=MovieResponse)
async def add_movie(append_movie: MovieCreate, db: AsyncSession = Depends(get_db)):
    
    data = append_movie.model_dump(exclude_unset=True)
    # При відповіді береться datetime.now(), беремо з нього тільки рік
    if isinstance(data.get('year'), datetime):
        data['year'] = data['year'].year

    if not data:
        raise HTTPException(status_code=404, detail="Something wrong with data")
    
    stmt = insert(Movie).values(**data).returning(Movie) # Створюємо команду INSERT і повертаємо об'єкт
    result = await db.execute(stmt) # Виконуємо
    await db.commit() # Відправляємо зміни на БД
    
    new_movie = result.scalar_one()
    app_logger.info(f"{section} | {new_movie.title} has appended to database")

    return new_movie

# Точка PATCH для ОНОВЛЕННЯ фільму через АЙДІ
@app.patch("/movies/{movie_id}", response_model=MovieResponse)
async def update_movie(movie_id: int, movie_changes: MovieUpdate, db: AsyncSession = Depends(get_db)):
    data = movie_changes.model_dump(exclude_unset=True)
    if isinstance(data.get('updated_date'), datetime): 
         data['updated_date'] = datetime.now() # Оновлюєм час апдейта
    
    # returning 
    stmt = update(Movie).where(Movie.id == movie_id).values(data).returning(Movie)
    result = await db.execute(stmt)
    await db.commit()
    updated_movie=result.scalar_one_or_none()
    
    return updated_movie

# Точка DELETE для ВИДАЛЕННЯ фільму по АЙДІ
@app.delete("/movies/{movie_id}")
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = delete(Movie).where(Movie.id == movie_id).returning(Movie)
    result = await db.execute(stmt)
    deleted_movie = result.scalar_one_or_none()
    await db.commit()
    
    return deleted_movie
