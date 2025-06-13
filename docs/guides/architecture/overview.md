# 🏗️ Архитектурный обзор neira-code-analyzer

## 📋 Принципы архитектуры

### 🎯 Основные принципы
- **Простота** - отказ от сложных DI-паттернов в пользу прямого создания зависимостей
- **Модульность** - разделение ответственности по принципу SRP (Single Responsibility Principle)
- **Безопасность** - использование типизированных контрактов и безопасной обработки путей
- **Производительность** - оптимизированные фильтры и ленивая инициализация

## 🏢 Структура модулей

### 📡 MCP Server Layer
- `main.py` - точка входа MCP сервера
- `mcp_schemas.py` - схемы валидации инструментов

### 🧠 Core Services
- `ai_analyzer.py` - AI анализ кода с Google Gemini
- `context_generator.py` - генерация контекста для анализа
- `project_manager.py` - анализ структуры проектов

### 🔧 Utility Services  
- `filter_setup_service.py` - настройка фильтров проектов
- `docs_generator.py` - автоматическая генерация документации
- `filters.py` - система фильтрации файлов

### 📚 Support Components
- `template_manager.py` - управление шаблонами анализа
- `preset_manager.py` - управление пресетами фильтров

## 🔄 Эволюция архитектуры

### ❌ Устаревшая архитектура с DI
```python
# Проблемы старой архитектуры:
# - Циклические зависимости
# - Сложность отладки
# - Избыточная абстракция
container.register_factory("service", create_service)
service = container.get("service")
```

### ✅ Текущая упрощенная архитектура
```python
# Преимущества новой архитектуры:
# - Прозрачность зависимостей  
# - Простота тестирования
# - Легкость понимания
def get_context_generator():
    return ContextGenerator()
```

## 🎨 Паттерны проектирования

### 🏭 Factory Pattern
Создание менеджеров через фабричные функции:
```python
def get_template_manager() -> TemplateManager:
    return TemplateManager()

def get_preset_manager() -> FilterPresetManager:
    return FilterPresetManager()
```

### 🎭 Command Pattern  
Структурированные действия в DocsGenerator:
```python
@dataclass
class ActionResult:
    action: str
    success: bool
    path: str
    details: str
```

### 🛡️ Strategy Pattern
Различные шаблоны анализа через enum:
```python
class AnalysisTemplate(str, Enum):
    CODE_REVIEW = "code-review"
    SECURITY_AUDIT = "security-audit"
    DOCUMENTATION = "documentation"
```

## 🔗 Интеграции и API

### 🤖 Google AI Integration
- **API:** Google Generative AI (Gemini)
- **Модели:** gemini-2.5-pro-preview-06-05, gemini-2.0-flash
- **Аутентификация:** GOOGLE_API_KEY, GEMINI_API_KEY

### 📡 MCP Protocol
- **Стандарт:** Model Context Protocol
- **Transport:** stdio
- **Схемы:** JSON Schema валидация

## 📊 Производительность

### 🚀 Оптимизации фильтров
```python
# Современные фреймворки исключаются автоматически:
DEFAULT_EXCLUDES = [
    "/.pnpm-store/", ".pnpm-store/**",    # pnpm
    "/.turbo/", ".turbo/**",              # Turbo
    "/.svelte-kit/", ".svelte-kit/**",    # SvelteKit
    "/.astro/", ".astro/**",              # Astro
]
```

### 💡 Ленивая инициализация
Зависимости создаются только при первом обращении.

## 🧪 Тестируемость

### ✅ Изолированные компоненты
Каждый модуль тестируется независимо благодаря простой архитектуре.

### 🎯 Моковые зависимости
Легкое создание моков благодаря прямым зависимостям.

## 🔮 Направления развития

- **Расширение поддержки языков** - специализированные фильтры
- **Кэширование результатов** - ускорение повторных анализов  
- **Батч-обработка** - анализ множественных проектов
- **Plugin-система** - модульная архитектура готова к расширениям

## 📚 Дополнительные ресурсы

- [Гайд по фильтрам](../features/filtering.md)
- [Настройка окружения](../setup/installation.md)
- [Операционные процедуры](../ops/maintenance.md) 