import pytgcalls.exceptions
from pyrogram import Client
from pyrogram.types import Message
from pytgcalls import StreamType
from pytgcalls.exceptions import GroupCallNotFound
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.exceptions import NotInGroupCallError
from pytgcalls.types import AudioVideoPiped

from ..context import tgcalls_client
from ..database import Movie


async def play_movie(_: Client, message: Message):
    match = message.matches[0]
    movie_id, episode = match.groups()
    movie_id = int(movie_id)
    episode = int(episode or 1)
    tgcalls = tgcalls_client.get()

    movie = await Movie.filter(id=movie_id).first()
    if movie is None:
        await message.reply("Invalid movie id.")
        return
    if episode > len(movie.episodes):
        await message.reply("Invalid episode.")
        return

    try:
        active_call = tgcalls.get_active_call(message.chat.id)
    except GroupCallNotFound:
        active_call = None

    await message.reply(
        f"**Starting**\n\n"
        f"Movie: `{movie.title}`\n"
        f"Episode: `{movie.episodes[episode - 1]} ({episode})`"
    )

    if active_call is None:
        action = tgcalls.join_group_call(
            message.chat.id,
            AudioVideoPiped(
                f"./data/movies/{movie_id}/{episode}.mkv",
            ),
            stream_type=StreamType().pulse_stream,
        )
    else:
        action = tgcalls.change_stream(
            message.chat.id,
            AudioVideoPiped(
                f"./data/movies/{movie_id}/{episode}.mkv",
            ),
        )

    try:
        await action
    except NoActiveGroupCall:
        await message.reply("Please, create a group call.")


async def stop_movie(_: Client, message: Message):
    tgcalls = tgcalls_client.get()
    try:
        await tgcalls.leave_group_call(chat_id=message.chat.id)
    except (NotInGroupCallError, GroupCallNotFound, NoActiveGroupCall):
        await message.reply("Already stopped.")
    else:
        await message.reply("Stopped.")


async def pause_movie(_: Client, message: Message):
    tgcalls = tgcalls_client.get()
    try:
        await tgcalls.pause_stream(
            message.chat.id,
        )
    except (NotInGroupCallError, GroupCallNotFound, NoActiveGroupCall):
        await message.reply("Nothing to pause.")
    else:
        await message.reply("Paused.")


async def resume_movie(_: Client, message: Message):
    tgcalls = tgcalls_client.get()
    try:
        await tgcalls.resume_stream(
            message.chat.id,
        )
    except (NotInGroupCallError, GroupCallNotFound, NoActiveGroupCall):
        await message.reply("Nothing to resume.")
    else:
        await message.reply("Resumed.")
