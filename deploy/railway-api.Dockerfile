# Himma API — Railway release image
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY services/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app

WORKDIR /app/services/api

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
