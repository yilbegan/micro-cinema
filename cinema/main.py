import json

import pyrogram
from pytgcalls import idle
from pytgcalls import PyTgCalls

from .context import tgcalls_client
from .database import init as init_db
from .handlers import setup_handlers


async def main():
    await init_db()

    with open("./data/account/metadata.json", "r") as f:
        metadata = json.load(f)

    client = pyrogram.Client(
        "cinema",
        api_id=metadata.get("api_id") or metadata.get("app_id"),
        workdir="./data/account",
        device_model=metadata.get("device"),
        app_version=metadata.get("app_version"),
        lang_code=metadata.get("lang_pack"),
    )

    setup_handlers(client)
    tgcalls = PyTgCalls(client)
    tgcalls_client.set(tgcalls)
    await tgcalls.start()
    await idle()
