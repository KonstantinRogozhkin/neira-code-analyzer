# 🔧 Отладочные скрипты

## Правильный запуск

Все скрипты должны запускаться **из корня проекта** как Python модули:

```bash
# Из корня проекта neira-code-analyzer/
python -m scripts.debug.debug_tools
```

## ❌ Не использовать:

```bash
# НЕ делайте так:
cd scripts/debug/
python debug_tools.py  # Не работает из-за импортов
```

## ✅ Правильно:

```bash
# Всегда из корня проекта:
python -m scripts.debug.debug_tools
python -m scripts.test.test_script  # если есть
```

Это устраняет необходимость в `sys.path.insert()` и делает импорты предсказуемыми. 