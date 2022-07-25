from pyrogram import Client
from pyrogram import filters
from .control import movies_list, movies_inspect
from .video import play_movie, stop_movie, pause_movie, resume_movie
import re


def setup_handlers(client: Client):
    # control.py
    client.on_message(
        filters.regex(re.compile(r"(^\/movies list$)|(^\/movies$)"))
    )(movies_list)

    client.on_message(
        filters.regex(re.compile(r"^\/movies inspect ([0-9]+)$"))
    )(movies_inspect)

    # video.py

    client.on_message(
        filters.regex(re.compile(r"^\/play ([0-9]+)(?: ([0-9]+))?$"))
    )(play_movie)

    client.on_message(
        filters.regex(re.compile(r"^\/stop$"))
    )(stop_movie)

    client.on_message(
        filters.regex(re.compile(r"^\/pause$"))
    )(pause_movie)

    client.on_message(
        filters.regex(re.compile(r"^\/resume$"))
    )(resume_movie)
