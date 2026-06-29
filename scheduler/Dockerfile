FROM python:3.11-slim
WORKDIR /app
COPY scheduler/requirements.txt requirements.txt
RUN apt-get update && apt-get -y install libpq-dev gcc postgresql-client && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt
COPY scheduler/ .
COPY utils ./utils
COPY const ./const
CMD ["python", "main.py"]
