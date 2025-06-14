# 🌐 Интеграция с neira-browser

**Статус:** ✅ Настроена  
**Проект:** NEIRA Browser Super App 2.0  
**Версия:** 2.2.0  

## 🎯 Обзор

Neira-code-analyzer полностью интегрирован с **NEIRA Browser** - минималистичным браузером с AI-агентами, основанным на Electron + React.

## 📂 Конфигурация

**Папка:** `.neira/` (директория, не файл)
- **analysis_session.json** - основная сессия
- **analysis_sessions/current_session.json** - активная сессия
- **config.json** - общие настройки (автосоздается при конфликте)

## 🔧 Активные настройки

**Текущая сессия:** 20250613_171112
- **Режим:** interactive (шаг 2)
- **Шаблон:** code-review  
- **AI модель:** gemini-2.5-pro-preview-06-05
- **Лимит токенов:** 1,000,000
- **Пресет:** react-app (расширенный)

## 🎛️ Рекомендуемые пресеты

**Для Electron проектов:**
- ✅ **electron-app** - оптимальный для neira-browser
- **react-app** - текущий (работает, но не идеален)
- **aggressive** - для экономии токенов

## 🚫 Критические исправления фильтров

**Проблема:** Огромные файлы не исключались
- `crxtesthost_simple` (85.2MB) - native messaging host
- `.turbo/cache/*.tar.zst` (554MB) - Turbo кэш  
- `node_modules/electron/dist/` (161MB) - Electron binary

**Решение:** Обновлены фильтры в `DEFAULT_EXCLUDES`:
```python
# Критические исключения
".turbo/**", "**/.turbo/**",
"**/native-messaging-host/**", 
"crxtesthost*", "**/crxtesthost*",
"**/Electron.app/**", "**/*electron*/**",
"*.node", "*.dylib", "*.so", "*.dll"
```

## 🏗️ Архитектура проекта

**Монорепозиторий (6 пакетов):**
1. **packages/shell** - Основное Electron приложение
2. **packages/electron-chrome-extensions** - Chrome extensions
3. **packages/electron-chrome-context-menu** - Контекстное меню
4. **packages/electron-chrome-web-store** - Chrome Web Store интеграция
5. **packages/neira-app** - React фронтенд
6. **packages/shared-types** - Общие TypeScript типы

## 🛠️ Технологический стек

**Основа:**
- **Node.js:** ≥20.0.0, **Yarn:** ≥1.10.0
- **Electron:** ^36.3.2, **React:** ^19.1.0
- **TypeScript:** ^5.8.3, **Tailwind CSS:** ^4.1.8

**Инструменты:**
- **Turbo** - монорепозиторий, **Electron Vite** - сборка
- **Vitest** - тестирование, **Playwright** - E2E
- **ESLint/Prettier** - качество кода

## 📋 Включаемые типы файлов

```json
{
  "include_patterns": [
    "*.ts", "*.tsx", "*.js", "*.jsx",
    "*.json", "*.md", "*.css"
  ],
  "exclude_patterns": []
}
```

## 🎯 Последний анализ

**Запрос:** "Код-ревью с фокусом на проблемы с агентами в чате при выполнении Tools и архитектурные улучшения браузера"

**Выявленные проблемы:**
1. **UI компоненты** - неработающие вкладки и навигация (критично)
2. **APIManager** - требует рефакторинг для улучшения обработки инструментов

## 🚀 Рекомендации

**Приоритет 1 (Критично):**
- Исправить UI компоненты (вкладки, навигация)
- Переключиться на пресет `electron-app`

**Приоритет 2:**
- Рефакторинг APIManager для Tools
- Оптимизировать размер анализируемых файлов
- Провести security-audit анализ

## 📊 Производительность

**Оптимизации:**
- Исключение `.git` папки (экономия ~100MB)
- Агрессивная фильтрация кэша и билдов
- Лимит файлов: 200KB (ужесточен с 500KB)

---
**Поддержка:** Автоматическая через .neira конфигурацию  
**Обновления:** При каждом анализе  
**Детали:** [Архив 2025-01](../../archive/2025-01/) 