FROM python:3.10

WORKDIR /usr/src/app/

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install --no-install-recommends -y ffmpeg curl

# Cringe starts here
RUN curl -sL https://deb.nodesource.com/setup_18.x -o /tmp/nodesource_setup.sh
RUN bash /tmp/nodesource_setup.sh
RUN apt-get install --no-install-recommends -y nodejs
RUN rm -rf /var/lib/apt/lists/*
# Cringe ends here

RUN curl -L https://yt-dl.org/latest/youtube-dl -o /usr/bin/youtube-dl
RUN chmod 755 /usr/bin/youtube-dl

RUN pip install poetry

ADD poetry.lock /usr/src/app/
ADD pyproject.toml /usr/src/app/
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-dev

ADD cinema/ /usr/src/app/cinema

CMD ["python", "-m", "cinema"]
