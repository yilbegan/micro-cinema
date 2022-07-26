def format_time(time: int) -> str:
    seconds = time % 60
    minutes = (time // 60) % 60
    hours = time // 60 // 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
