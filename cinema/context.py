from contextvars import ContextVar
from pytgcalls import PyTgCalls

tgcalls_client: ContextVar[PyTgCalls] = ContextVar("tgcalls_client")
