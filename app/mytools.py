# region Імпорти
from .models import Movie
# endregion


async def is_none_filter(**kwargs):
    filters = {**kwargs}
    result = []
    for field_name, value in filters.items():
        if value is not None and value != "":
            
            column = getattr(Movie, field_name, None)
            if column is not None:
                
                if field_name == "genre":
                    result.append(column.ilike(f"%{value}%"))
                else:
                    result.append(column == value)
                    
    return result