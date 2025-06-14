# ИСПРАВЛЕНО: Multi-stage build с обработкой ошибок
FROM python:slim as builder

# ИСПРАВЛЕНО: Добавлен set -e для немедленного прерывания при ошибках
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

# Устанавливаем системные зависимости только для сборки
RUN apt update && apt install -y \
    curl build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ИСПРАВЛЕНО: Устанавливаем Rust с проверкой успешности
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && echo "✅ Rust installed successfully"
ENV PATH="/root/.cargo/bin:$PATH"

# ИСПРАВЛЕНО: Проверяем установку Rust
RUN rustc --version || (echo "❌ Rust installation failed" && exit 1)

# ИСПРАВЛЕНО: Устанавливаем UV с проверкой
RUN pip install uv \
    && uv --version \
    && echo "✅ UV installed successfully"

# Копируем файлы проекта
WORKDIR /app
COPY pyproject.toml requirements.lock ./

# ИСПРАВЛЕНО: Устанавливаем зависимости с проверкой успешности
RUN uv venv \
    && echo "✅ Virtual environment created" \
    && uv pip install --no-cache -r requirements.lock \
    && echo "✅ Dependencies installed successfully"

# Финальная стадия - минимальный runtime образ
FROM python:slim

# ИСПРАВЛЕНО: Добавлен set -e и для runtime стадии
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

# ИСПРАВЛЕНО: Создаем пользователя с проверкой
RUN groupadd -r appuser \
    && useradd -r -g appuser appuser \
    && echo "✅ User appuser created successfully"

WORKDIR /app

# ИСПРАВЛЕНО: Копируем с проверкой существования файлов
COPY --from=builder /app/.venv /app/.venv
RUN test -d /app/.venv || (echo "❌ Virtual environment not found" && exit 1)

COPY --chown=appuser:appuser . .
RUN test -f pyproject.toml || (echo "❌ Project files not found" && exit 1)

# Активируем виртуальное окружение
ENV PATH="/app/.venv/bin:$PATH"

# ИСПРАВЛЕНО: Проверяем виртуальное окружение
RUN python --version \
    && echo "✅ Python environment ready"

# Переключаемся на непривилегированного пользователя
USER appuser

# ИСПРАВЛЕНО: Устанавливаем пакет с проверкой
RUN pip install --no-deps -e . \
    && python -c "import neira_code_analyzer; print('✅ Package installed successfully')" \
    || (echo "❌ Package installation failed" && exit 1)

# ИСПРАВЛЕНО: Healthcheck для проверки работоспособности
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import neira_code_analyzer" || exit 1

CMD ["python", "-m", "neira_code_analyzer.main"]
