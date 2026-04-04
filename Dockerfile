FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

RUN echo "0 * * * * kill -HUP 1 > /proc/1/fd/1 2>&1" | crontab -

EXPOSE 5000

CMD cron && gunicorn -b 0.0.0.0:5000 app:app
