FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt requirements.txt
RUN apt-get update && apt-get -y install libpq-dev gcc
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
ENV FLASK_APP=app.py
CMD ["flask", "run", "--host=0.0.0.0"]
