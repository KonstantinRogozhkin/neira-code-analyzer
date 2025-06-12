# Быстрый старт

## Что такое neira-code-analyzer

neira-code-analyzer - это MCP сервер для продвинутого анализа кодовых баз. Он предоставляет мощные инструменты для генерации структурированного контекста, оптимизированного для анализа большими языковыми моделями (LLM).

## Основные возможности

- **🔍 Анализ фильтров**: Интеллектуальная оптимизация паттернов включения/исключения файлов
- **📄 Генерация контекста**: Создание структурированных промптов с профессиональными шаблонами
- **📊 Подсчет токенов**: Точный анализ использования токенов для оптимизации под разные LLM
- **🎯 Умные фильтры**: Автоматическое исключение build-артефактов и системных файлов
- **📋 Готовые шаблоны**: 7 профессиональных шаблонов для различных задач анализа

## Основные инструменты MCP

### 1. 🔍 analyze_filters - Анализ и оптимизация фильтров

Этот инструмент поможет вам создать оптимальные фильтры для анализа кода:

**Базовое использование:**
```json
{
  "path": "/Users/username/Projects/my-project"
}
```

**Python проект с оптимизацией:**
```json
{
  "path": "/Users/username/Projects/python-app",
  "include_patterns": ["*.py", "*.md", "requirements*.txt"],
  "exclude_patterns": ["tests/**", "__pycache__/**", "*.pyc", "venv/**", ".pytest_cache/**"]
}
```

**Веб-приложение (Python + JS):**
```json
{
  "path": "/Users/username/Projects/webapp",
  "include_patterns": ["*.py", "*.js", "*.html", "*.css", "*.md"],
  "exclude_patterns": ["node_modules/**", "dist/**", "build/**", "*.min.js", "*.min.css", "__pycache__/**"]
}
```

### 2. 📄 get_context - Генерация контекста для анализа

После анализа фильтров используйте оптимизированные настройки:

**Code Review:**
```json
{
  "path": "/Users/username/Projects/my-project",
  "template_name": "code-review",
  "include_patterns": ["src/**/*.py", "*.py", "*.md"],
  "exclude_patterns": ["tests/**", "__pycache__/**", ".git/**"],
  "line_numbers": true
}
```

**Аудит безопасности:**
```json
{
  "path": "/Users/username/Projects/webapp",
  "template_name": "security-audit",
  "include_patterns": ["*.py", "*.js", "*.html", "*.sql"],
  "exclude_patterns": ["node_modules/**", "tests/**", "*.min.js", "__pycache__/**"]
}
```

**Генерация документации:**
```json
{
  "path": "/Users/username/Projects/my-project",
  "template_name": "documentation",
  "include_patterns": ["*.py", "*.md", "README*", "pyproject.toml"],
  "exclude_patterns": ["tests/**", "__pycache__/**", ".git/**", "dist/**"]
}
```

### 3. 📋 get_templates - Просмотр доступных шаблонов

```json
{}
```

## Рабочий процесс

### Шаг 1: Анализ структуры проекта
Начните с анализа фильтров для понимания структуры и оптимизации:

```json
{
  "path": "/Users/username/Projects/my-project",
  "show_top_files": 20
}
```

### Шаг 2: Оптимизация фильтров
Используйте рекомендации из analyze_filters для настройки паттернов:

```json
{
  "path": "/Users/username/Projects/my-project",
  "include_patterns": ["src/**/*.py", "*.md", "pyproject.toml"],
  "exclude_patterns": ["tests/**", "__pycache__/**", "dist/**", ".git/**"],
  "min_file_size": 50
}
```

### Шаг 3: Генерация контекста
Примените оптимизированные фильтры для получения контекста:

```json
{
  "path": "/Users/username/Projects/my-project",
  "template_name": "code-review",
  "include_patterns": ["src/**/*.py", "*.md", "pyproject.toml"],
  "exclude_patterns": ["tests/**", "__pycache__/**", "dist/**", ".git/**"]
}
```

## Доступные шаблоны анализа

- **code-review** - Структурированный код-ревью с проверкой качества
- **security-audit** - Аудит безопасности с анализом уязвимостей
- **documentation** - Генерация технической документации
- **refactoring** - Рекомендации по рефакторингу и улучшению архитектуры
- **migration-guide** - Планирование миграции на новые технологии
- **api-documentation** - Создание API документации
- **performance-analysis** - Анализ производительности и оптимизация

## Популярные паттерны исключений

### Python проекты:
```json
["__pycache__/**", "*.pyc", "venv/**", ".venv/**", ".pytest_cache/**", "tests/**", "*.egg-info/**"]
```

### JavaScript/Node.js:
```json
["node_modules/**", "dist/**", "build/**", "*.min.js", "*.min.css", "*.map", ".webpack/**"]
```

### Общие исключения:
```json
[".git/**", "*.log", "*.tmp", "*.cache", "*.lock", "coverage/**", "test-results/**"]
```

## Советы по оптимизации

1. **Начинайте с analyze_filters** - всегда анализируйте структуру проекта перед генерацией контекста
2. **Используйте min_file_size** - исключайте файлы меньше 50-100 байт для уменьшения шума
3. **Предпочитайте include_patterns** - для больших проектов эффективнее указывать что включить
4. **Исключайте build-артефакты** - всегда исключайте dist, build, node_modules, __pycache__
5. **Проверяйте топ файлы** - используйте show_top_files для выявления больших файлов

## Примеры для разных типов проектов

### Микросервис (Python):
```json
{
  "path": "/path/to/microservice",
  "template_name": "code-review",
  "include_patterns": ["*.py", "requirements*.txt", "Dockerfile", "*.yml", "*.yaml"],
  "exclude_patterns": ["tests/**", "__pycache__/**", ".pytest_cache/**", "*.pyc"]
}
```

### API сервис:
```json
{
  "path": "/path/to/api",
  "template_name": "api-documentation", 
  "include_patterns": ["*.py", "*.yaml", "*.yml", "*.md", "requirements*.txt"],
  "exclude_patterns": ["tests/**", "__pycache__/**", "migrations/**", "*.log"]
}
```

### Фронтенд (React):
```json
{
  "path": "/path/to/frontend",
  "template_name": "security-audit",
  "include_patterns": ["src/**/*.js", "src/**/*.jsx", "src/**/*.ts", "src/**/*.tsx", "*.json"],
  "exclude_patterns": ["node_modules/**", "build/**", "dist/**", "public/**", "*.min.js"]
}
``` 