# region Імпорти
from pydantic import BaseModel
from typing import Text
from datetime import datetime
# endregion

# region Мої Імпорти
from .models import MovieStatus
# endregion 


class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    created_at: datetime
    is_active: bool


class MovieCreate(BaseModel):
    # Не забуваєм про типізацію
    title: str
    year: int
    genre: str
    status: MovieStatus
    # TMDB fields (optional)
    tmdb_id: int | None = None
    original_title: str | None = None
    poster_url: str | None = None
    overview: Text | None = None


class MovieUpdate(BaseModel):
    # Типізуєм і додаєм "| None = None" щоб параметр міг бути NULL в БД
    tmdb_id: int | None = None
    title: str | None = None
    original_title: str | None = None
    year: int | None = None
    genre: str | None = None
    poster_url: str | None = None
    overview: Text | None = None
    runtime: int | None = None
    status: MovieStatus | None = None
    user_rating: float | None = None
    notes: Text | None = None
    updated_date: datetime | None = None


# Схема відповіді для фільмів
class MovieResponse(BaseModel):
    id: int
    tmdb_id: int | None = None
    title: str
    original_title: str | None = None
    year: int
    genre: str
    poster_url: str | None = None
    overview: Text | None = None
    runtime: int | None = None
    status: MovieStatus
    user_rating: float | None = None
    notes: Text | None = None
    added_date: datetime | None = None
    updated_date: datetime | None = None

    model_config = {
        # Дозволяє конвертувати SQLAlchemy obj у Pydantic
        "from_attributes": True,  
        # Конвертує Enum в строкове значення JSON
        "use_enum_values": True
    }
