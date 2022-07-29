import os
import re
import uuid
from pathlib import Path

from loguru import logger
from pyrogram import Client
from pyrogram.types import Message

from ..database import Bookmark
from ..database import Episode
from ..database import Movie
from ..database import update_from_settings
from ..misc.permissions import admin_required
from ..misc.permissions import moderator_required
from ..misc.utils import download_url
from ..misc.utils import download_youtube
from ..misc.utils import FFmpegException
from ..misc.utils import format_time
from ..misc.utils import get_media_info
from ..misc.utils import youtube_regex
from ..misc.utils import YoutubeException


async def movies_list(_: Client, message: Message):
    movies = await Movie.all().limit(20)
    reply = ["**Available movies:**", ""]
    for movie in movies:
        reply.append(f"{movie.movie_id}: `{movie.title}`")
    if not movies:
        reply.append("`Nothing :(`")

    await message.reply("\n".join(reply))


async def movies_inspect(_: Client, message: Message):
    match = message.matches[0]
    movie_id = match.group(1)
    movie = await Movie.filter(movie_id=movie_id).first()
    if movie is None:
        await message.reply("Invalid movie id.")
        return

    reply = [f"**{movie.title}**", "", f"`{movie.description.strip()}`", ""]
    episodes = await movie.episodes.order_by("episode_id").all()
    for i, episode in enumerate(episodes):
        reply.append(
            f"{episode.episode_id}. `{episode.title}` [{format_time(episode.duration)}]"
        )
    await message.reply("\n".join(reply))


async def bookmarks_list(_: Client, message: Message):
    bookmarks = (
        await Bookmark.filter(chat_id=message.chat.id)
        .prefetch_related("movie", "episode")
        .all()
    )
    reply = ["**Bookmarks:**", ""]
    for bookmark in bookmarks:
        reply.append(
            f"{bookmark.id}. {bookmark.movie.title} ({bookmark.episode}: {format_time(bookmark.timecode)})"
        )
    if not bookmarks:
        reply.append("`Nothing :(`")

    await message.reply("\n".join(reply))


@moderator_required
async def bookmarks_delete(_: Client, message: Message):
    match = message.matches[0]
    bookmark_id = match.group(1)
    bookmark = await Bookmark.filter(
        chat_id=message.chat.id, bookmark_id=bookmark_id
    ).first()
    if bookmark is None:
        await message.reply("Invalid bookmark id.")
        return
    await bookmark.delete()
    await message.reply(f"Bookmark `{bookmark.name}` deleted.")


@moderator_required
async def bookmarks_rename(_: Client, message: Message):
    match = message.matches[0]
    bookmark_id = match.group(1)
    new_name = match.group(2)
    bookmark = await Bookmark.filter(
        chat_id=message.chat.id, bookmark_id=bookmark_id
    ).first()
    if bookmark is None:
        await message.reply("Invalid bookmark id.")
        return

    bookmark.name = new_name
    await bookmark.save()
    await message.reply(f"Bookmark renamed.")


@admin_required
async def cache_episode(_: Client, message: Message):
    match = message.matches[0]
    movie_id, episode = match.groups()
    movie_id = movie_id
    episode = int(episode or 1)

    movie = await Movie.filter(movie_id=movie_id).first()
    if movie is None:
        await message.reply("Invalid movie id.")
        return
    episode = await Episode.filter(episode_id=episode, movie=movie).first()
    if episode is None:
        await message.reply("Invalid episode.")
        return

    if not re.fullmatch(r"^https?://.*$", episode.location):
        await message.reply("Already using local location.")
        return

    try:
        media_info = await get_media_info(episode.location)
    except FFmpegException:
        await message.reply(f"Invalid media `{movie_id}:{episode.episode_id}`!")
        return

    if episode.cache is not None:
        reply_text = f"Updating cache for `{movie_id}:{episode.episode_id}` [{{}}/100]"
    else:
        reply_text = f"Caching `{movie_id}:{episode.episode_id}` [{{}}/100]"
    reply = await message.reply(reply_text.format(0))

    cache_path = Path("./movies_cache")
    cache_path.mkdir(parents=True, exist_ok=True)
    cache_path /= (
        f"{movie_id}_{episode.episode_id:03d}_{uuid.uuid4().hex}.{media_info.extension}"
    )

    if youtube_regex.fullmatch(episode.location):
        try:
            await download_youtube(output=cache_path, youtube_url=episode.location)
        except FileNotFoundError:
            await reply.delete()
            await message.reply("Youtube-dl is required for youtube videos!")
            return
        except YoutubeException:
            await reply.delete()
            await message.reply("Unable to cache from youtube!")
            logger.exception("Unable to cache from youtube!")
            return
    else:
        current_progress = 0
        step = 25
        async for progress in download_url(
            location=episode.location, output=cache_path
        ):
            if progress // step == current_progress:
                continue
            current_progress = progress // step
            await reply.edit_text(reply_text.format(current_progress))

    os.remove(episode.cache)
    episode.cache = str(cache_path)
    await episode.save()

    await reply.edit_text(f"Cached `{movie_id}:{episode.episode_id}`.")


@admin_required
async def movies_update(_: Client, message: Message):
    try:
        await update_from_settings()
    except:  # noqa
        logger.exception("Error during database update")
        await message.reply("Error during update!")
    else:
        await message.reply("Movies have been updated from settings.")
