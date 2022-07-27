from tortoise import fields
from tortoise.models import Model


class Movie(Model):
    id: int = fields.IntField(pk=True)
    movie_id: str = fields.CharField(unique=True, max_length=64)
    title: str = fields.CharField(max_length=128)
    description: str = fields.CharField(max_length=256)
    bookmarks: fields.ReverseRelation["Bookmark"]
    episodes: fields.ReverseRelation["Episode"]

    class Meta:
        table = "movies"


class Episode(Model):
    id: int = fields.IntField(pk=True)
    episode_id: int = fields.IntField()
    location: str = fields.CharField(max_length=256)
    cache: str | None = fields.CharField(max_length=256, null=True, default=None)
    duration: int = fields.IntField()
    title: str = fields.CharField(max_length=128)
    bookmarks: fields.ReverseRelation["Bookmark"]
    movie: fields.ForeignKeyRelation[Movie] = fields.ForeignKeyField(
        "models.Movie", related_name="episodes"
    )

    class Meta:
        table = "episodes"


class Bookmark(Model):
    id: int = fields.IntField(pk=True)
    chat_id: int = fields.BigIntField()
    timecode: int = fields.IntField()
    name: str | None = fields.CharField(max_length=32, null=True, default=None)
    movie: fields.ForeignKeyRelation[Movie] = fields.ForeignKeyField(
        "models.Movie", related_name="bookmarks"
    )
    episode: fields.ForeignKeyRelation[Episode] = fields.ForeignKeyField(
        "models.Episode", related_name="bookmarks"
    )

    class Meta:
        table = "bookmarks"
