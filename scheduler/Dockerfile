FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt requirements.txt
RUN apt-get update && apt-get -y install libpq-dev gcc postgresql-client && apt-get clean
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
