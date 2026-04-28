FROM ghcr.io/astral-sh/uv:0.11.8-debian-slim

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .

CMD ["uv", "run", "--frozen", "--no-dev", "python", "main.py"]
