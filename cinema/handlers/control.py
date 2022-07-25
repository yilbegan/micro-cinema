import asyncio
import os
import shutil
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from pyrogram import Client
from pyrogram.types import Message

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
    contents = ZipFile(open(path, "rb"))

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
    os.makedirs(movie_dir)
    for i, file in enumerate(episodes):
        with open(file, "rb") as infile, open(movie_dir / f"{i + 1}.mkv") as outfile:
            shutil.copyfileobj(infile, outfile)
        movie.episodes.append(f"Episode {i + 1}")
    tempdir.cleanup()
    if not movie.episodes:
        await movie.delete()
        await message.reply("To add a movie you should send `zip` with `mkv` files!")
        return

    await movie.save()
    await message.reply(
        f"Added movie **#{movie.id}** (`{movie_title}`) with {len(episodes)}!"
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
