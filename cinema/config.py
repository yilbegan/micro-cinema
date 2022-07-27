from dataclasses import dataclass
from dataclasses import field
from enum import Enum

import dataclass_factory
import pyaml_env


class Language(Enum):
    ENGLISH = "en"


@dataclass
class BotSettings:
    admins: list[str | int] = field()
    moderators: list[str | int] = field(default_factory=list)
    database_url: str = field(default="sqlite://./micro-cinema.db")
    language: Language = field(default=Language.ENGLISH)


@dataclass
class EpisodeSettings:
    location: str = field()
    title: str = field(default="Le cool episode")


@dataclass
class MovieSettings:
    id: str = field()
    title: str = field(default="Le cool movie")
    description: str | None = field(default="No description")
    episodes: list[EpisodeSettings] = field(default_factory=list)


@dataclass
class Settings:
    bot: BotSettings = field()
    movies: list[MovieSettings] = field()


def get_settings(path: str = "./config.yaml") -> Settings:
    config = pyaml_env.parse_config(path)
    factory = dataclass_factory.Factory()
    return factory.load(config, Settings)
