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
    apt -y install ffmpeg && \
    apt -y remove wget && \
    apt -y autoremove && apt -y clean

RUN pip install uv

WORKDIR /app
COPY pyproject.toml ./
COPY uv.lock ./
COPY *.py ./
COPY bot/ ./bot/
COPY conf/ ./conf/
COPY examples/settings_prod.py ./settings.py

RUN uv install && uv run playwright install chromium && uv run playwright install-deps

ENTRYPOINT ["uv", "run", "python", "manage.py"]
