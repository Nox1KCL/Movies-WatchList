# region Імпорти

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from logger import setup_logger
import os
from dotenv import load_dotenv

# endregion

section = 'DATABASE' # Для зрозумілості звідки логи
db_logger = setup_logger() 
load_dotenv() # Загружаєм змінні з .env

# Дістаєм ссилку на БД + не забуваєм про дефолт, щоб "create_async_engine" не возмущався
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://localhost/default_db")
engine = create_async_engine(DATABASE_URL, future=True, echo=True) # З'єднуємося з БД
async_session = async_sessionmaker(engine, # Фабрика сесій (Кожен запит отримує свою)
    class_=AsyncSession, 
    expire_on_commit=False, 
    autocommit=False, 
    autoflush=False
)

# Отримуємо БД сессію (Щоб не смітити мейн код, забути про закриття сесії)
async def get_db():
    db_logger.debug("Creating async database session")

    async with async_session() as session:
        try:
    
            yield session # Віддаєм сесію
            await session.commit()

        except Exception as e:

            db_logger.error(f"{session} | Database error: {e}")
            await session.rollback() # При помилці відкочуємося
            raise e
            
        finally:

            await session.close() # Закриваєм сесію
            db_logger.debug(f"{section} | Closed async database session")

# Ініціалізація БД
async def init_db():
    import models # Щоб Base мала метадані і розуміла яку таблицю створювати

    db_logger.info(f"{section} | Creating database tables")
    # Створення таблиці (Обов'язоково має бути модель класу у файлі (або імпорт))
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    db_logger.info(f"{section} | Database tables created")