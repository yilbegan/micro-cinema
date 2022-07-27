import re

from pyrogram import Client
from pyrogram import filters
from pytgcalls import PyTgCalls

from .control import bookmarks_list
from .control import movies_inspect
from .control import movies_list
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

    client.on_message(filters.regex(re.compile(r"^\/movies inspect ([a-z_]+)$")))(
        movies_inspect
    )

    client.on_message(filters.regex(re.compile(r"^\/bookmarks( list)?$")))(
        bookmarks_list
    )

    # video.py

    client.on_message(filters.regex(re.compile(r"^\/play ([a-z_]+)(?: ([0-9]+))?$")))(
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
