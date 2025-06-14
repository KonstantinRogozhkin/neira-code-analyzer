# API Reference - neira-code-analyzer

## Обзор MCP Tools

`neira-code-analyzer` предоставляет мощный набор инструментов через Model Context Protocol (MCP) для анализа кодовых баз.

## 🎯 Core Tools

### 1. `get_analyze` - Интерактивный AI Анализ ⭐

**Флагманский инструмент** для полного интерактивного анализа кода с использованием Google Gemini.

#### Параметры

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `path` | string | ✅ | Полный путь к проекту |
| `session_id` | string | ❌ | ID сессии для продолжения диалога. Если пустой - создается новая сессия |
| `user_query` | string | ❌ | Запрос пользователя для фокуса анализа |
| `template_name` | enum | ❌ | Шаблон анализа: `code-review`, `security-audit`, `documentation`, `refactoring`, `performance-analysis`, `migration-guide`, `api-documentation` |
| `ai_model` | enum | ❌ | Модель AI: `gemini-2.5-pro-preview-06-05`, `gemini-2.0-flash`, `gemini-1.5-pro` |
| `max_tokens` | integer | ❌ | Максимум токенов (10,000 - 2,000,000). По умолчанию: 1,000,000 |
| `include_patterns` | array | ❌ | Glob-паттерны файлов для включения |
| `exclude_patterns` | array | ❌ | Glob-паттерны файлов для исключения |
| `preset_name` | enum | ❌ | Предустановленный фильтр проекта |
| `merge_with_preset` | boolean | ❌ | Объединять ли паттерны с пресетом |
| `save_as_preset` | string | ❌ | Сохранить конфигурацию фильтров как новый пресет |

#### Пример использования

**Новая сессия:**
```json
{
  "path": "/Users/username/Projects/my-project",
  "template_name": "code-review",
  "user_query": "Проанализируй код на предмет производительности и безопасности",
  "ai_model": "gemini-2.5-pro-preview-06-05",
  "include_patterns": ["*.py", "*.js", "*.ts"],
  "exclude_patterns": ["tests/**", "node_modules/**"],
  "max_tokens": 500000
}
```

**Продолжение сессии:**
```json
{
  "path": "/Users/username/Projects/my-project",
  "session_id": "20241213_143022",
  "user_query": "Теперь сфокусируйся на модуле авторизации"
}
```

#### Возвращаемый формат

```json
{
  "session_id": "20241213_143022",
  "ai_response": "Детальный анализ кода...",
  "actions_applied": [
    {
      "type": "file_edit",
      "file": "src/auth.py",
      "description": "Исправлена уязвимость SQL-инъекции"
    }
  ],
  "file_stats": {
    "total_files": 45,
    "total_tokens": 125000,
    "included_extensions": [".py", ".js"]
  }
}
```

---

### 2. `get_context` - Генерация Контекста

Создает структурированный контекст кодовой базы для анализа ИИ.

#### Параметры

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `path` | string | ✅ | Путь к проекту |
| `template_name` | enum | ❌ | Шаблон форматирования |
| `template` | string | ❌ | Кастомный Handlebars шаблон |
| `include_patterns` | array | ❌ | Паттерны включения файлов |
| `exclude_patterns` | array | ❌ | Паттерны исключения файлов |
| `preset_name` | enum | ❌ | Предустановленный набор фильтров |
| `save_to_file` | string | ❌ | Путь для сохранения результата |
| `encoding` | enum | ❌ | Кодировка токенизатора: `cl100k`, `p50k`, `gpt2`, `o200k` |
| `line_numbers` | boolean | ❌ | Добавлять номера строк (по умолчанию: true) |
| `code_blocks` | boolean | ❌ | Обертывать код в markdown блоки (по умолчанию: true) |
| `auto_analyze` | boolean | ❌ | Автоматически запускать set_filters (по умолчанию: true) |

#### Пример

```json
{
  "path": "/Users/username/Projects/my-project",
  "template_name": "documentation",
  "include_patterns": ["*.py", "*.md"],
  "exclude_patterns": ["tests/**", "__pycache__/**"],
  "save_to_file": "analysis/project-context.md",
  "auto_analyze": true
}
```

---

### 3. `set_filters` - Автоматическая Настройка Фильтров

Анализирует проект и автоматически применяет оптимальные фильтры файлов.

#### Параметры

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `path` | string | ✅ | Путь к проекту |
| `preset_name` | enum | ❌ | Пресет фильтров или автоопределение |
| `include_patterns` | array | ❌ | Дополнительные паттерны включения |
| `exclude_patterns` | array | ❌ | Дополнительные паттерны исключения |
| `merge_with_preset` | boolean | ❌ | Объединять с пресетом (по умолчанию: false) |
| `encoding` | enum | ❌ | Кодировка для подсчета токенов |

#### Доступные пресеты

- `default` - Базовая конфигурация
- `aggressive` - Максимальное исключение файлов
- `code-only` - Только исходный код
- `python-project` - Оптимизация для Python проектов
- `web-app` - Веб-приложения (HTML, CSS, JS)
- `react-app` - React приложения
- `electron-app` - Electron приложения

#### Пример

```json
{
  "path": "/Users/username/Projects/python-api",
  "preset_name": "python-project",
  "include_patterns": ["*.md", "*.txt"],
  "merge_with_preset": true
}
```

---

### 4. `manage_presets` - Управление Пресетами

Создание, редактирование и управление пресетами фильтров.

#### Параметры

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `action` | enum | ✅ | Действие: `list`, `create`, `details`, `delete`, `export`, `import` |
| `name` | string | ❌* | Имя пресета (*обязательно для create, details, delete, export) |
| `description` | string | ❌ | Описание пресета (для create) |
| `include_patterns` | array | ❌ | Паттерны включения (для create) |
| `exclude_patterns` | array | ❌ | Паттерны исключения (для create) |
| `file_path` | string | ❌ | Путь к файлу (для export/import) |

#### Примеры

**Создание пресета:**
```json
{
  "action": "create",
  "name": "my-web-app",
  "description": "Кастомный пресет для веб-приложения",
  "include_patterns": ["*.js", "*.ts", "*.html", "*.css", "*.vue"],
  "exclude_patterns": ["node_modules/**", "dist/**", "build/**"]
}
```

**Экспорт пресета:**
```json
{
  "action": "export",
  "name": "my-web-app",
  "file_path": "/path/to/preset.json"
}
```

---

### 5. `get_templates` - Просмотр Шаблонов

Получение списка всех доступных шаблонов анализа.

#### Параметры

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `show_content` | boolean | ❌ | Показать содержимое шаблонов (по умолчанию: false) |

#### Пример

```json
{
  "show_content": false
}
```

---

## 🔧 Utility Tools

### 6. `gen_docs` - Генерация Документации

Автоматическое создание и обновление документации проекта.

#### Параметры

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `path` | string | ✅ | Путь к проекту |
| `docs_structure` | enum | ❌ | Структура документации: `standard`, `minimal` |
| `update_changelog` | boolean | ❌ | Обновлять CHANGELOG.md (по умолчанию: true) |
| `git_scan_days` | integer | ❌ | Дней для сканирования git истории (1-90, по умолчанию: 14) |
| `archive_processed` | boolean | ❌ | Архивировать обработанные файлы (по умолчанию: true) |
| `compress_guides` | boolean | ❌ | Сжимать длинные руководства (по умолчанию: true) |
| `target_guide_length` | integer | ❌ | Целевая длина руководств в строках (50-300, по умолчанию: 150) |
| `max_file_size` | integer | ❌ | Максимальный размер обрабатываемых файлов в строках (50-1000, по умолчанию: 400) |
| `scan_depth` | integer | ❌ | Глубина сканирования директорий (1-5, по умолчанию: 3) |

#### Пример

```json
{
  "path": "/Users/username/Projects/my-project",
  "docs_structure": "standard",
  "update_changelog": true,
  "git_scan_days": 30,
  "compress_guides": true,
  "target_guide_length": 200
}
```

---

## 📊 Коды Ответов

| Код | Описание |
|-----|----------|
| `✅ SUCCESS` | Операция выполнена успешно |
| `❌ ERROR` | Произошла ошибка |
| `⚠️ WARNING` | Операция выполнена с предупреждениями |
| `📊 STATS` | Статистическая информация |

---

## 🔍 Поиск и Устранение Неисправностей

### Общие проблемы

1. **Превышение лимита токенов**
   - Используйте более агрессивные фильтры
   - Уменьшите `max_tokens`
   - Примените пресет `aggressive`

2. **Ошибки сессий**
   - Проверьте корректность `session_id`
   - Удалите папку `.docs_session/` для сброса

3. **Проблемы с путями**
   - Используйте абсолютные пути
   - Избегайте символа `"."` как путь

### Логирование

Включите подробное логирование установив переменную окружения:
```bash
export NEIRA_DEBUG=1
```

---

*Последнее обновление: 2024-12-14* 