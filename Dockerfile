FROM python:3.10-slim-buster

WORKDIR /app

RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev build-essential python3-setuptools

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "stravadiscordbot.py"]
