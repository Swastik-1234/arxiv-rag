FROM python:3.12-slim

WORKDIR /app

# system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# copy dependency files first (for layer caching)
COPY pyproject.toml ./

# install dependencies
RUN uv sync --no-dev

# copy source code
COPY src/ ./src/
COPY gradio_launcher.py ./

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

EXPOSE 8000 7861

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
