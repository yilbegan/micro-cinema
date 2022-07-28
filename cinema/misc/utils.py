import asyncio
import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# TODO: More formats and check if audio only

format_extensions = {"matroska": "mkv", "webm": "webm", "mp4": "mp4"}
youtube_regex = re.compile(
    r"^(?:https?:)?(?:\/\/)?(?:youtu\.be\/|(?:www\.|m\.)?youtube\.com\/"
    r"(?:watch|v|embed)(?:\.php)?(?:\?.*v=|\/))"
    r"([a-zA-Z0-9\_-]{7,15})(?:[\?&][a-zA-Z0-9\_-]+=[a-zA-Z0-9\_-]+)*$"
)


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


class YoutubeException(Exception):
    pass


class YoutubeQuality(Enum):
    LOW = "best[height<=?360][width<=?480]"
    MEDIUM = "best[height<=?480][width<=?640]"
    HIGH = "best[height<=?720][width<=?1280]"


async def resolve_youtube(
    url: str, quality: YoutubeQuality = YoutubeQuality.MEDIUM
) -> str:
    process = await asyncio.create_subprocess_shell(
        "command -v youtube-dl", stdout=subprocess.DEVNULL
    )

    await process.wait()
    if process.returncode != 0:
        raise FileNotFoundError("youtube-dl required for youtube videos!")

    cmd = ["youtube-dl", "-g", "-f", quality.value, url]
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise YoutubeException(stderr.decode())

    return stdout.decode().split("\n")[0]


async def resolve_location(location: str) -> str:
    if youtube_regex.fullmatch(location):
        return await resolve_youtube(location)
    elif re.match("^https?://.*$", location):
        return location
    else:
        if Path(location).is_file():
            return location
        raise FileNotFoundError(location)


async def get_media_info(location: str) -> MediaInfo:
    location = await resolve_location(location)

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
        "default=nw=1",
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd, stderr=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise FFmpegException(stderr)

    stdout = stdout.decode("utf-8").strip()
    entries = {}
    for line in stdout.split("\n"):
        entry_name, entry_value = line.split("=", 1)
        entries[entry_name] = entry_value

    duration, format_name = entries["duration"], entries["format_name"]
    duration = int(float(duration))
    format_names = format_name.split(",")
    for format_name in format_names:
        if format_name in format_extensions:
            extension = format_extensions[format_name]
            break
    else:
        raise FFmpegException("Unknown file format!")

    return MediaInfo(duration=duration, extension=extension)
