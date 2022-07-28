import json
from pathlib import Path

from pyrogram import Client
from pyrogram.types import User


def main():
    session_path = (
        input("Enter file in which to save the session (./account/cinema): ")
        or "./account/cinema"
    )
    session_path = Path(session_path)
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.unlink(missing_ok=True)
    session_path.with_name(session_path.stem + ".session").unlink(missing_ok=True)

    print("You can get api_id and api_hash here: https://my.telegram.org/apps")
    api_id = int(input("Enter your api_id: "))
    api_hash = input("Enter your api_hash: ")

    client = Client(
        session_path.stem, workdir=session_path.parent, api_id=api_id, api_hash=api_hash
    )

    with client:
        me: User = client.get_me()
        print(f"Created session for @{me.username}.")

    with open(session_path.parent / f"{session_path.stem}.metadata.json", "w") as f:
        json.dump(
            {
                "api_id": api_id,
                "api_hash": api_hash,
            },
            f,
        )

    print("Session created.")


if __name__ == "__main__":
    main()
