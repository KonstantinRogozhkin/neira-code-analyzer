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
result = cg.analyze_filters('/path/to/project')
print(f'Tokens: {result.stats.estimated_tokens}')
"
```

## 🔍 Диагностика проблем

### 🚨 Основные проблемы и решения

#### Высокое потребление токенов
- Используйте `analyze_filters` для оптимизации
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