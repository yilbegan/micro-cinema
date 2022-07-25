from tortoise import fields
from tortoise.models import Model
from .fields import DataClassField


class Movie(Model):
    title: str = fields.CharField(max_length=128)
    chapters: str = DataClassField(list[str])


class ChatStatus(Model):
    chat_id: int = fields.IntField()
    movie: Movie | None = fields.ForeignKeyField("models.Movie")
    chapter: int = fields.IntField()
    timecode: int = fields.IntField()
