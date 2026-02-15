# region Модулі для БД / Веба
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete, update
from app.auth.registration import router as auth_router
from app.auth.login import router as login_router
from app.auth.security import get_current_user
from app.database.models import User
# endregion

# region Python / Mine модулі
from app.core.mytools import is_none_filter
from app.database.database import init_db, get_db
from app.core.logger import setup_logger
from app.database.schemas import MovieResponse, MovieCreate, MovieUpdate
from app.database.models import Movie, MovieStatus
from app.services.tmdb import tmdb_service
from datetime import datetime
# endregion

"""
СПІЛКУВАННЯ з БД оформленно в підході SQLAlchemy Core 
    Бо працює з асинхронністю та є швидшим способом
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

app.include_router(login_router) # login
app.include_router(auth_router) # Підключаємо роутер registration
app_logger = setup_logger()
section = "APP" # Для зрозумілості звідки логи


# ========== TMDB API ==========

@app.get('/movies/search')
async def search_tmdb_movies(
        query: str,
        page: int = 1,
        current_user: User = Depends(get_current_user)
    ):
    """
    Пошук фільмів в TMDB за назвою.
    Повертає список знайдених фільмів з постерами та описом.
    """
    results = await tmdb_service.search_and_format(query, page)
    return results


@app.get('/movies/tmdb/{tmdb_id}')
async def get_tmdb_movie_details(
        tmdb_id: int,
        current_user: User = Depends(get_current_user)
    ):
    """
    Отримати детальну інформацію про фільм з TMDB.
    Повертає повні дані: жанри, акторів, режисера, тривалість і т.д.
    """
    details = await tmdb_service.get_details_formatted(tmdb_id)
    return details

# Точка GET для отримання списку фільмів ПО ФІЛЬТРАМ
@app.get('/movies/', response_model=list[MovieResponse]) # (Pydantic) response_model відповідає за структуру відповіді ендпоїнта
async def show_all_movies(
        genre: str | None = None,
        year: int | None = None,
        status: MovieStatus | None = None,
        # (FastAPI) Dependency injection для використання БД
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ): 

    stmt = select(Movie).where(Movie.user_id == current_user.id) # Створюємо SELECT запит

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
async def show_one_movie(movie_id: int, 
            db: AsyncSession = Depends(get_db),
            current_user: User = Depends(get_current_user)
    ):
    stmt = select(Movie).where(Movie.user_id == current_user.id, 
                                Movie.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().one()

    return movie

# Точка POST для ДОДАВАННЯ нових фільмів
@app.post("/movies/", response_model=MovieResponse)
async def add_movie(append_movie: MovieCreate, 
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    
    data = append_movie.model_dump(exclude_unset=True)
    data['user_id'] = current_user.id

    if not data:
        raise HTTPException(status_code=404, 
        detail="Movie\'s data is incorrect")
    
    stmt = insert(Movie).values(**data).returning(Movie) # Створюємо команду INSERT і повертаємо об'єкт
    result = await db.execute(stmt) # Виконуємо
    await db.commit() # Відправляємо зміни на БД
    
    new_movie = result.scalar_one()
    app_logger.info(f"{section} | {new_movie.title} has appended to database")

    return new_movie

# Точка PATCH для ОНОВЛЕННЯ фільму через АЙДІ
@app.patch("/movies/{movie_id}", response_model=MovieResponse)
async def update_movie(movie_id: int, 
        movie_changes: MovieUpdate, 
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    data = movie_changes.model_dump(exclude_unset=True)
    if isinstance(data.get('updated_date'), datetime): 
         data['updated_date'] = datetime.now() # Оновлюєм час апдейта
    
    if not data:
        raise HTTPException(status_code=404, 
        detail="Movie is not exist")

    stmt = update(Movie).where(Movie.user_id == current_user.id, Movie.id == movie_id).values(data).returning(Movie)
    result = await db.execute(stmt)
    updated_movie=result.scalar_one_or_none()
    await db.commit()

    if not updated_movie:
        raise HTTPException(status_code=404,
        detail="Movie not found")
    
    return updated_movie

# Точка DELETE для ВИДАЛЕННЯ фільму по АЙДІ
@app.delete("/movies/{movie_id}")
async def delete_movie(movie_id: int, 
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    stmt = delete(Movie).where(Movie.user_id == current_user.id, Movie.id == movie_id).returning(Movie)
    result = await db.execute(stmt)
    deleted_movie = result.scalar_one_or_none()
    await db.commit()

    if not deleted_movie:
        raise HTTPException(status_code=404,
        detail="Movie not found")
    
    return deleted_movie
