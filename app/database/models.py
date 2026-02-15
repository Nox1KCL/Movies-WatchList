# region Модулі для БД
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Boolean, DateTime, Integer, String, Text, Enum, Float
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
# endregion

# region інші Імпорти
import enum
from datetime import datetime
# endregion


# (SQLAlchemy) Для створення ORM об'єктів
class Base(DeclarativeBase): pass 


class User(Base):
    # Назва таблиці
    __tablename__ = "users"
    # Зв'язок One-to-Many з Movie
    movies: Mapped[list["Movie"]] = relationship(back_populates="owner", cascade="all, delete-orphan")

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class MovieStatus(str, enum.Enum):
    want_to_watch = 'want_to_watch'
    watching = 'watching'
    watched = 'watched'

# Таблиця для БД (Загальний вигляд)
class Movie(Base):
    
    __tablename__ = "movies"
    # Зв'язок One-to-Many з User
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    owner: Mapped["User"] = relationship(back_populates="movies")

    # Типізуєм, вказуєм "| None" для типів які можуть бути NULL в БД
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    tmdb_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_title: Mapped[str | None] = mapped_column(String(255))
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    genre: Mapped[str] = mapped_column(String(200), nullable=False)
    poster_url: Mapped[str | None] = mapped_column(String(500))
    overview: Mapped[Text | None] = mapped_column(Text)
    runtime: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[Enum] = mapped_column(Enum(MovieStatus), nullable=False)
    user_rating: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[Text | None] = mapped_column(Text)
    watch_date: Mapped[DateTime | None] = mapped_column(DateTime)
    added_date: Mapped[DateTime | None] = mapped_column(DateTime, default=datetime.now)
    updated_date: Mapped[DateTime | None] = mapped_column(DateTime, onupdate=datetime.now)
    


     