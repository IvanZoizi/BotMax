FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_TOOL_BIN_DIR=/usr/local/bin

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Синхронизируем зависимости
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

# Копируем исходный код
COPY . .

# Синхронизируем проект
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

FROM python:3.12-slim-bookworm

WORKDIR /app

# Создаем не-root пользователя для безопасности
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Копируем виртуальное окружение и код из builder stage
COPY --from=builder --chown=appuser:appuser /app /app


# Устанавливаем путь к Python окружению
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Переключаемся на непривилегированного пользователя
USER appuser

# Запускаем приложение
CMD ["python", "/app/bot.py"]

