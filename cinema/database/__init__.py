import asyncio
import itertools
from dataclasses import dataclass

from loguru import logger
from tortoise import Tortoise
from tortoise import transactions

from ..config import EpisodeSettings
from ..config import get_settings
from ..config import MovieSettings
from .models import Bookmark
from .models import Episode
from .models import Movie


async def init():
    logger.info("Initializing database...", enqueue=True)
    settings = get_settings()

    await Tortoise.init(
        {
            "connections": {"default": settings.bot.database_url},
            "apps": {
                "models": {
                    "models": ["cinema.database.models"],
                    "default_connection": "default",
                },
            },
        }
    )

    await Tortoise.generate_schemas(safe=True)


@dataclass
class MediaInfo:
    duration: int


class FFmpegException(Exception):
    pass


async def get_media_info(location: str) -> MediaInfo:
    cmd = [
        "ffprobe",
        "-i",
        location,
        "-v",
        "error",
        "-show_entries",
        "format=duration" "-hide_banner",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
    ]

    process = await asyncio.create_subprocess_shell(
        cmd, stderr=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise FFmpegException(stderr)
    return MediaInfo(duration=int(float(stdout)))


@transactions.atomic
async def update_movie(movie_db: Movie, movie_settings: MovieSettings):
    movie_db.title = movie_settings.title
    movie_db.description = movie_settings.description

    for i, (episode_db, episode_settings) in enumerate(
        itertools.zip_longest(
            movie_db.episodes, movie_settings.episodes, fillvalue=None
        )
    ):
        episode_db: Episode | None
        episode_settings: EpisodeSettings | None
        if episode_db is None:
            media_info = await get_media_info(episode_settings.location)
            await Episode.create(
                episode_id=i + 1,
                location=episode_settings.location,
                duration=media_info.duration,
                title=episode_settings.title,
                movie=movie_db,
            )
        elif episode_settings is None:
            await episode_db.delete()
        elif episode_settings.location != episode_db.location:
            media_info = await get_media_info(episode_settings.location)
            await episode_db.delete()
            await Episode.create(
                episode_id=i + 1,
                location=episode_settings.location,
                duration=media_info.duration,
                title=episode_settings.title,
                movie=movie_db,
            )
        elif episode_settings.title != episode_db.title:
            episode_db.title = episode_settings.title
            await episode_db.save()
    await movie_db.save()


@transactions.atomic
async def create_movie(movie_settings: MovieSettings):
    movie = await Movie.create(
        movie_id=movie_settings.id,
        title=movie_settings.title,
        description=movie_settings.description,
    )

    for i, episode in enumerate(movie_settings.episodes):
        media_info = await get_media_info(episode.location)
        await Episode.create(
            episode_id=i + 1,
            location=episode.location,
            duration=media_info.duration,
            title=episode.title,
            movie=movie,
        )


@logger.catch(reraise=True)
async def update_from_settings():
    settings = get_settings()
    logger.info("Updating database from settings...", enqueue=True)
    for movie_settings in settings.movies:
        movie_db = (
            await Movie.filter(movie_id=movie_settings.id)
            .prefetch_related("episodes")
            .first()
        )
        if movie_db is not None:
            logger.info(f"Updating movie '{movie_settings.id}'...", enqueue=True)
            await update_movie(movie_db, movie_settings)
        else:
            logger.info(f"Creating new movie '{movie_settings.id}'...", enqueue=True)
            await create_movie(movie_settings)
    logger.info("Database updated.", enqueue=True)
