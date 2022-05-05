FROM python:3.8-slim

WORKDIR /opt/text_finder

# Install Poetry and set up environment
RUN apt update && apt install -y curl
RUN export POETRY_HOME=/opt/poetry && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python - \
  && ln -s $POETRY_HOME/bin/poetry /usr/local/bin/poetry
COPY poetry.lock pyproject.toml alembic.ini ./
RUN poetry config virtualenvs.create false && poetry update && poetry install --no-root --no-dev

# Copy project files and run application
COPY ./web ./web
COPY ./alembic ./alembic
CMD alembic upgrade head && uvicorn web.main:app --host ${APP_HOST:-"0.0.0.0"} --port ${APP_PORT:-8080} --reload
