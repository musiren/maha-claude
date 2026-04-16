FROM python:3.11-slim AS base

WORKDIR /app

# Install dependencies in a separate layer for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY auth.py models.py session.py main.py ./

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]
