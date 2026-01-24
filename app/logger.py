import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger():    
    # Створюємо папку logs якщо її немає
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Шлях до файлу логів
    log_file = log_dir / "watchlist.log"
    
    # Створюємо логер
    logger = logging.getLogger("watchlist")
    logger.setLevel(logging.DEBUG)
    
    # Очищаємо попередні handler'и (якщо є)
    logger.handlers.clear()
    
    # Формат логів
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler для файлу з ротацією
    # Максимальний розмір файлу: 5 МБ, кількість backup файлів: 3
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=5*1024*1024,  # 5 МБ
        backupCount=3,          # Зберігати 3 backup файли
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Handler для консолі
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Додаємо handler'и до логера
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger