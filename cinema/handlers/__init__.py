import re

from pyrogram import Client
from pyrogram import filters

from .control import movies_inspect
from .control import movies_list
from .video import pause_movie
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

    # video.py

    client.on_message(filters.regex(re.compile(r"^\/play ([0-9]+)(?: ([0-9]+))?$")))(
        play_movie
    )

    client.on_message(filters.regex(re.compile(r"^\/stop$")))(stop_movie)
    client.on_message(filters.regex(re.compile(r"^\/pause$")))(pause_movie)
    client.on_message(filters.regex(re.compile(r"^\/resume$")))(resume_movie)
