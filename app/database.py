from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from logger import setup_logger
import os
from dotenv import load_dotenv

section = 'DATABASE'
db_logger = setup_logger() 

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://localhost/default_db")
engine = create_async_engine(DATABASE_URL, future=True, echo=True)
async_session = async_sessionmaker(engine, 
    class_=AsyncSession, 
    expire_on_commit=False, 
    autocommit=False, 
    autoflush=False
)

async def get_db():
    db_logger.debug("Creating async database session")

    async with async_session() as session:
        try:
    
            yield session
            await session.commit()

        except Exception as e:

            db_logger.error(f"{session} | Database error: {e}")
            await session.rollback()
            raise e
            
        finally:

            await session.close()
            db_logger.debug(f"{section} | Closed async database session")


async def init_db():
    import models
    db_logger.info(f"{section} | Creating database tables")
    # Створення таблиці (Обов'язоково має бути модель класу у файлі (або імпорт))
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
        await conn.run_sync(models.Base.metadata.create_all)

    db_logger.info(f"{section} | Database tables created")