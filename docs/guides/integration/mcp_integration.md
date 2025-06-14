# Интеграция MCP - neira-code-analyzer

Данное руководство описывает процесс интеграции `neira-code-analyzer` с различными MCP-клиентами.

## 🎯 Обзор Model Context Protocol (MCP)

`neira-code-analyzer` реализует **Model Context Protocol (MCP)** - стандарт для взаимодействия между ИИ-моделями и внешними инструментами.

### Преимущества MCP

- **Стандартизация**: Универсальный протокол для всех MCP-клиентов
- **Безопасность**: Контролируемое выполнение операций
- **Расширяемость**: Легкое добавление новых инструментов
- **Переносимость**: Работа с различными ИИ-платформами

---

## 🔧 Поддерживаемые MCP-клиенты

### 1. Claude Desktop (Anthropic)

**Конфигурация** (`~/.claude_desktop/claude_desktop_config.json`):

```json
{
  "servers": {
    "neira-code-analyzer": {
      "command": "uv",
      "args": [
        "run", 
        "python", 
        "-m", 
        "src.neira_code_analyzer.main"
      ],
      "cwd": "/path/to/neira-code-analyzer",
      "env": {
        "GOOGLE_AI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**Запуск**:
1. Убедитесь что `uv` установлен
2. Перезапустите Claude Desktop
3. Сервер будет автоматически доступен в чате

---

### 2. Cline (VS Code Extension)

**Конфигурация** (в настройках VS Code):

```json
{
  "cline.mcp.servers": {
    "neira-code-analyzer": {
      "command": "uv",
      "args": [
        "run", 
        "python", 
        "-m", 
        "src.neira_code_analyzer.main"
      ],
      "cwd": "/path/to/neira-code-analyzer",
      "env": {
        "GOOGLE_AI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**Использование**:
1. Откройте VS Code
2. Активируйте Cline
3. Инструменты neira-code-analyzer будут доступны в контекстном меню

---

### 3. MCP Inspector (Отладка)

**Для тестирования и отладки**:

```bash
# Установка MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Запуск с neira-code-analyzer
npx @modelcontextprotocol/inspector \
  uv run python -m src.neira_code_analyzer.main
```

**Возможности**:
- Интерактивное тестирование всех инструментов
- Просмотр схем и параметров
- Отладка JSON-запросов и ответов

---

### 4. Кастомные клиенты

**Базовая структура для собственного клиента**:

```python
import asyncio
from mcp import Server, create_server_session

async def main():
    # Подключение к серверу
    server = Server()
    
    # Запуск neira-code-analyzer
    process = await asyncio.create_subprocess_exec(
        "uv", "run", "python", "-m", "src.neira_code_analyzer.main",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd="/path/to/neira-code-analyzer"
    )
    
    # Создание сессии
    session = await create_server_session(process.stdin, process.stdout)
    
    # Использование инструментов
    result = await session.call_tool(
        "get_analyze",
        {
            "path": "/path/to/project",
            "template_name": "code-review"
        }
    )
    
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🛠️ Настройка окружения

### Переменные окружения

| Переменная | Описание | Обязательная |
|------------|----------|--------------|
| `GOOGLE_AI_API_KEY` | API ключ Google AI | ✅ |
| `NEIRA_DEBUG` | Включить отладочное логирование | ❌ |
| `NEIRA_LOG_LEVEL` | Уровень логирования (INFO, DEBUG, ERROR) | ❌ |
| `NEIRA_TEMP_DIR` | Папка для временных файлов | ❌ |

### Получение Google AI API ключа

1. Перейдите на [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Создайте новый API ключ
3. Добавьте ключ в переменные окружения:

```bash
export GOOGLE_AI_API_KEY="your-api-key-here"
```

**Для Windows**:
```cmd
set GOOGLE_AI_API_KEY=your-api-key-here
```

---

## 🔍 Проверка интеграции

### Базовая проверка

```bash
# Проверка установки зависимостей
uv sync

# Проверка запуска сервера
uv run python -m src.neira_code_analyzer.main --help

# Тест с MCP Inspector
npx @modelcontextprotocol/inspector \
  uv run python -m src.neira_code_analyzer.main
```

### Проверка инструментов

В MCP Inspector выполните:

```json
{
  "method": "tools/call",
  "params": {
    "name": "get_templates",
    "arguments": {}
  }
}
```

**Ожидаемый результат**: Список доступных шаблонов анализа.

---

## 🚨 Решение проблем

### Проблема: Сервер не запускается

**Симптомы**: 
- Ошибка "command not found"
- Сервер недоступен в MCP-клиенте

**Решение**:
1. Проверьте установку `uv`: `uv --version`
2. Убедитесь что путь к проекту правильный
3. Проверьте права доступа к файлам

```bash
# Проверка установки
which uv
uv --version

# Проверка проекта
cd /path/to/neira-code-analyzer
uv sync
uv run python -m src.neira_code_analyzer.main --version
```

---

### Проблема: Отсутствует API ключ

**Симптомы**:
- Ошибка "API key not found"
- Инструменты работают, но анализ падает

**Решение**:
1. Установите переменную окружения `GOOGLE_AI_API_KEY`
2. Перезапустите MCP-клиент

```bash
# Проверка переменной
echo $GOOGLE_AI_API_KEY

# Установка (Linux/macOS)
export GOOGLE_AI_API_KEY="your-key"

# Установка (Windows)
set GOOGLE_AI_API_KEY=your-key
```

---

### Проблема: Превышение лимитов токенов

**Симптомы**:
- Ошибка "Token limit exceeded"
- Медленная работа анализа

**Решение**:
1. Используйте более агрессивные фильтры
2. Уменьшите `max_tokens`
3. Примените подходящий пресет

```json
{
  "path": "/path/to/project",
  "preset_name": "aggressive",
  "max_tokens": 500000
}
```

---

## 📊 Мониторинг и логирование

### Включение подробного логирования

```bash
# Установка переменной окружения
export NEIRA_DEBUG=1
export NEIRA_LOG_LEVEL=DEBUG

# Запуск с логированием
uv run python -m src.neira_code_analyzer.main 2>&1 | tee neira.log
```

### Анализ логов

```bash
# Просмотр последних ошибок
grep -i error neira.log | tail -10

# Анализ производительности
grep -i "processing time" neira.log

# Статистика по токенам
grep -i "tokens" neira.log
```

---

## 🔧 Продвинутая настройка

### Кастомные конфигурации для разных проектов

**Для Python проектов**:
```json
{
  "servers": {
    "neira-python": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.neira_code_analyzer.main"],
      "cwd": "/path/to/neira-code-analyzer",
      "env": {
        "GOOGLE_AI_API_KEY": "your-key",
        "NEIRA_DEFAULT_PRESET": "python-project"
      }
    }
  }
}
```

**Для веб-приложений**:
```json
{
  "servers": {
    "neira-web": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.neira_code_analyzer.main"],
      "cwd": "/path/to/neira-code-analyzer",
      "env": {
        "GOOGLE_AI_API_KEY": "your-key",
        "NEIRA_DEFAULT_PRESET": "web-app"
      }
    }
  }
}
```

### Автоматизация через CI/CD

**GitHub Actions пример**:
```yaml
name: Code Analysis
on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install uv
        run: pip install uv
        
      - name: Clone neira-code-analyzer
        run: |
          git clone https://github.com/odancona/neira-code-analyzer.git
          cd neira-code-analyzer
          uv sync
          
      - name: Run analysis
        env:
          GOOGLE_AI_API_KEY: ${{ secrets.GOOGLE_AI_API_KEY }}
        run: |
          cd neira-code-analyzer
          uv run python -c "
          import json
          from src.neira_code_analyzer.main import main
          
          # Анализ текущего проекта
          result = main({
            'path': '../',
            'template_name': 'code-review',
            'preset_name': 'default'
          })
          
          with open('../analysis_result.json', 'w') as f:
            json.dump(result, f, indent=2)
          "
          
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: analysis-results
          path: analysis_result.json
```

---

*Последнее обновление: 2024-12-14* 