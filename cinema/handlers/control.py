from pyrogram import Client
from pyrogram.types import Message
from ..database import Movie


async def movies_list(_: Client, message: Message):
    movies = await Movie.all()
    reply = ["*Available movies:*", ""]
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

    reply = [f"*{movie.title}*", ""]
    for i, episode in enumerate(movie.episodes):
        reply.append(f"{i + 1}. `{episode}`")
    await message.reply("\n".join(reply))
