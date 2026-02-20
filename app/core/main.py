# region Модулі для БД / Веба
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete, update, func, extract
from app.auth.registration import router as auth_router
from app.auth.login import router as login_router
from app.auth.security import get_current_user
from app.database.models import User
from app.core.redis_client import get_redis, close_redis
from app.services.tmdb import TMDBService
# endregion

# region Python / Mine модулі
import asyncio
from collections import Counter
from app.core.mytools import is_none_filter
from app.database.database import init_db, get_db
from app.core.logger import setup_logger
from app.database.schemas import MovieResponse, MovieCreate, MovieUpdate, StatsResponse, MonthlyHistory, GenreCount
from app.database.models import Movie, MovieStatus
from datetime import datetime
# endregion

"""
СПІЛКУВАННЯ з БД оформленно в підході SQLAlchemy Core 
    Бо працює з асинхронністю та є швидшим способом
"""

# Глобальна змінна для TMDB сервісу (ініціалізується в lifespan)
tmdb_service = None

# Життєвий цикл для керування ресурсами (Асинхронність)
@asynccontextmanager
async def lifespan(app: FastAPI):
    
    await init_db()
    app_logger.info(f"{section} | Application started")
    redis = await get_redis()
    app_logger.info("Redis connected")
    
    # Ініціалізувати TMDB сервіс з Redis клієнтом
    from app.services.tmdb import TMDBService
    global tmdb_service
    tmdb_service = TMDBService(redis_client=redis)
    app_logger.info("TMDB service initialized")

    yield

    await close_redis()
    app_logger.info("Redis disconnected")
    app_logger.info(f"{section} | Application shutting down")


# Dependency injection для TMDB сервісу
def get_tmdb_service():
    """Повертає ініціалізований TMDB сервіс."""
    if tmdb_service is None:
        raise HTTPException(
            status_code=503, 
            detail="TMDB service is not initialized"
        )
    return tmdb_service


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
        current_user: User = Depends(get_current_user),
        tmdb: TMDBService = Depends(get_tmdb_service)
    ):
    """
    Пошук фільмів в TMDB за назвою.
    Повертає список знайдених фільмів з постерами та описом.
    """
    results = await tmdb.search_and_format(query, page)
    return results


@app.get('/movies/tmdb/{tmdb_id}')
async def get_tmdb_movie_details(
        tmdb_id: int,
        current_user: User = Depends(get_current_user),
        tmdb: TMDBService = Depends(get_tmdb_service)
    ):
    """
    Отримати детальну інформацію про фільм з TMDB.
    Повертає повні дані: жанри, акторів, режисера, тривалість і т.д.
    """
    details = await tmdb.get_details_formatted(tmdb_id)
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


# Точка GET для СТАТИСТИКИ — має бути ДО /movies/{movie_id} !
@app.get("/movies/stats/", response_model=StatsResponse)
async def user_stats(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    
    stmt = select(Movie.status, func.count(Movie.id).label("count")
    ).where(Movie.user_id == current_user.id).group_by(Movie.status)
    response = await db.execute(stmt)
    status_rows = response.all()
    by_status = {row._mapping["status"].value: int(row._mapping["count"]) for row in status_rows}

    genre_stmt = select(Movie.genre).where(Movie.user_id == current_user.id)
    genre_result = await db.execute(genre_stmt)
    genres_raw = genre_result.scalars().all()
    counter = Counter()
    for genre_str in genres_raw:
        for genre in genre_str.split(","):
            counter[genre.strip()] += 1
    top_genres = [GenreCount(name=g, count=c) for g, c in counter.most_common(5)]

    monthly_stmt = (
        select(
            extract('year', Movie.watch_date).label("year"),
            extract('month', Movie.watch_date).label("month"),
            func.count(Movie.id).label("count")
        )
        .where(
            Movie.user_id == current_user.id,
            Movie.status == MovieStatus.watched,
            Movie.watch_date.isnot(None)
        )
        .group_by(
            extract('year', Movie.watch_date),
            extract('month', Movie.watch_date)
        )
        .order_by(
            extract('year', Movie.watch_date),
            extract('month', Movie.watch_date)
        )
    )
    monthly_result = await db.execute(monthly_stmt)
    monthly_rows = monthly_result.all()
    monthly_history = [
        MonthlyHistory(year=int(r._mapping["year"]), month=int(r._mapping["month"]), count=int(r._mapping["count"]))
        for r in monthly_rows
    ]

    return StatsResponse(
        by_status=by_status,
        top_genres=top_genres,
        monthly_history=monthly_history
    )


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

    # Автоматично ставимо дату перегляду якщо статус watched
    if data.get('status') == MovieStatus.watched and not data.get('watch_date'):
        data['watch_date'] = datetime.now()

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
        data['updated_date'] = datetime.now()

    # Автоматично ставимо дату перегляду якщо статус змінено на watched
    if data.get('status') == MovieStatus.watched and not data.get('watch_date'):
        data['watch_date'] = datetime.now()
    
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
@app.delete("/movies/{movie_id}", response_model=MovieResponse)
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
