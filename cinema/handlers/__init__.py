from pyrogram import Client
from pyrogram import filters
from .control import movies_list, movies_inspect
import re


def setup_handlers(client: Client):
    # control.py
    client.on_message(
        filters.regex(re.compile(r"(^\/movies list$)|(^\/movies$)"))
    )(movies_list)

    client.on_message(
        filters.regex(re.compile(r"^\/movies inspect ([0-9]+)$"))
    )

    # video.py

