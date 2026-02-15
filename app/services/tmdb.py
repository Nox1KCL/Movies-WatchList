"""TMDB API Service

Сервіс для взаємодії з The Movie Database API.
"""

import redis.asyncio as redis
import os
import httpx
import json
from typing import Optional
from dotenv import load_dotenv

load_dotenv("app/.env")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

# Кеш для жанрів (завантажується один раз)



class TMDBService:
    """Клієнт для TMDB API."""
    
    def __init__(self, redis_client: redis.Redis | None = None):
        self.api_key = TMDB_API_KEY
        self.base_url = TMDB_BASE_URL
        self.genres_loaded = False
        self.redis_client = redis_client
        
    async def load_genres(self) -> None:
        """Завантажити список жанрів з TMDB."""
        if self.genres_loaded or not self.redis_client:
            return
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/genre/movie/list",
                params={
                    "api_key": self.api_key,
                    "language": "uk-UA"
                }
            )
            if response.status_code == 200:
                data = response.json()
                await self.redis_client.hset("tmdb:genres", mapping={ # type: ignore
                    str(g["id"]): g["name"] for g in data.get("genres", [])
                })
                self.genres_loaded = True
    


    
    async def get_genres_text(self, genre_ids: list[int]) -> str:
        """Перетворити список ID жанрів у текст."""
        if not self.redis_client or not genre_ids:
            return ""        
        
        genres = []
        for gid in genre_ids:
            genre_name = await self.redis_client.hget("tmdb:genres", str(gid))  # type: ignore
            if genre_name:
                genres.append(genre_name)

        return ", ".join(genres[:3]) if genres else ""
        

    async def search_movies(self, query: str, page: int = 1) -> dict:
        """Пошук фільмів за назвою."""
        await self.load_genres()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search/movie",
                params={
                    "api_key": self.api_key,
                    "query": query,
                    "page": page,
                    "language": "uk-UA",
                    "include_adult": False
                }
            )
            response.raise_for_status()
            return response.json()
    

    async def get_movie_details(self, tmdb_id: int) -> dict:
        """Отримати детальну інформацію про фільм."""
        await self.load_genres()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/movie/{tmdb_id}",
                params={
                    "api_key": self.api_key,
                    "language": "uk-UA",
                    "append_to_response": "credits"  # Додаємо інфо про акторів/режисерів
                }
            )
            response.raise_for_status()
            return response.json()
    

    async def format_movie_result(self, movie: dict) -> dict:
        """Форматування результату пошуку для фронтенду."""
        genre_ids = movie.get("genre_ids", [])
        
        return {
            "tmdb_id": movie.get("id"),
            "title": movie.get("title"),
            "original_title": movie.get("original_title"),
            "year": int(movie.get("release_date", "0000")[:4]) if movie.get("release_date") else None,
            "overview": movie.get("overview"),
            "poster_url": f"{TMDB_IMAGE_BASE}{movie.get('poster_path')}" if movie.get("poster_path") else None,
            "backdrop_url": f"{TMDB_IMAGE_BASE}{movie.get('backdrop_path')}" if movie.get("backdrop_path") else None,
            "vote_average": movie.get("vote_average"),
            "vote_count": movie.get("vote_count"),
            "genre": await self.get_genres_text(genre_ids),
            "genre_ids": genre_ids,
        }
    

    def format_movie_details(self, movie: dict) -> dict:
        """Форматування детальної інформації про фільм."""
        # Отримуємо жанри напряму (в деталях вони як об'єкти)
        genres = [g.get("name") for g in movie.get("genres", [])]
        
        # Отримуємо режисера та акторів
        credits = movie.get("credits", {})
        directors = [c.get("name") for c in credits.get("crew", []) if c.get("job") == "Director"]
        cast = [c.get("name") for c in credits.get("cast", [])[:5]]  # Топ-5 акторів
        
        return {
            "tmdb_id": movie.get("id"),
            "title": movie.get("title"),
            "original_title": movie.get("original_title"),
            "year": int(movie.get("release_date", "0000")[:4]) if movie.get("release_date") else None,
            "overview": movie.get("overview"),
            "poster_url": f"{TMDB_IMAGE_BASE}{movie.get('poster_path')}" if movie.get("poster_path") else None,
            "backdrop_url": f"{TMDB_IMAGE_BASE}{movie.get('backdrop_path')}" if movie.get("backdrop_path") else None,
            "vote_average": movie.get("vote_average"),
            "vote_count": movie.get("vote_count"),
            "runtime": movie.get("runtime"),  # Тривалість в хвилинах
            "genre": ", ".join(genres[:3]),
            "genres": genres,
            "directors": directors,
            "cast": cast,
            "tagline": movie.get("tagline"),
            "budget": movie.get("budget"),
            "revenue": movie.get("revenue"),
            "status": movie.get("status"),
        }
    

    async def search_and_format(self, query: str, page: int = 1) -> list[dict]:
        """Пошук та форматування результатів."""
        cache_key = f"tmdb:search:{query}:{page}"
        
        # Спроба отримати з кешу
        json_data = await self.redis_client.get(cache_key) # type: ignore
        
        data = None
        if json_data:
            data = json.loads(json_data)
        
        # Якщо в кеші немає - запит до API
        if not data:
            data = await self.search_movies(query, page)
            # Зберігаємо в кеш на 1 годину (3600 сек)
            await self.redis_client.setex( # type: ignore
                cache_key, 
                3600, 
                json.dumps(data)
            )

        # Форматування результату (спільне для кешу та API)
        results = []
        for movie in data.get("results", []):
            formatted = await self.format_movie_result(movie)
            results.append(formatted)
            
        return results
    

    async def get_details_formatted(self, tmdb_id: int) -> dict:
        """Отримати відформатовані деталі фільму."""
        data = await self.get_movie_details(tmdb_id)
        return self.format_movie_details(data)


# Singleton instance - буде ініціалізовано при старті застосунку
tmdb_service: TMDBService
