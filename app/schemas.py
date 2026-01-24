from pydantic import BaseModel
from typing import Optional, Text
from datetime import datetime
from enum import Enum



class MovieStatus(str, Enum):
    want_to_watch = 'want_to_watch'
    watching = 'watching'
    watched = 'watched'


class MovieCreate(BaseModel):

    title: str
    year: int
    genre: str
    status: MovieStatus


class MovieUpdate(BaseModel):

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

class MovieResponse(BaseModel):

    model_config = {
        "from_attributes": True, 
        "use_enum_values": True 
    }

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