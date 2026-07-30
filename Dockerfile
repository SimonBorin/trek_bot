FROM python:3.11-slim

ARG GAME_VERSION=development

LABEL maintainer="Semen Borin <mrblooomberg@gmail.com>"
LABEL org.opencontainers.image.source="https://github.com/SimonBorin/trek_bot"
LABEL org.opencontainers.image.version="$GAME_VERSION"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV GAME_VERSION="$GAME_VERSION"

COPY ./requirements /trek/requirements
WORKDIR /trek
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements
COPY ./ /trek

CMD ["python", "trek.py"]
