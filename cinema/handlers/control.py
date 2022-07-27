import asyncio
import os
import shutil
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from pyrogram import Client
from pyrogram.types import Message

from ..database import Bookmark
from ..database import Movie
from ..misc.utils import format_time


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

    reply = [f"**{movie.title}**", "", f"`{movie.description}`", ""]
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
