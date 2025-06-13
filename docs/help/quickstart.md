# Быстрый старт

## Что такое neira-code-analyzer

neira-code-analyzer - это MCP сервер для продвинутого анализа кодовых баз. Он предоставляет мощные инструменты для генерации структурированного контекста, оптимизированного для анализа большими языковыми моделями (LLM).

## Основные возможности

- **🤖 Автоматический AI анализ**: Полный анализ кода с Neira AI (флагманская функция)
- **🎯 Автонастройка фильтров**: Автоопределение типа проекта и применение оптимальных пресетов
- **📄 Генерация контекста**: Создание структурированных промптов с профессиональными шаблонами
- **📊 Подсчет токенов**: Точный анализ использования токенов для оптимизации под разные LLM
- **📋 Готовые шаблоны**: 7 профессиональных шаблонов для различных задач анализа

## Основные инструменты MCP

### 1. 🤖 get_analyze - Автоматический AI анализ кода (⭐ Рекомендуется)

Флагманская функция для полного автоматического анализа:

**Простой анализ:**
```json
{
  "path": "/Users/username/Projects/my-project",
  "template_name": "code-review"
}
```

### 2. 🎯 set_filters - Автоматическая настройка фильтров (🔧 Начните с этого)

Автоматически определяет тип проекта и настраивает оптимальные фильтры:

**Автоматическое определение типа проекта:**
```json
{
  "path": "/Users/username/Projects/my-project"
}
```

**С указанием конкретного пресета:**
```json
{
  "path": "/Users/username/Projects/python-app",
  "preset_name": "python-project"
}
```

**Объединение пресета с дополнительными файлами:**
```json
{
  "path": "/Users/username/Projects/webapp",
  "preset_name": "web-app",
  "merge_with_preset": true,
  "include_patterns": ["*.md", "*.yml"]
}
```

### 3. 📄 get_context - Генерация контекста для анализа

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

## 🚀 Рекомендуемый рабочий процесс

### Шаг 1: Автоматическая настройка фильтров (🔧 Рекомендуется сначала)
Настройте оптимальные фильтры один раз:

```json
{
  "path": "/Users/username/Projects/my-project"
}
```

### Шаг 2: Полный AI анализ (⭐ Главная функция)
Запустите автоматический анализ кода:

```json
{
  "path": "/Users/username/Projects/my-project",
  "template_name": "code-review"
}
```

### Альтернативный подход: Ручная генерация контекста
Если нужен более точный контроль:

```json
{
  "path": "/Users/username/Projects/my-project",
  "template_name": "code-review",
  "preset_name": "python-project"
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

## 💡 Советы по эффективному использованию

1. **Начинайте с set_filters** - настройте оптимальные фильтры один раз для проекта
2. **Используйте get_analyze** - флагманская функция для полного анализа кода
3. **Применяйте пресеты** - используйте встроенные пресеты (python-project, react-app, web-app)
4. **Сохраняйте .neira в git** - для единых настроек в команде
5. **Объединяйте пресеты** - используйте merge_with_preset для добавления специфичных файлов

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