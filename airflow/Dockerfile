FROM apache/airflow:2.10.3-python3.12

USER root
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    procps \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER airflow

RUN pip install --no-cache-dir \
    arxiv==2.1.0 \
    pymupdf==1.24.0 \
    pdfplumber==0.11.0 \
    httpx==0.27.0 \
    tenacity==8.3.0
