import json

import pyrogram
from loguru import logger
from pytgcalls import idle
from pytgcalls import PyTgCalls

from .database import init as init_db
from .database import update_from_settings
from .handlers import setup_handlers
from .handlers import setup_tgcalls
from .misc.context import chat_clock
from .misc.context import pyrogram_client
from .misc.context import tgcalls_client


@logger.catch(reraise=True)
async def main():
    logger.info("Starting...", enqueue=True)

    await init_db()
    await update_from_settings()

    with open("./account/cinema.metadata.json", "r") as f:
        metadata = json.load(f)

    client = pyrogram.Client(
        "cinema",
        api_id=metadata.get("api_id") or metadata.get("app_id"),
        workdir="./account",
        device_model=metadata.get("device"),
        app_version=metadata.get("app_version"),
        lang_code=metadata.get("lang_pack"),
    )

    setup_handlers(client)
    tgcalls = PyTgCalls(client)
    setup_tgcalls(tgcalls)
    tgcalls_client.set(tgcalls)
    pyrogram_client.set(client)
    chat_clock.set({})

    logger.info("Starting bot...", enqueue=True)
    await tgcalls.start()
    await idle()
