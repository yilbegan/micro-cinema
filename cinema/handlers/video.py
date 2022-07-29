from pathlib import Path

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
from ..misc.utils import format_time
from ..misc.utils import resolve_location


async def add_bookmark(chat_id: int, status: ViewStatus):
    movie = await Movie.filter(movie_id=status.movie_id).first()
    episode = await Episode.filter(movie=movie, episode_id=status.episode).first()

    await Bookmark.create(
        chat_id=chat_id,
        movie=movie,
        episode=episode,
        timecode=min(status.progress, episode.duration - 1),
    )


async def stream_movie(
    chat_id: int, movie_id: str, episode: int, timecode: int | None = None
):
    tgcalls = tgcalls_client.get()
    client = pyrogram_client.get()

    movie = await Movie.filter(movie_id=movie_id).first()
    if movie is None:
        await client.send_message(chat_id=chat_id, text="Invalid movie id.")
        return
    episode = await Episode.filter(episode_id=episode, movie=movie).first()
    if episode is None:
        await client.send_message(chat_id=chat_id, text="Invalid episode.")
        return

    await client.send_message(
        chat_id=chat_id,
        text=(
            f"**Starting**\n\n"
            f"Movie: `{movie.title}`\n"
            f"Episode: `{episode.title} ({episode.episode_id})`"
            + (f"\nTimecode: `{format_time(timecode)}`" if timecode else "")
        ),
    )

    clock = chat_clock.get()
    current_status = clock.get(chat_id)

    if current_status is None:
        action = tgcalls.join_group_call(
            chat_id,
            AudioVideoPiped(
                await resolve_location(
                    episode.location
                    if episode.cache is None or not Path(episode.cache).is_file()
                    else episode.cache
                ),
                additional_ffmpeg_parameters=(
                    f" -ss {int(timecode)} " if timecode is not None else ""
                ),
            ),
            stream_type=StreamType().pulse_stream,
        )
    else:
        del clock[chat_id]
        action = tgcalls.change_stream(
            chat_id,
            AudioVideoPiped(
                await resolve_location(
                    episode.location
                    if episode.cache is None or not Path(episode.cache).is_file()
                    else episode.cache
                ),
                additional_ffmpeg_parameters=(
                    f" -ss {int(timecode)} " if timecode is not None else ""
                ),
            ),
        )

    clock[chat_id] = ViewStatus(
        movie_id=movie_id, episode=episode.episode_id, progress=timecode
    )

    try:
        await action
    except NoActiveGroupCall:
        del clock[chat_id]
        await client.send_message(chat_id=chat_id, text="Please, create a group call.")


@moderator_required
async def play_movie(_: Client, message: Message):
    match = message.matches[0]
    movie_id, episode = match.groups()
    movie_id = movie_id
    episode = int(episode or 1)
    await stream_movie(
        chat_id=message.chat.id,
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
        chat_id=message.chat.id,
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

    if match.group(1):
        current_status.pause()
        await add_bookmark(chat_id=message.chat.id, status=current_status)
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


async def skip_to(_: Client, message: Message):
    clock = chat_clock.get()
    current_status = clock.get(message.chat.id)
    if current_status is None:
        await message.reply("Nothing to skip.")
        return

    timecode = message.matches[0].groups()[::-1]
    timecode = sum([int(v) * 60 ^ i for i, v in enumerate(timecode)])
    episode = await Episode.filter(
        movie__movie_id=current_status.movie_id, episode_id=current_status.episode
    ).first()
    if timecode > episode.duration:
        await message.reply(
            f"Invalid timecode `{format_time(timecode)}` > `{format_time(episode.duration)}`!"
        )
        return

    await stream_movie(
        chat_id=message.chat.id,
        movie_id=current_status.movie_id,
        episode=current_status.episode,
        timecode=timecode,
    )


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
            await resolve_location(
                episode.location
                if episode.cache is None or not Path(episode.cache).is_file()
                else episode.cache
            ),
        ),
    )
