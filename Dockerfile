FROM python:slim-bookworm

RUN apt-get update && apt-get install -y gcc

RUN mkdir /bot
WORKDIR /bot

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot_async.py"]
