# Примеры Использования - neira-code-analyzer

Данный документ содержит реальные примеры использования всех основных функций `neira-code-analyzer`.

## 🎯 Сценарии использования

### 1. Анализ кода для code review ⭐

**Сценарий**: Подготовка к code review с фокусом на безопасность и производительность.

```json
{
  "path": "/Users/developer/Projects/web-api",
  "template_name": "code-review",
  "user_query": "Проанализируй код API на предмет безопасности, производительности и соответствия best practices. Особое внимание уделить аутентификации и обработке ошибок.",
  "ai_model": "gemini-2.5-pro-preview-06-05",
  "include_patterns": ["*.py", "*.js", "*.sql"],
  "exclude_patterns": ["tests/**", "node_modules/**", "*.log"],
  "max_tokens": 800000
}
```

**Результат**: Детальный анализ с рекомендациями по улучшению безопасности и производительности.

---

### 2. Анализ безопасности проекта 🔒

**Сценарий**: Аудит безопасности существующего проекта.

```json
{
  "path": "/Users/developer/Projects/banking-app",
  "template_name": "security-audit",
  "user_query": "Проведи полный аудит безопасности банковского приложения. Найди потенциальные уязвимости, небезопасные практики и рекомендации по улучшению.",
  "ai_model": "gemini-2.5-pro-preview-06-05",
  "preset_name": "web-app",
  "max_tokens": 1000000
}
```

**Результат**: Отчет по безопасности с классификацией угроз и планом исправлений.

---

### 3. Создание документации 📚

**Сценарий**: Автоматическая генерация документации для нового проекта.

```json
{
  "path": "/Users/developer/Projects/ml-library",
  "template_name": "documentation",
  "user_query": "Создай подробную документацию для ML библиотеки, включая API reference, примеры использования, архитектурный обзор и руководство по установке.",
  "ai_model": "gemini-2.5-pro-preview-06-05",
  "include_patterns": ["*.py", "*.md", "*.rst", "*.txt"],
  "exclude_patterns": ["__pycache__/**", "*.pyc", ".git/**"],
  "save_as_preset": "ml-library-docs"
}
```

**Результат**: Комплексная документация с API reference и примерами.

---

### 4. Рефакторинг legacy кода 🔄

**Сценарий**: Анализ и план рефакторинга старого кода.

```json
{
  "path": "/Users/developer/Projects/legacy-system",
  "template_name": "refactoring",
  "user_query": "Проанализируй legacy код и предложи план рефакторинга. Определи проблемные области, технический долг и приоритеты для модернизации.",
  "ai_model": "gemini-2.5-pro-preview-06-05",
  "preset_name": "code-only",
  "max_tokens": 1200000
}
```

**Результат**: Детальный план рефакторинга с приоритизацией задач.

---

### 5. Миграция на новую технологию 🚀

**Сценарий**: Планирование миграции с React на Vue.js.

```json
{
  "path": "/Users/developer/Projects/react-app",
  "template_name": "migration-guide",
  "user_query": "Создай план миграции React приложения на Vue.js 3. Определи ключевые компоненты, зависимости и потенциальные проблемы.",
  "ai_model": "gemini-2.5-pro-preview-06-05",
  "include_patterns": ["*.jsx", "*.js", "*.ts", "*.tsx", "*.json"],
  "exclude_patterns": ["node_modules/**", "build/**", "dist/**"]
}
```

**Результат**: Пошаговый план миграции с оценкой сложности.

---

## 🔧 Продвинутые сценарии

### 6. Интерактивный анализ с продолжением сессии

**Шаг 1**: Создание новой сессии
```json
{
  "path": "/Users/developer/Projects/e-commerce",
  "template_name": "code-review",
  "user_query": "Проанализируй архитектуру e-commerce платформы",
  "ai_model": "gemini-2.5-pro-preview-06-05",
  "preset_name": "web-app"
}
```

**Ответ**: `{"session_id": "20241214_143022", ...}`

**Шаг 2**: Продолжение анализа
```json
{
  "path": "/Users/developer/Projects/e-commerce",
  "session_id": "20241214_143022",
  "user_query": "Теперь сфокусируйся на модуле платежей и найди потенциальные проблемы безопасности"
}
```

**Шаг 3**: Глубокий анализ конкретного модуля
```json
{
  "path": "/Users/developer/Projects/e-commerce",
  "session_id": "20241214_143022",
  "user_query": "Предложи конкретные исправления для найденных уязвимостей в платежном модуле"
}
```

---

### 7. Создание и использование кастомного пресета

**Шаг 1**: Создание пресета
```json
{
  "action": "create",
  "name": "django-api",
  "description": "Пресет для Django REST API проектов",
  "include_patterns": [
    "*.py",
    "*.html",
    "*.js",
    "*.css",
    "*.json",
    "*.yaml",
    "*.yml",
    "requirements*.txt",
    "Dockerfile",
    "docker-compose.yml"
  ],
  "exclude_patterns": [
    "__pycache__/**",
    "*.pyc",
    "*.pyo",
    "migrations/**",
    "static/admin/**",
    "media/**",
    ".git/**",
    "venv/**",
    "env/**",
    "*.log",
    "db.sqlite3"
  ]
}
```

**Шаг 2**: Использование созданного пресета
```json
{
  "path": "/Users/developer/Projects/django-api",
  "template_name": "api-documentation",
  "preset_name": "django-api",
  "user_query": "Создай API документацию для Django REST API",
  "ai_model": "gemini-2.5-pro-preview-06-05"
}
```

---

### 8. Анализ производительности

**Сценарий**: Выявление узких мест в производительности.

```json
{
  "path": "/Users/developer/Projects/high-load-service",
  "template_name": "performance-analysis",
  "user_query": "Проанализируй код высоконагруженного сервиса и найди узкие места. Предложи оптимизации для увеличения производительности в 2-3 раза.",
  "ai_model": "gemini-2.5-pro-preview-06-05",
  "include_patterns": ["*.py", "*.sql", "*.json", "*.yaml"],
  "exclude_patterns": ["tests/**", "*.log", "__pycache__/**"],
  "max_tokens": 1500000
}
```

**Результат**: Детальный отчет с конкретными рекомендациями по оптимизации.

---

## 🎨 Работа с шаблонами

### 9. Создание кастомного шаблона

Хотя создание новых шаблонов не поддерживается через API, вы можете использовать параметр `template` для передачи кастомного Handlebars шаблона:

```json
{
  "path": "/Users/developer/Projects/my-project",
  "template": "# Кастомный анализ проекта {{project_name}}\n\n## Структура файлов\n{{#each files}}\n- {{this.path}} ({{this.lines}} строк)\n{{/each}}\n\n## Исходный код\n{{#each files}}\n### {{this.path}}\n```{{this.language}}\n{{this.content}}\n```\n{{/each}}",
  "user_query": "Создай краткий обзор проекта с фокусом на ключевые компоненты"
}
```

---

### 10. Генерация полной документации проекта

**Сценарий**: Создание всей документации проекта автоматически.

```json
{
  "path": "/Users/developer/Projects/open-source-lib",
  "docs_structure": "standard",
  "update_changelog": true,
  "git_scan_days": 60,
  "archive_processed": true,
  "compress_guides": false,
  "target_guide_length": 250,
  "max_file_size": 600,
  "scan_depth": 4
}
```

**Результат**: Полная структура документации с README, changelog, руководствами и архивом.

---

## 🛠️ Лучшие практики

### Оптимизация производительности

1. **Используйте соответствующие пресеты** для вашего типа проекта
2. **Ограничивайте max_tokens** в зависимости от сложности задачи
3. **Применяйте точные фильтры** для исключения ненужных файлов
4. **Используйте интерактивные сессии** для глубокого анализа

### Безопасность

1. **Всегда делайте backup** перед автоматическими исправлениями
2. **Проверяйте применяемые изменения** перед коммитом
3. **Используйте версионирование** для отслеживания изменений

### Масштабируемость

1. **Создавайте переиспользуемые пресеты** для типовых проектов
2. **Сохраняйте результаты анализа** в файлы для последующего использования
3. **Автоматизируйте генерацию документации** в CI/CD pipeline

---

*Последнее обновление: 2024-12-14* 