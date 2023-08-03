FROM python:3.11-slim-bullseye

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1

RUN apt -y update && apt -y install ffmpeg libmagic-dev

RUN pip install "pipenv"

WORKDIR /app
COPY Pipfile ./
COPY Pipfile.lock ./
COPY main.py ./
COPY downloader/* ./downloader/
COPY cookies.txt ./

RUN pipenv install && pipenv run playwright install && pipenv run playwright install-deps

# Set this
ENTRYPOINT ["pipenv", "run", "python", "main.py"]
