FROM python:3.9

WORKDIR /usr/src/app/

RUN apt update
RUN apt install ffmpeg curl

# Cringe starts here
RUN curl -sL https://deb.nodesource.com/setup_18.x -o /tmp/nodesource_setup.sh
RUN bash /tmp/nodesource_setup.sh
RUN apt install nodejs
# Cringe ends here

RUN pip install poetry

ADD poetry.lock /usr/src/app/
ADD pyproject.toml /usr/src/app/
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-dev

ADD cinema/ /usr/src/app/cinema

CMD ["python", "-m", "cinema"]
