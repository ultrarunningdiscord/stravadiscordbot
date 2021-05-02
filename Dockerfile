# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app

# ARG DISCORDTOKEN
# ARG STRAVATOKEN
# ARG STRAVACLUB
# ENV DISCORDTOKEN=$DISCORDTOKENL
# ENV STRAVATOKEN=$STRAVATOKEN
# ENV STRAVACLUB=$STRAVACLUB

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "stravadiscordbot.py"]
