# 🎯 Система фильтров neira-code-analyzer


## 📋 Встроенные пресеты

### 🔧 `default`
**Описание:** Базовые исключения для большинства проектов  
**Рекомендуется для:** Общего анализа, документирования  
**Токены:** Средний размер проекта

### ⚡ `aggressive` 
**Описание:** Агрессивные исключения для экономии токенов  
**Рекомендуется для:** Code review с лимитами токенов  
**Токены:** Значительная экономия токенов

### 🎯 `code-only`
**Описание:** Только основной код без документации и тестов  
**Рекомендуется для:** Анализ архитектуры, рефакторинг  
**Токены:** Максимальная экономия токенов

### 🐍 `python-project`
**Описание:** Оптимизировано для Python проектов  
**Включает:** `*.py`, `*.pyi`, `requirements*.txt`, `pyproject.toml`  
**Исключает:** `__pycache__`, `.pytest_cache`, `venv`, `*.pyc`

### 🌐 `web-app`
**Описание:** Веб-приложения (JS/TS + Python/PHP)  
**Включает:** `*.js`, `*.ts`, `*.tsx`, `*.py`, `*.html`, `*.css`  
**Исключает:** `*.min.js`, `public/**`, `__pycache__`

### ⚛️ `react-app`
**Описание:** React/Next.js приложения  
**Включает:** `*.js`, `*.ts`, `*.tsx`, `*.jsx`, `*.css`, `*.scss`  
**Исключает:** `.next/**`, `public/**`, `*.min.js`

### 🖥️ `electron-app`
**Описание:** Electron приложения с мульти-пакетной архитектурой  
**Включает:** `packages/*/src/**/*.js`, `packages/*/**/*.tsx`  
**Исключает:** `packages/*/dist/**`, `certificates/**`

## 🛠️ Использование пресетов

### Через MCP инструменты

```json
{
  "path": "/path/to/project",
  "preset_name": "python-project"
}
```

### Объединение с кастомными фильтрами

```json
{
  "path": "/path/to/project", 
  "preset_name": "default",
  "include_patterns": ["*.md"],
  "exclude_patterns": ["*.backup"],
  "merge_with_preset": true
}
```

## 📊 Управление пресетами

### Создание собственного пресета

```json
{
  "action": "create",
  "name": "my-web-preset",
  "include_patterns": ["*.js", "*.ts", "*.html"],
  "exclude_patterns": ["node_modules/**", "dist/**"],
  "description": "Мой кастомный веб-пресет"
}
```

### Экспорт/импорт пресетов

```json
{
  "action": "export",
  "name": "my-preset",
  "file_path": "/path/to/preset.json"
}
```

```json
{
  "action": "import", 
  "file_path": "/path/to/preset.json"
}
```

## 🚀 Quick Performance Win

### Автоматические исключения
По умолчанию исключаются:
- 📦 **Lock-файлы:** `package-lock.json`, `yarn.lock`, `poetry.lock`
- 🔤 **Шрифты:** `*.woff`, `*.woff2`, `*.ttf`, `*.eot`
- 🗂️ **Кэши:** `.mypy_cache`, `.pytest_cache`, `.tox`, `.ruff_cache`
- 🏗️ **Сборка:** `.next`, `.nuxt`, `.vite`, `.rollup.cache`

### Экономия токенов
- **Lock-файлы:** до 50,000 токенов каждый
- **Кэши тестов:** до 10,000 токенов  
- **Минифицированные файлы:** до 20,000 токенов

## 💡 Принципы оптимизации

### Основной принцип
> **"Provide as little context as possible, but as much as necessary"**

### Стратегии экономии
1. **Используйте include_patterns** вместо широких exclude_patterns
2. **Исключайте тестовые данные** - они часто самые "тяжелые"
3. **Уберите lock-файлы** - один файл может содержать десятки тысяч токенов
4. **Игнорируйте медиа-файлы** - изображения и шрифты не нужны для анализа кода

### Автоматические рекомендации

---
*Документ автоматически сжат до ключевых моментов*
