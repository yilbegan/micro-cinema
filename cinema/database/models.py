from tortoise import fields
from tortoise.models import Model
from .fields import DataClassField


class Movie(Model):
    id: int = fields.IntField(pk=True)
    title: str = fields.CharField(max_length=128)
    episodes: str = DataClassField(list[str])
    bookmarks: fields.ReverseRelation["Bookmark"]


class Bookmark(Model):
    id: int = fields.IntField(pk=True)
    chat_id: int = fields.IntField()
    movie: fields.ForeignKeyRelation[Movie] = fields.ForeignKeyField("models.Movie", related_name="bookmarks")
    episode: int = fields.IntField()
    timecode: int = fields.IntField()