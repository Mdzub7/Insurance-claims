FROM python:3.9-slim

WORKDIR /app

# Copy all files
COPY . /app

# Expose port 8000 (standard for Python simple server)
EXPOSE 8000

# Run a simple HTTP server on port 8000
CMD ["python3", "-m", "http.server", "8000"]
