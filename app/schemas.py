from pydantic import BaseModel
from typing import Optional, Text
from datetime import datetime
from enum import Enum



class MovieStatus(str, Enum):
    WANT_TO_WATCH = 'want_to_watch'
    WATCHING = 'watching'
    WATCHED = 'watched'


class MovieCreate(BaseModel):

    title: str
    year: int
    genre: str


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

    tmdb_id: int
    title: str
    original_title: str
    year: int
    genre: str
    poster_url: str 
    overview: Text 
    runtime: int 
    status: Enum
    user_rating: float 
    notes: Text
    watch_date: datetime
    added_date: datetime 
    updated_date: datetime 