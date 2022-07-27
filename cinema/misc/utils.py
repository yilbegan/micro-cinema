import asyncio
from dataclasses import dataclass


# TODO: More formats and check if audio only
format_extensions = {"matroska": "mkv", "webm": "webm", "mp4": "mp4"}


def format_time(time: int) -> str:
    seconds = time % 60
    minutes = (time // 60) % 60
    hours = time // 60 // 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


@dataclass
class MediaInfo:
    duration: int
    extension: str


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
        "format=duration,format_name",  # format=duration,format_name:stream=codec_type
        "-hide_banner",
        "-of",
        "default=nk=1:nw=1",
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd, stderr=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise FFmpegException(stderr)

    stdout = stdout.decode("utf-8").strip()
    duration, format_names = stdout.split("\n")
    duration = int(float(duration))
    format_names = format_names.split(",")
    for format_name in format_names:
        if format_name not in format_extensions:
            extension = format_extensions[format_name]
            break
    else:
        raise FFmpegException("Unknown file format!")

    return MediaInfo(duration=duration, format=extension)
