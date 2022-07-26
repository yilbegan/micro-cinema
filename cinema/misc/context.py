from contextvars import ContextVar

from pyrogram import Client
from pytgcalls import PyTgCalls

from .clock import ViewStatus

# TODO: Rename it
chat_clock: ContextVar[dict[int, ViewStatus]] = ContextVar("chat_clock")
tgcalls_client: ContextVar[PyTgCalls] = ContextVar("tgcalls_client")
pyrogram_client: ContextVar[Client] = ContextVar("pyrogram_client")
