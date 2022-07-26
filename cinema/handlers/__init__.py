import re

from pyrogram import Client
from pyrogram import filters
from pytgcalls import PyTgCalls

from .control import bookmarks_list
from .control import movies_add
from .control import movies_inspect
from .control import movies_list
from .control import movies_remove
from .control import movies_rename
from .video import on_stream_ends
from .video import pause_movie
from .video import play_bookmark
from .video import play_movie
from .video import resume_movie
from .video import stop_movie


def setup_handlers(client: Client):
    # control.py
    client.on_message(filters.regex(re.compile(r"(^\/movies list$)|(^\/movies$)")))(
        movies_list
    )

    client.on_message(filters.regex(re.compile(r"^\/movies inspect ([0-9]+)$")))(
        movies_inspect
    )

    client.on_message(filters.regex(re.compile(r"^\/movies add(?: \"(.{1,128})\")?$")))(
        movies_add
    )

    client.on_message(filters.regex(re.compile(r"^\/movies remove ([0-9]+)$")))(
        movies_remove
    )

    client.on_message(
        filters.regex(re.compile(r"^\/movies rename ([0-9]+) \"(.{1,128})\"$"))
    )(movies_rename)

    client.on_message(filters.regex(re.compile(r"^\/bookmarks( list)?$")))(
        bookmarks_list
    )

    # video.py

    client.on_message(filters.regex(re.compile(r"^\/play ([0-9]+)(?: ([0-9]+))?$")))(
        play_movie
    )

    client.on_message(filters.regex(re.compile(r"^\/play bookmark ([0-9]+)$")))(
        play_bookmark
    )

    client.on_message(filters.regex(re.compile(r"^\/stop( nosave)?$")))(stop_movie)
    client.on_message(filters.regex(re.compile(r"^\/pause$")))(pause_movie)
    client.on_message(filters.regex(re.compile(r"^\/resume$")))(resume_movie)


def setup_tgcalls(client: PyTgCalls):
    client.on_stream_end()(on_stream_ends)
