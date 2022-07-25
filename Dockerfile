FROM python:3.9

WORKDIR /usr/src/app/

RUN pip install poetry

ADD poetry.lock /usr/src/app/
ADD pyproject.toml /usr/src/app/
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-dev

ADD cinema/ /usr/src/app/cinema

CMD ["python", "-m", "cinema"]
