# syntax=docker/dockerfile:1

FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        ffmpeg \
        git \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Node for the frontend/ dashboard shell (Vite/React/TS).
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definitions first.
# Docker can cache this layer until requirements change.
COPY requirements.in requirements.lock /tmp/

RUN python -m pip install \
    --no-cache-dir \
    -r /tmp/requirements.lock

# Persist a wheelhouse of every direct dependency so `lando lock` can
# re-resolve with --no-index --find-links after adding a new package,
# without needing network access inside the running container.
RUN python -m pip download \
    -r /tmp/requirements.in \
    -d /wheelhouse

CMD ["sleep", "infinity"]