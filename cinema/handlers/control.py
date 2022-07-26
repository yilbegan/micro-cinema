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


async def movies_list(_: Client, message: Message):
    movies = await Movie.all()
    reply = ["**Available movies:**", ""]
    for movie in movies:
        reply.append(f"{movie.id}. `{movie.title}`")
    if not movies:
        reply.append("`Nothing :(`")

    await message.reply("\n".join(reply))


async def movies_inspect(_: Client, message: Message):
    match = message.matches[0]
    movie_id = int(match.group(1))
    movie = await Movie.filter(id=movie_id).first()
    if movie is None:
        await message.reply("Invalid movie id.")
        return

    reply = [f"**{movie.title}**", ""]
    for i, episode in enumerate(movie.episodes):
        reply.append(f"{i + 1}. `{episode}`")
    await message.reply("\n".join(reply))


def unzip_large(path: Path):
    contents = ZipFile(open(path / "movie.zip", "rb"))

    for file in contents.infolist():
        # wtf lol
        if file.filename == "movie.zip":
            continue
        if file.is_dir():
            continue
        output_name = Path(file.filename).name
        if not output_name.endswith(".mkv"):
            continue
        with open(path / output_name, "wb") as outfile, contents.open(file) as infile:
            shutil.copyfileobj(infile, outfile)


async def movies_add(_: Client, message: Message):
    if message.document is None or not message.document.file_name.endswith(".zip"):
        await message.reply("Please, attach a zip file.")
        return

    await message.reply("Downloading your movie...")
    match = message.matches[0]
    movie_title = match.group(1) or "Le cool movie"

    tempdir = TemporaryDirectory()
    tempdir_path = Path(tempdir.name)
    await message.download(tempdir_path / "movie.zip")
    if not zipfile.is_zipfile(tempdir_path / "movie.zip"):
        tempdir.cleanup()
        await message.reply("Invalid zip file!")
        return

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, unzip_large, tempdir_path)

    movie = await Movie.create(title=movie_title)
    episodes = sorted(tempdir_path.glob("*.mkv"))
    movie_dir = Path(f"./data/movies/{movie.id}")
    os.makedirs(movie_dir, exist_ok=True)
    for i, file in enumerate(episodes):
        with open(file, "rb") as infile, open(
            movie_dir / f"{i + 1}.mkv", "wb"
        ) as outfile:
            shutil.copyfileobj(infile, outfile)
        movie.episodes.append(f"Episode {i + 1}")
    tempdir.cleanup()
    if not movie.episodes:
        await movie.delete()
        await message.reply("To add a movie you should send `zip` of `mkv` files!")
        return

    await movie.save()
    await message.reply(
        f"Added movie **#{movie.id}** (`{movie_title}`) with {len(episodes)} episodes!"
    )


async def movies_rename(_: Client, message: Message):
    match = message.matches[0]
    movie_id = int(match.group(1))
    movie_title = match.group(2)

    movie = await Movie.filter(id=movie_id).first()
    if movie is None:
        await message.reply("Invalid movie id.")
        return
    movie.title = movie_title
    await movie.save()
    await message.reply(f"Updated title for movie **#{movie_id}**")


async def bookmarks_list(_: Client, message: Message):
    bookmarks = (
        await Bookmark.filter(chat_id=message.chat.id).prefetch_related("movie").all()
    )
    reply = ["**Bookmarks:**", ""]
    for bookmark in bookmarks:
        reply.append(f"{bookmark.id}. `{bookmark.movie.title}` ({bookmark.episode})")
    if not bookmarks:
        reply.append("`Nothing :(`")

    await message.reply("\n".join(reply))


async def movies_remove(_: Client, message: Message):
    movie_id = int(message.matches[0].group(1))
    movie = await Movie.filter(id=movie_id).first()
    if movie is None:
        await message.reply("Invalid movie id.")
        return

    shutil.rmtree(Path(f"./data/movies/{movie.id}"))
    await movie.delete()
    await message.reply(f"Deleted movie #{movie.id}.")
