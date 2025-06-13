# 🛠️ Установка для разработчиков

## 📋 Системные требования

- **Python:** 3.11+ (рекомендуется 3.13)
- **Менеджер пакетов:** uv или rye (рекомендуется uv)
- **Git:** для работы с gen_docs функциональностью
- **API ключ:** Google AI Studio

## ⚡ Быстрая установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/odancona/neira-code-analyzer.git
cd neira-code-analyzer
```

### 2. Установка зависимостей
```bash
# С помощью uv (рекомендуется)
uv sync

# Или с помощью rye
rye sync
```

### 3. Настройка переменных окружения
```bash
# Добавьте в .env или экспортируйте
export GOOGLE_API_KEY="your-api-key-here"
# или
export GEMINI_API_KEY="your-api-key-here"
```

### 4. Тестирование установки
```bash
# Запуск отладочного сервера
uv run python -m src.neira_code_analyzer.main

# Проверка с MCP Inspector
npx @modelcontextprotocol/inspector uv run python -m src.neira_code_analyzer.main
```

## 🔧 Конфигурация MCP клиента

### Claude Desktop
Добавьте в `~/.config/claude/claude_desktop_config.json`:
```json
{
  "servers": {
    "neira-code-analyzer": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.neira_code_analyzer.main"],
      "cwd": "/path/to/neira-code-analyzer"
    }
  }
}
```

### Cursor/VS Code
Используйте MCP расширения для интеграции с редактором.

## 🐳 Docker установка

```bash
# Сборка образа
docker build -t neira-code-analyzer .

# Запуск контейнера
docker run -e GOOGLE_API_KEY="your-key" neira-code-analyzer
```

## ✅ Проверка установки

После установки должны быть доступны инструменты:
- `get_analyze` - AI анализ кода
- `get_context` - генерация контекста  
- `set_filters` - настройка фильтров
- `gen_docs` - генерация документации
- `get_templates` - просмотр шаблонов
- `analyze_filters` - анализ фильтров

## 🔍 Отладка проблем

### Проблемы с импортами
```bash
# Проверка структуры проекта
uv run python scripts/debug_imports.py
```

### Проблемы с API ключами
```bash
# Проверка переменных окружения
echo $GOOGLE_API_KEY
echo $GEMINI_API_KEY
```

### Проблемы с MCP
- Убедитесь, что путь к проекту корректный
- Проверьте права доступа к файлам
- Используйте MCP Inspector для диагностики

## 📚 Следующие шаги

1. [Быстрый старт](../../help/quickstart.md) - базовое использование
2. [Архитектурный обзор](../architecture/overview.md) - понимание структуры
3. [Настройка фильтров](../features/filtering.md) - оптимизация работы 