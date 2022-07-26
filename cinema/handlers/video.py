from pyrogram import Client
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls import StreamType
from pytgcalls.exceptions import GroupCallNotFound
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.exceptions import NotInGroupCallError
from pytgcalls.types import AudioVideoPiped
from pytgcalls.types import StreamAudioEnded
from pytgcalls.types import StreamVideoEnded
from pytgcalls.types import Update

from ..database import Bookmark
from ..database import Movie
from ..misc.clock import ViewStatus
from ..misc.context import chat_clock
from ..misc.context import pyrogram_client
from ..misc.context import tgcalls_client


async def add_bookmark(chat_id: int):
    clock = chat_clock.get()
    current_status = clock.get(chat_id)
    if current_status is None:
        return

    current_status.pause()
    progress = current_status.get_progress()
    del clock[chat_id]

    await Bookmark.create(
        chat_id=chat_id,
        movie=await Movie.filter(id=current_status.movie_id).first(),
        episode=current_status.episode,
        timecode=progress,
    )


async def stream_movie(
    message: Message, movie_id: int, episode: int, timecode: int | None = None
):
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

    clock = chat_clock.get()
    current_status = clock.get(message.chat.id)

    if active_call is None and current_status is None:
        action = tgcalls.join_group_call(
            message.chat.id,
            AudioVideoPiped(
                f"./data/movies/{movie_id}/{episode}.mkv",
                additional_ffmpeg_parameters=(
                    f" -ss {int(timecode)} " if timecode is not None else ""
                ),
            ),
            stream_type=StreamType().pulse_stream,
        )
    else:
        await add_bookmark(message.chat.id)
        action = tgcalls.change_stream(
            message.chat.id,
            AudioVideoPiped(
                f"./data/movies/{movie_id}/{episode}.mkv",
                additional_ffmpeg_parameters=(
                    f" -ss {int(timecode)} " if timecode is not None else ""
                ),
            ),
        )

    clock[message.chat.id] = ViewStatus(
        movie_id=movie_id, episode=episode, progress=timecode
    )

    try:
        await action
    except NoActiveGroupCall:
        await message.reply("Please, create a group call.")


async def play_movie(_: Client, message: Message):
    match = message.matches[0]
    movie_id, episode = match.groups()
    movie_id = int(movie_id)
    episode = int(episode or 1)
    await stream_movie(
        message=message,
        movie_id=movie_id,
        episode=episode,
    )


async def play_bookmark(_: Client, message: Message):
    match = message.matches[0]
    bookmark_id = match.group(1)
    bookmark = await Bookmark.filter(id=bookmark_id).first()
    if bookmark is None:
        await message.reply("Bookmark not found!")
        return

    await stream_movie(
        message=message,
        movie_id=bookmark.movie.id,
        episode=bookmark.episode,
        timecode=bookmark.timecode,
    )


async def stop_movie(_: Client, message: Message):
    tgcalls = tgcalls_client.get()
    match = message.matches[0]
    clock = chat_clock.get()
    current_status = clock.get(message.chat.id)
    if current_status is None:
        await message.reply("Nothing to stop.")
        return

    if not match.group(1):
        await add_bookmark(message.chat.id)
    else:
        del clock[message.chat.id]

    try:
        await tgcalls.leave_group_call(chat_id=message.chat.id)
    except (NotInGroupCallError, GroupCallNotFound, NoActiveGroupCall):
        await message.reply("Nothing to stop.")
    else:
        await message.reply("Stopped.")


async def pause_movie(_: Client, message: Message):
    tgcalls = tgcalls_client.get()
    clock = chat_clock.get()
    current_status = clock.get(message.chat.id)
    if current_status is None:
        await message.reply("Nothing to pause.")
        return

    current_status.pause()

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
    clock = chat_clock.get()
    current_status = clock.get(message.chat.id)
    if current_status is None:
        await message.reply("Nothing to resume.")
        return

    current_status.resume()

    try:
        await tgcalls.resume_stream(
            message.chat.id,
        )
    except (NotInGroupCallError, GroupCallNotFound, NoActiveGroupCall):
        await message.reply("Nothing to resume.")
    else:
        await message.reply("Resumed.")


async def on_stream_ends(client: PyTgCalls, update: Update):
    pyro_client = pyrogram_client.get()
    clock = chat_clock.get()
    current_status = clock.get(update.chat_id)
    if current_status is None:
        return

    del clock[update.chat_id]
    current_status.pause()
    movie = await Movie.filter(id=current_status.movie_id).first()
    if movie is None:
        return

    if current_status.episode == len(movie.episodes):
        await pyro_client.send_message(
            chat_id=update.chat_id, text=f"Thanks for watching `{movie.title}`!"
        )
        return

    await pyro_client.send_message(
        chat_id=update.chat_id,
        text=(
            f"**Now playing**\n\n"
            f"{movie.title}: "
            f"{movie.episodes[current_status.episode - 1]} "
            f"({current_status.episode})"
        ),
    )

    await client.change_stream(
        update.chat_id,
        AudioVideoPiped(
            f"./data/movies/{movie.id}/{current_status.episode + 1}.mkv",
        ),
    )
