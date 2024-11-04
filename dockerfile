FROM python:3.11.0-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

CMD ["sh", "-c", "cd /app/code && python3 main.py ${BOT_TOKEN}"]