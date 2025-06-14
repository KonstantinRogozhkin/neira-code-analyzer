# 🔧 Операционные процедуры

## 📋 Регулярное обслуживание

### 🔄 Обновление документации (еженедельно)
```bash
# Автоматическое обновление через gen_docs
{
  "path": "/path/to/project",
  "structure": "standard",
  "auto_update_changelog": true,
  "archive_processed": true
}
```

### 🧹 Очистка временных файлов
```bash  
# Удаление старых логов
find . -name "*.log" -mtime +7 -delete

# Очистка кэша Python
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete
```

### 📊 Мониторинг производительности
```bash
# Проверка размера токенов для проектов
uv run python -c "
from src.neira_code_analyzer.context_generator import ContextGenerator
cg = ContextGenerator()
result = cg.set_filters('/path/to/project')
print(f'Tokens: {result.stats.estimated_tokens}')
"
```

## 🔍 Диагностика проблем

### 🚨 Основные проблемы и решения

#### Высокое потребление токенов
- Используйте `set_filters` для автоматической оптимизации
- Добавьте исключения для `node_modules`, `.venv`, `build`

#### Ошибки API аутентификации  
- Проверьте `GOOGLE_API_KEY` в переменных окружения
- Убедитесь в правильности ключа через Google AI Studio

#### Проблемы с фильтрами
- Удалите `.neira` для сброса настроек
- Используйте `set_filters` для автонастройки

## 📈 Оптимизация производительности

### ⚡ Рекомендуемые настройки

#### Для веб-проектов
```json
{
  "exclude_patterns": [
    "node_modules/**", 
    "/.pnpm-store/", ".pnpm-store/**",
    "/.turbo/", ".turbo/**",
    "/dist/", "dist/**",
    "/build/", "build/**"
  ]
}
```

#### Для Python проектов  
```json
{
  "exclude_patterns": [
    "__pycache__/**",
    ".venv/**", "venv/**",
    "*.pyc", "*.pyo", "*.pyd",
    ".pytest_cache/**"
  ]
}
```

### 🎯 Целевые метрики
- **Время анализа:** < 30 сек для проектов до 500К токенов
- **Точность фильтров:** > 90% релевантных файлов  
- **Использование API:** < 100К токенов на анализ среднего проекта

## 🔐 Безопасность

### 🛡️ Проверка безопасности
```bash
# Аудит зависимостей
uv audit

# Проверка на уязвимости в путях
grep -r "os.path.join\|path.join" src/ --exclude-dir=__pycache__
```

### 🔑 Управление API ключами
- Используйте переменные окружения, не хардкодьте ключи
- Ротация ключей каждые 90 дней
- Мониторинг использования API через Google AI Studio

## 📝 Логирование и мониторинг

### 📊 Настройка логов
```python
# Логи автоматически ротируются:
# - Максимальный размер: 5MB
# - Количество бэкапов: 3
# - Уровень по умолчанию: INFO
```

### 📈 Метрики для отслеживания
- Количество анализов в день
- Средний размер токенов на анализ  
- Частота ошибок API
- Время отклика системы

## 🚀 Обновления и деплой

### 📋 Checklist обновления
1. ✅ Запуск тестов: `uv run pytest`
2. ✅ Проверка совместимости API
3. ✅ Бэкап конфигураций пресетов  
4. ✅ Обновление документации
5. ✅ Тест с MCP Inspector

### 🐳 Docker деплой
```bash
# Обновление продакшн образа
docker build -t neira-code-analyzer:latest .
docker tag neira-code-analyzer:latest neira-code-analyzer:v$(date +%Y%m%d)

# Откат на предыдущую версию при проблемах
docker run neira-code-analyzer:v20250112
```

## 📞 Эскалация проблем

### 🆘 Критические ошибки
- API недоступен > 5 минут
- Потеря данных сессий
- Массовые ошибки токенизации

### 📧 Контакты поддержки  
- GitHub Issues: основной канал
- Техническая документация: docs/archive/
- Логи системы: debug_neira.log 

# 🔧 Руководство по поддержке neira-code-analyzer

## 📊 Текущее состояние системы (2025-06-14)

### ✅ Критические проблемы решены
- **Интеграционные тесты:** 82/82 успешно (было 77/82)
- **Покрытие кода:** 34.95% (превышает требуемые 34%)
- **Автоматическая оптимизация:** Реализована для новых проектов (40-60% ускорение)
- **CI/CD pipeline:** Строгий контроль качества с fail-fast

### 🏗️ Архитектурные улучшения
- **Service Container:** Thread-safe dependency injection
- **Error Handling:** Унифицированная система обработки ошибок
- **Path Validation:** Защита от path traversal атак
- **Auto Configuration:** Автоматическая загрузка .neira настроек
- **API Rate Limiting:** Семафор для контроля AI API (max 5 запросов)

## 🚨 Мониторинг

### Ключевые метрики
```bash
# Проверка состояния тестов
uv run pytest tests/ -v

# Покрытие кода (должно быть ≥34%)
uv run pytest --cov=src --cov-report=term-missing

# Качество кода
uv run ruff check .
uv run mypy src/
```

### Критические компоненты для мониторинга
1. **AnalysisSessionManager** - управление сессиями анализа
2. **ServiceContainer** - dependency injection система
3. **PathValidator** - валидация безопасности путей
4. **ErrorHandling** - обработка и логирование ошибок

## 🔄 Процедуры обслуживания

### Еженедельные проверки
- [ ] Запуск полного набора тестов
- [ ] Проверка покрытия кода (цель: ≥34%)
- [ ] Обновление зависимостей через `uv sync`
- [ ] Проверка работы MCP сервера

### Ежемесячные задачи
- [ ] Обновление архитектурной документации
- [ ] Анализ производительности на больших кодовых базах
- [ ] Проверка security audit (bandit, pip-audit)
- [ ] Очистка старых analysis/ файлов

## 🐛 Устранение неполадок

### Частые проблемы и решения

#### 1. Проблемы с импортами в тестах
```bash
# Симптом: ModuleNotFoundError при запуске тестов
# Решение: Проверить PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
uv run pytest tests/
```

#### 2. Ошибки автоконфигурации
```bash
# Симптом: Не применяются настройки .neira
# Проверка: Валидность конфигурации
uv run python -c "from src.neira_code_analyzer.neira_config_loader import NeiraConfigLoader; print(NeiraConfigLoader().get_config_info('.'))"
```

#### 3. Performance деградация
```bash
# Симптом: Медленный анализ
# Решение: Проверить фильтры
uv run python -m src.neira_code_analyzer.main
# В MCP клиенте: set_filters с preset="aggressive"
```

## 📈 Оптимизация производительности

### Автоматическая оптимизация
- **Новые проекты:** Автоматически применяется `set_filters` с aggressive preset
- **Существующие проекты:** Сохраняют текущие настройки
- **Graceful fallback:** Анализ продолжается даже при ошибках автонастройки

### Мониторинг производительности
```bash
# Анализ времени выполнения
time uv run python -c "
from src.neira_code_analyzer.main import main
# Время запуска MCP сервера
"

# Проверка размера контекста
find . -name '*.py' | wc -l  # Количество файлов
find . -name '*.py' -exec wc -l {} + | tail -1  # Общее количество строк
```

## 🔐 Безопасность

### Текущие защиты
- **Path Traversal:** Автоматическая валидация всех путей
- **Input Sanitization:** Проверка пользовательских данных
- **Rate Limiting:** Защита от перегрузки AI API
- **Container Security:** Непривилегированный пользователь в Docker

### Регулярные проверки безопасности
```bash
# Security audit
uv run bandit -r src/
uv run pip-audit

# Vulnerability scan
uv run safety check
```

## 📚 Ссылки на документацию

- **Архитектура:** `docs/guides/architecture/overview.md`
- **Тестирование:** `docs/guides/ops/testing.md`
- **API:** `docs/API.md`
- **Конфигурация:** `docs/guides/features/configuration.md`
- **История изменений:** `docs/changelog/CHANGELOG.md`

## 🆘 Поддержка

### Известные ограничения
- Максимальный размер анализируемого проекта: ~50MB кода
- Concurrent AI запросы: 5 одновременно
- Поддерживаемые языки: Python, JavaScript, TypeScript, Markdown

### Контакты для поддержки
- **Issues:** GitHub Issues для багов и feature requests
- **Documentation:** Обновляется в `docs/` директории
- **Testing:** Все изменения должны проходить через CI/CD 