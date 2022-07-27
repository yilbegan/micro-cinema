import asyncio
from dataclasses import dataclass


def format_time(time: int) -> str:
    seconds = time % 60
    minutes = (time // 60) % 60
    hours = time // 60 // 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


@dataclass
class MediaInfo:
    duration: int


class FFmpegException(Exception):
    pass


async def get_media_info(location: str) -> MediaInfo:
    cmd = [
        "ffprobe",
        "-i",
        location,
        "-v",
        "error",
        "-show_entries",
        "format=duration" "-hide_banner",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd, stderr=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise FFmpegException(stderr)
    return MediaInfo(duration=int(float(stdout)))
