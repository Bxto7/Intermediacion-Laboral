FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Switch apt sources to HTTPS (HTTP port 80 may be blocked on some networks)
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    libglib2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-xlib-2.0-0 \
    libfontconfig1 \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Descargar modelo spaCy en español
RUN python -m spacy download es_core_news_md

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
