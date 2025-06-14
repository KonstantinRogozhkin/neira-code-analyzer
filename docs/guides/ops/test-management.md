# 🧪 Управление тестами

**Статус:** ✅ Реализовано (95%)  
**Покрытие:** 40.23% (цель: 34%)  
**Успешность:** 95% тестов проходят  

## 🎯 Концепция

- **«Зелёный master»** - все PR блокируются при красных тестах
- **«Ноль хаоса»** - устаревшие скрипты архивируются
- **«Автомат вместо руки»** - каждый баг → регрессионный тест
- **«Отладка → тест → архив»** - цикл конвертации за неделю

## 📁 Структура

```
tests/
├── unit/          # 117 тестов ✅
├── integration/   # 8 тестов ✅  
├── e2e/           # структура готова
├── regression/    # 10 тестов ✅
├── performance/   # структура готова
└── helpers/       # общие фикстуры
```

## 🔄 Недельный цикл S-A-C-V-C

| Шаг | Действие | Команда | Лимит времени |
|-----|----------|---------|---------------|
| **Scan** | Найти новые скрипты | `ls scripts/debug` | 15 мин |
| **Analyze** | Проверить дубли | `grep -Ri "<key>" tests/` | 30 мин |
| **Convert** | Создать тест | pytest format | 2 часа |
| **Validate** | Полный suite | `uv run pytest tests/` | 5 мин |
| **Clean** | Архивировать | `git mv → archive/` | 10 мин |

## 📊 Месячный аудит

**Проверяемые зоны:**
1. **Regression** (крит.) - нельзя skip/xfail
2. **E2E flows** - актуальность UI сценариев  
3. **Coverage holes** - модули < 90%
4. **Performance** - Suite < 5 мин

**Критерии Done:**
- Flaky-index ≤ 1%
- Coverage backend ≥ 95%
- `scripts/debug` пуст

## 🚀 Команды

```bash
# Быстрые тесты
uv run pytest tests/

# С покрытием
uv run pytest tests/ --cov=src --cov-report=html

# Только unit
uv run pytest tests/unit/

# Производительность
uv run pytest tests/ --durations=10
```

## ✅ Правила коммитов

**Формат:** `test(scope): action`
- **Scope:** unit|integration|e2e|regression|perf
- **Action:** add|fix|refactor|remove|quarantine

**Примеры:**
- `test(regression): add case for #412 null pointer`
- `test(unit): add coverage for edge case in validator`

## 📋 Reviewer checklist

- [ ] Файл в правильной подпапке
- [ ] Название отражает поведение
- [ ] Нет debug артефактов
- [ ] Время < 2 сек (unit) / < 30 сек (e2e)
- [ ] Скрипт-предок заархивирован

## 🎯 Текущие метрики

**Покрытие по модулям:**
- 🟢 **>85%:** AI Utils (92%), BaseSessionManager (90%)
- 🟡 **50-85%:** DocsGenerator (81%), MCPSchemas (79%)  
- 🔴 **<50%:** ActionExecutor (46%), Filters (36%)

**Автоматизация:**
- ✅ Недельный цикл: `scripts/utils/test_management_cycle.py`
- ✅ Месячный аудит: `scripts/utils/monthly_test_audit.py`

## 🚨 Критические правила

**RED FLAGS:**
- Тест не запускается на CI
- Дублирует существующий без причины
- Hardcoded пути/пароли
- Unit тест зависит от integration компонентов

---
**Автоматизация:** Полная  
**Статус:** Готово к production  
**Детали:** [Архив 2025-01](../../archive/2025-01/) 