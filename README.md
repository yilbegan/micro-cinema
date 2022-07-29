<p align="center">
  <a href="https://github.com/yilbegan/micro-cinema">
    <img src="https://raw.githubusercontent.com/yilbegan/micro-cinema/main/images/logo.png" style="image-rendering: pixelated; image-rendering: crisp-edges;" alt="Micro Cinema">
  </a>
</p>
<h1 align="center">
  Cinema in your telegram voice chat
</h1>
<p align="center">
  <img alt="Code Quality" src="https://img.shields.io/codefactor/grade/github/yilbegan/micro-cinema">
  <img alt="Github top language" src="https://img.shields.io/github/languages/top/yilbegan/micro-cinema?style=flat-square">
  <img alt="Code Style" src="https://img.shields.io/badge/code%20style-black-black?style=flat-square">
</p>

## Prerequisites

- Python 3.10
- ffmpeg
- youtube-dl (if you want youtube support)

## Setup

Clone the repo and setup environment:

```
$ git clone https://github.com/yilbegan/micro-cinema.git && cd micro-cinema
$ python3.10 -m venv ./venv
$ source ./venv/bin/activate
$ pip install poetry
$ poetry install
```

Get your api_id and api_hash [here](https://my.telegram.org/apps) and log in to the account where you want to launch the bot:

```
# You can skip this step and use your pyrogram session+json if you have one.
# Just put them into ./account and rename to cinema.session and metadata.cinema.json
$ python -m cinema.login
```

Create config and edit it in any text editor:

```
$ cp config.yaml.example config.yaml
```

Now you can launch your cinema:

```
$ python -m cinema
```

## Commands


Command                           | Permission | Description
:-------------------------------: | :--------: | :---------------------------:
`/movies`                         | Anyone     | List all available movies.
`/movies inspect {movie_id}`      | Anyone     | Show detaled info about movie.
`/bookmarks`                      | Anyone     | Show bookmarks in this chat
`/movies update`                  | Admin      | Update movies from config
`/cache {movie_id} {episode}`     | Admin      | Download episode to improve playback quality
`/play {movie_id} {episode}`      | Moderator  | Play the movie. Episode defaults to first.
`/play bookmark {bookmark_id}`    | Moderator  | Start from the bookmark.
`/join {chat}`                    | Moderator  | Join chat. Supported `t.me/*` and `@chat_name`.
`/stop`                           | Moderator  | Stop current movie.
`/stop save`                      | Moderator  | Stop and create bookmark.
