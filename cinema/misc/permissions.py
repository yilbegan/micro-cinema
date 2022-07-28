from typing import Awaitable
from typing import Callable

from loguru import logger
from pyrogram import Client
from pyrogram.types import Message

from cinema.config import get_settings


def admin_required(func: Callable[[Client, Message], Awaitable]):
    async def wrapper(client: Client, message: Message):
        if message.from_user is None:
            return
        settings = get_settings()
        user = message.from_user
        privileged = settings.bot.admins
        if (
            user.id in privileged
            or user.username in privileged
            or "@" + user.username in privileged
        ):
            return await func(client, message)
        logger.info(
            f"Insufficient privileges for '{message.text}' (@{message.from_user.username}:{user.id})"
        )
        await message.react(emoji="🤬")

    return wrapper


def moderator_required(func: Callable[[Client, Message], Awaitable]):
    async def wrapper(client: Client, message: Message):
        if message.from_user is None:
            return
        settings = get_settings()
        user = message.from_user
        privileged = settings.bot.admins + settings.bot.moderators
        if (
            user.id in privileged
            or user.username in privileged
            or "@" + user.username in privileged
        ):
            return await func(client, message)
        logger.info(
            f"Insufficient privileges for '{message.text}' (@{message.from_user.username}:{user.id})"
        )
        await message.react(emoji="🤬")

    return wrapper
