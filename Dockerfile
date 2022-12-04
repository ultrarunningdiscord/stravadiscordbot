FROM 3.11-slim-buster

WORKDIR /app

RUN apt-get update -y

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "stravadiscordbot.py"]
