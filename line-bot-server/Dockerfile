FROM python:3.11-slim
WORKDIR /app
COPY line-bot-server/requirements.txt requirements.txt
RUN apt-get update && apt-get -y install libpq-dev gcc && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt
COPY line-bot-server/ .
COPY utils ./utils
COPY const ./const
EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
