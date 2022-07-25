from .models import Bookmark, Movie
from tortoise import Tortoise
from ..config import Settings


async def init():
    settings = Settings()

    await Tortoise.init({
        "connections": {"default": settings.database_url},
        "apps": {
            "models": {
                "models": ["cinema.database.models"],
                "default_connection": "default",
            },
        },
    })

    await Tortoise.generate_schemas(safe=True)
