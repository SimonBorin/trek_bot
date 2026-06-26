FROM python:3.11-slim

LABEL maintainer="Semen Borin <mrblooomberg@gmail.com>"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /trek

COPY requirements /trek/requirements
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements

COPY . /trek

CMD ["python", "trek.py"]
