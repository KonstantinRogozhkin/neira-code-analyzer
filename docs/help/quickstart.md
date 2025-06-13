# 🚀 Быстрое использование neira-code-analyzer

> **📖 Полная документация:** См. [docs/help/quickstart.md](help/quickstart.md) для детальных инструкций и примеров.

## ⚡ Основные команды

### 🎯 Быстрый старт (2 команды)

1. **Настройка фильтров:**
```json
{"path": "/path/to/project"}
```

2. **AI анализ кода:**
```json
{"path": "/path/to/project", "template_name": "code-review"}
```

### 📋 Полный список инструментов

| Инструмент | Описание | Пример |
|------------|----------|---------|
| `set_filters` | 🔧 Автоматическая настройка фильтров | `{"path": "."}` |
| `get_analyze` | ⭐ Полный AI анализ кода | `{"path": ".", "template_name": "code-review"}` |
| `get_context` | 📄 Генерация контекста | `{"path": ".", "template_name": "documentation"}` |
| `get_templates` | 📋 Список шаблонов | `{}` |

### 🎨 Доступные шаблоны

- `code-review` - Код-ревью
- `security-audit` - Аудит безопасности  
- `documentation` - Документация
- `refactoring` - Рефакторинг
- `performance-analysis` - Анализ производительности

**💡 Совет:** Начните с `set_filters`, затем используйте `get_analyze` для полного анализа.

**📖 Больше примеров и деталей:** [docs/help/quickstart.md](help/quickstart.md) 