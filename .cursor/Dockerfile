# Multi-stage build для оптимизации размера и безопасности
FROM python:slim as builder

# Устанавливаем системные зависимости только для сборки
RUN apt update && apt install -y \
    curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Rust для сборки code2prompt-rs
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:$PATH"

# Устанавливаем UV для управления зависимостями Python
RUN pip install uv

# Копируем файлы проекта
WORKDIR /app
COPY pyproject.toml requirements.lock ./

# Устанавливаем зависимости Python в виртуальное окружение
RUN uv venv && \
    uv pip install --no-cache -r requirements.lock

# Финальная стадия - минимальный runtime образ
FROM python:slim

# Создаем непривилегированного пользователя для безопасности
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Копируем виртуальное окружение и код из builder стадии
COPY --from=builder /app/.venv /app/.venv
COPY --chown=appuser:appuser . .

# Активируем виртуальное окружение
ENV PATH="/app/.venv/bin:$PATH"

# Переключаемся на непривилегированного пользователя
USER appuser

# Устанавливаем пакет neira_code_analyzer правильным способом
RUN pip install --no-deps -e .

CMD ["python", "-m", "neira_code_analyzer.main"]
