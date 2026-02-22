# 🍿 Movie Watchlist

Особистий список фільмів з пошуком через TMDB, статистикою та real-time оновленнями через WebSocket.

## Tech Stack

| Layer        | Tech                                                |
| ------------ | --------------------------------------------------- |
| Backend      | FastAPI · SQLAlchemy (async) · PostgreSQL · asyncpg |
| Cache        | Redis                                               |
| Auth         | JWT (python-jose · bcrypt)                          |
| Real-time    | WebSocket (uvicorn[standard])                       |
| Frontend     | Vue 3 (CDN) · Tailwind CSS                          |
| External API | TMDB API                                            |

## Features

- **Auth** — реєстрація / логін, JWT токени
- **CRUD** — додавання, редагування, видалення фільмів
- **Статуси** — `want_to_watch` / `watching` / `watched`
- **TMDB пошук** — пошук фільмів з постерами та описом через TMDB API
- **Кешування** — результати TMDB кешуються в Redis (TTL 1 год)
- **Статистика** — кількість фільмів за статусом, топ жанри, місячна історія переглядів
- **Real-time** — WebSocket нотифікації при змінах (toast + автооновлення списку)
- **Multi-tab** — синхронізація між вкладками одного акаунту

## Project Structure

```
Movie-WatchList/
├── app/
│   ├── auth/
│   │   ├── login.py          # POST /auth/login
│   │   ├── registration.py   # POST /auth/register
│   │   └── security.py       # JWT, bcrypt
│   ├── core/
│   │   ├── main.py           # FastAPI app, всі ендпоїнти, WS
│   │   ├── ws_manager.py     # ConnectionManager для WebSocket
│   │   ├── redis_client.py   # Redis підключення
│   │   ├── logger.py
│   │   └── mytools.py
│   ├── database/
│   │   ├── database.py       # AsyncEngine, get_db
│   │   ├── models.py         # SQLAlchemy ORM (User, Movie, MovieStatus)
│   │   └── schemas.py        # Pydantic схеми
│   └── services/
│       └── tmdb.py           # TMDBService з Redis кешем
└── frontend/
    └── index.html            # Vue 3 SPA
```

## Setup

### 1. Залежності

```bash
uv sync
```

### 2. Змінні середовища `.env`

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/watchlist
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
TMDB_API_KEY=your-tmdb-api-key
```

### 3. Запуск

```bash
uv run uvicorn app.core.main:app --reload --port 8000
```

Фронтенд доступний за адресою: **http://127.0.0.1:8000/app/**

## API Endpoints

| Method | Path                   | Description                  |
| ------ | ---------------------- | ---------------------------- |
| POST   | `/auth/register`       | Реєстрація                   |
| POST   | `/auth/login`          | Логін → JWT                  |
| GET    | `/movies/`             | Список фільмів (з фільтрами) |
| POST   | `/movies/`             | Додати фільм                 |
| PATCH  | `/movies/{id}`         | Оновити фільм                |
| DELETE | `/movies/{id}`         | Видалити фільм               |
| GET    | `/movies/stats/`       | Статистика переглядів        |
| GET    | `/movies/search`       | Пошук у TMDB                 |
| GET    | `/movies/{id}/details` | Деталі фільму з TMDB         |
| WS     | `/ws?token=<jwt>`      | WebSocket з'єднання          |

## WebSocket

Після логіну фронтенд автоматично підключається до `/ws?token=<jwt>`.  
При будь-якій зміні в списку фільмів — сервер надсилає подію всім відкритим вкладкам юзера:

```json
{"event": "added",   "movie": {"id": 1, "title": "...", "status": "want_to_watch"}}
{"event": "updated", "movie": {"id": 1, "title": "...", "status": "watched"}}
{"event": "deleted", "movie_id": 1}
```

При обриві з'єднання — auto-reconnect через 3 сек.
