# 🔧 Фильтры для анализа кода

Этот файл описывает централизованную систему фильтров в `src/neira_code_analyzer/filters.py`.

## 📋 Доступные наборы фильтров

### `DEFAULT_EXCLUDES` - Базовые исключения
Применяются везде для разумного анализа кода:
- 🏗️ **Сборка:** `node_modules/`, `dist/`, `build/`, `tmp-*/`, `.webpack/`
- 🧪 **Тесты:** `test/`, `tests/`, `*.test.js`, `playwright-report/`, `coverage/`
- 📁 **Системные:** `.git/`, `.DS_Store`, `*.log`, `*.cache`, `uv.lock`
- 🖼️ **Медиа:** `*.png`, `*.jpg`, `*.mp3`, `*.mp4`, `*.ico`
- 📦 **Бинарные:** `*.exe`, `*.dll`, `*.db`, `*.sqlite`

### `AGGRESSIVE_EXCLUDES` - Для экономии токенов
Включает `DEFAULT_EXCLUDES` плюс:
- 📖 **Документация:** `*.md`, `docs/`, `README*`, `CHANGELOG*`
- ⚙️ **Конфигурация:** `*.json`, `*.yaml`, `*.yml`, `scripts/`
- 🎨 **Стили:** `*.css`, `*.scss`, `*.html`, `assets/`, `public/`

### `CODE_ONLY_INCLUDES` - Только исходный код
Паттерны для включения только файлов кода:
```
*.py, *.js, *.ts, *.tsx, *.jsx, *.java, *.cpp, *.c, *.h, *.go, *.rs, *.php
```

## 🛠️ Функции

```python
from src.neira_code_analyzer.filters import (
    get_default_excludes,
    get_aggressive_excludes, 
    get_code_only_patterns
)

# Базовые исключения
excludes = get_default_excludes()

# Агрессивные исключения для экономии токенов
excludes = get_aggressive_excludes()

# Только код (возвращает (includes, excludes))
includes, excludes = get_code_only_patterns()
```

## 🎯 Рекомендации использования

- **Документация/рефакторинг:** используйте `DEFAULT_EXCLUDES`
- **Code review с лимитом токенов:** используйте `AGGRESSIVE_EXCLUDES`
- **Анализ архитектуры:** используйте `get_code_only_patterns()`
- **Безопасность:** добавьте свои паттерны к `DEFAULT_EXCLUDES`

## 💡 Принцип

**"Provide as little context as possible, but as much as necessary"**

Максимально исключить ненужные файлы, включить только необходимые для анализа. 