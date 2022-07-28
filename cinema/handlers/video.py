from pyrogram import Client
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls import StreamType
from pytgcalls.exceptions import GroupCallNotFound
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.exceptions import NotInGroupCallError
from pytgcalls.types import AudioVideoPiped
from pytgcalls.types import Update

from ..database import Bookmark
from ..database import Episode
from ..database import Movie
from ..misc.clock import ViewStatus
from ..misc.context import chat_clock
from ..misc.context import pyrogram_client
from ..misc.context import tgcalls_client
from ..misc.permissions import moderator_required


@moderator_required
async def add_bookmark(chat_id: int):
    clock = chat_clock.get()
    current_status = clock.get(chat_id)
    if current_status is None:
        return

    current_status.pause()
    progress = current_status.get_progress()
    del clock[chat_id]
    movie = await Movie.filter(movie_id=current_status.movie_id).first()
    episode = await Episode.filter(
        movie=movie, episode_id=current_status.episode
    ).first()

    await Bookmark.create(
        chat_id=chat_id,
        movie=movie,
        episode=episode,
        timecode=min(progress, episode.duration - 1),
    )


async def stream_movie(
    message: Message, movie_id: str, episode: int, timecode: int | None = None
):
    tgcalls = tgcalls_client.get()

    movie = await Movie.filter(movie_id=movie_id).first()
    if movie is None:
        await message.reply("Invalid movie id.")
        return
    episode = await Episode.filter(episode_id=episode, movie=movie).first()
    if episode is None:
        await message.reply("Invalid episode.")
        return

    try:
        active_call = tgcalls.get_active_call(message.chat.id)
    except GroupCallNotFound:
        active_call = None

    await message.reply(
        f"**Starting**\n\n"
        f"Movie: `{movie.title}`\n"
        f"Episode: `{episode.title} ({episode.episode_id})`"
    )

    clock = chat_clock.get()
    current_status = clock.get(message.chat.id)

    if active_call is None and current_status is None:
        action = tgcalls.join_group_call(
            message.chat.id,
            AudioVideoPiped(
                episode.location if episode.cache is None else episode.cache,
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
                episode.location if episode.cache is None else episode.cache,
                additional_ffmpeg_parameters=(
                    f" -ss {int(timecode)} " if timecode is not None else ""
                ),
            ),
        )

    clock[message.chat.id] = ViewStatus(
        movie_id=movie_id, episode=episode.episode_id, progress=timecode
    )

    try:
        await action
    except NoActiveGroupCall:
        del clock[message.chat.id]
        await message.reply("Please, create a group call.")


@moderator_required
async def play_movie(_: Client, message: Message):
    match = message.matches[0]
    movie_id, episode = match.groups()
    movie_id = movie_id
    episode = int(episode or 1)
    await stream_movie(
        message=message,
        movie_id=movie_id,
        episode=episode,
    )


@moderator_required
async def play_bookmark(_: Client, message: Message):
    match = message.matches[0]
    bookmark_id = match.group(1)
    bookmark = await Bookmark.filter(id=bookmark_id).prefetch_related("movie").first()
    if bookmark is None:
        await message.reply("Bookmark not found!")
        return

    await stream_movie(
        message=message,
        movie_id=bookmark.movie.movie_id,
        episode=bookmark.episode,
        timecode=bookmark.timecode,
    )


@moderator_required
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


@moderator_required
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


@moderator_required
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
    movie = (
        await Movie.filter(movie_id=current_status.movie_id)
        .prefetch_related("episodes")
        .first()
    )
    if movie is None:
        return

    if current_status.episode == len(movie.episodes):
        await pyro_client.send_message(
            chat_id=update.chat_id, text=f"Thanks for watching `{movie.title}`!"
        )
        await client.leave_group_call(chat_id=update.chat_id)
        return

    current_status = ViewStatus(
        movie_id=movie.movie_id, episode=current_status.episode + 1
    )
    clock[update.chat_id] = current_status
    episode = await Episode.filter(
        movie=movie, episode_id=current_status.episode + 1
    ).first()

    await pyro_client.send_message(
        chat_id=update.chat_id,
        text=(
            f"**Now playing**\n\n"
            f"{movie.title}\n"
            f"{episode.title} "
            f"({current_status.episode})"
        ),
    )

    await client.change_stream(
        update.chat_id,
        AudioVideoPiped(
            episode.location if episode.cache is None else episode.cache,
        ),
    )
