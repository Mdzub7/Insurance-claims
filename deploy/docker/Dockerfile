FROM python:3.11-slim

WORKDIR /app
COPY ./deploy/docker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

ENV PORT=8001

COPY frontend frontend
COPY backend backend
COPY deploy/entrypoint.sh /app/entrypoint.sh
RUN chmod 777 /app/entrypoint.sh

EXPOSE 8000 8001
ENTRYPOINT ["/app/entrypoint.sh"]
