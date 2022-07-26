import time


class ViewStatus:
    movie_id: int
    episode: int
    progress: int = 0
    started_at: int | None = None
    paused: bool = False

    def __init__(self, movie_id: int, episode: int, progress: int | None = None):
        self.movie_id = movie_id
        self.episode = episode
        self.progress = 0 if progress is None else progress
        self.started_at = int(time.time())
        self.paused = False

    def pause(self):
        self.progress += int(time.time() - self.started_at)
        self.paused = True

    def resume(self):
        self.started_at = int(time.time())
        self.paused = False

    def get_progress(self):
        if self.paused:
            return self.progress
        return self.progress + int(time.time() - self.started_at)
