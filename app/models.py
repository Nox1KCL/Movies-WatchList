from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import DateTime, Integer, String, Text, Enum, Float
from sqlalchemy.orm import Mapped, mapped_column

import enum
from datetime import datetime
from tzlocal import get_localzone_name
import pytz

local_tz = get_localzone_name()
tz = pytz.timezone(local_tz)

class MovieStatus(enum.Enum):
    WANT_TO_WATCH = 'want_to_watch'
    WATCHING = 'watching'
    WATCHED = 'watched'


class Base(DeclarativeBase): pass
class Movie(Base):

    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    tmdb_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_title: Mapped[str | None] = mapped_column(String)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    genre: Mapped[str] = mapped_column(String(200), nullable=False)
    poster_url: Mapped[str | None] = mapped_column(String(500))
    overview: Mapped[Text | None] = mapped_column(Text)
    runtime: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[Enum | None] = mapped_column(Enum(MovieStatus))
    user_rating: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[Text | None] = mapped_column(Text)
    watch_date: Mapped[DateTime | None] = mapped_column(DateTime)
    added_date: Mapped[DateTime | None] = mapped_column(DateTime, default=datetime.now)
    updated_date: Mapped[DateTime | None] = mapped_column(DateTime, onupdate=datetime.now)
    

     