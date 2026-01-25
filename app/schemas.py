# region Імпорти
from pydantic import BaseModel
from typing import Optional, Text
from datetime import datetime
from enum import Enum
# endregion


class MovieStatus(str, Enum):
    want_to_watch = 'want_to_watch'
    watching = 'watching'
    watched = 'watched'


# Схема при створенні фільму
class MovieCreate(BaseModel):
    # Не забуваєм про типізацію
    title: str
    year: int
    genre: str
    status: MovieStatus


# Модель при обновленні фільму
class MovieUpdate(BaseModel):
    # Option - не обов'язоковий аргумент у відповіді + типізуєм
    tmdb_id: Optional[int]
    title: Optional[str] 
    original_title: Optional[str]
    year: Optional[int] 
    genre: Optional[str] 
    poster_url: Optional[str] 
    overview: Optional[Text] 
    runtime: Optional[int] 
    status: Optional[Enum] 
    user_rating: Optional[float] 
    notes: Optional[Text]
    watch_date: Optional[datetime]
    added_date: Optional[datetime] 
    updated_date: Optional[datetime] 


# Схема відповіді (Загальна)
class MovieResponse(BaseModel):
    # Типізуєм і додаєм "| None = None" щоб параметр міг бути NULL в БД
    tmdb_id: int | None = None
    title: str
    original_title: str | None = None
    year: int
    genre: str
    poster_url: str | None = None
    overview: Text | None = None
    runtime: int | None = None
    status: Enum
    user_rating: float | None = None
    notes: Text | None = None
    watch_date: datetime | None = None
    added_date: datetime | None = None
    updated_date: datetime | None = None

    model_config = {
        # Дозволяє конвертувати SQLAlchemy obj у Pydantic
        "from_attributes": True,  
        # Конвертує Enum в строкове значення JSON
        "use_enum_values": True 
    }