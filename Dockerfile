FROM python:3.12-slim-bookworm

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1

RUN apt -y update && apt -y install libmagic-dev wget

# Get latest ffmpeg
RUN apt -y update -oAcquire::AllowInsecureRepositories=true && \
    wget https://www.deb-multimedia.org/pool/main/d/deb-multimedia-keyring/deb-multimedia-keyring_2016.8.1_all.deb && \
    dpkg -i deb-multimedia-keyring_2016.8.1_all.deb && \
    rm deb-multimedia-keyring_2016.8.1_all.deb && \
    echo "deb https://www.deb-multimedia.org bookworm main non-free" >> /etc/apt/sources.list && \
    apt -y update && apt -y upgrade && \
    apt -y install ffmpeg gcc git && \
    apt -y remove wget && \
    apt -y autoremove && apt -y clean

RUN pip install "pipenv"

WORKDIR /app
COPY Pipfile ./
COPY Pipfile.lock ./
COPY *.py ./
COPY downloader/ ./downloader/
COPY models/ ./models/
COPY bots/ ./bots/

RUN pipenv install && pipenv run playwright install chromium && pipenv run playwright install-deps && \
    apt -y remove gcc git

# Set this
ENTRYPOINT ["pipenv", "run", "python", "main.py"]
