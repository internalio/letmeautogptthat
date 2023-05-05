# syntax=docker/dockerfile:1
FROM python:3.11.3-bullseye

WORKDIR /app
COPY main.py main.py
COPY requirements.txt requirements.txt
COPY src src
RUN mkdir workarea
RUN pip install -r requirements.txt

ENTRYPOINT [ "python",  "main.py"]