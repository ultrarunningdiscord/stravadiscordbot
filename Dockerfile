# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app

RUN apt-get -y install redis-server
CMD ["redis-server", "/etc/redis/redis.conf"]

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "stravadiscordbot.py"]
