# 🔍 Инструкция по использованию фильтров NEIRA Browser

## 📋 Обзор

Настроены оптимальные фильтры для анализа кода проекта NEIRA Browser. Конфигурация находится в файле `.neira`.

## 🎯 Основные результаты

- **Оригинальный размер**: 434,841 токенов
- **Оптимизированный размер**: 242,661 токенов  
- **Экономия**: 192,180 токенов (44.2%)
- **Фокус**: Только основной код без тестов, документации, примеров

## 🎛️ НОВОЕ: Система пресетов фильтров

Теперь вы можете сохранять и загружать готовые конфигурации фильтров!

### Встроенные пресеты

- **🏗️ `default`** - Базовые исключения для большинства проектов
- **⚡ `aggressive`** - Агрессивные исключения для экономии токенов  
- **💻 `code-only`** - Только основной код без документации и тестов
- **🐍 `python-project`** - Оптимизировано для Python проектов
- **🌐 `web-app`** - Веб-приложения (JS/TS + Python/PHP)
- **⚛️ `react-app`** - React/Next.js приложения
- **🖥️ `electron-app`** - Electron приложения с мульти-пакетной архитектурой

### Управление пресетами

```bash
# Просмотр всех пресетов
mcp_neira-code-analyzer_manage_presets --action list

# Создание нового пресета
mcp_neira-code-analyzer_manage_presets \
  --action create \
  --name "my-django-app" \
  --include_patterns "*.py" "*.html" "*.css" "*.js" "*.md" \
  --exclude_patterns "*/migrations/**" "*/venv/**" "*/staticfiles/**" \
  --description "Пресет для Django приложений"

# Детали пресета
mcp_neira-code-analyzer_manage_presets --action details --name "python-project"

# Экспорт пресета
mcp_neira-code-analyzer_manage_presets \
  --action export \
  --name "my-django-app" \
  --file_path "./my-django-preset.json"

# Импорт пресета  
mcp_neira-code-analyzer_manage_presets \
  --action import \
  --file_path "./shared-preset.json"
```

## 📊 Доступные пресеты

### 1. `core-only` (рекомендуется)
**Размер**: 242,661 токенов  
**Описание**: Только основной код проекта  
**Включает**:
- `packages/shell/src/**/*.js,*.ts` - Electron shell код
- `packages/neira-app/**/*.tsx,*.ts,*.js` - Next.js приложение  
- `packages/shared-types/src/**/*.ts` - Общие типы
- `*.json` - Конфигурационные файлы

### 2. `all-code` 
**Размер**: 360,871 токенов  
**Описание**: Весь код проекта включая CSS, HTML  
**Включает**: `*.js`, `*.ts`, `*.tsx`, `*.jsx`, `*.json`, `*.css`, `*.html`

### 3. `shell-only`
**Описание**: Только Electron shell код  
**Включает**: `packages/shell/src/**/*`, `packages/shared-types/**/*`

### 4. `neira-app-only`
**Описание**: Только Next.js приложение  
**Включает**: `packages/neira-app/**/*`, `packages/shared-types/**/*`

### 5. `managers-only`
**Описание**: Только Manager Architecture  
**Включает**: `packages/shell/src/main/managers/**/*`, `super-app.js`

## 🚀 Команды для анализа

### Использование встроенных пресетов

```bash
# Анализ Python проекта
mcp_neira-code-analyzer_analyze_filters \
  --path /Users/konstantin/Projects/my-python-app \
  --preset_name python-project

# Анализ React приложения с дополнительными файлами
mcp_neira-code-analyzer_analyze_filters \
  --path /Users/konstantin/Projects/my-react-app \
  --preset_name react-app \
  --merge_with_preset true \
  --include_patterns "*.md" "*.yml" \
  --save_as_preset "my-react-docs"

# Анализ Electron приложения
mcp_neira-code-analyzer_analyze_filters \
  --path /Users/konstantin/Projects/neira-browser \
  --preset_name electron-app
```

### Полный анализ кода с пресетами

```bash
# Code review с Python пресетом
mcp_neira-code-analyzer_code_review \
  --path /Users/konstantin/Projects/my-python-app \
  --preset_name python-project \
  --template_name code-review

# Web app анализ с сохранением в пресет
mcp_neira-code-analyzer_code_review \
  --path /Users/konstantin/Projects/my-webapp \
  --preset_name web-app \
  --merge_with_preset true \
  --include_patterns "*.md" \
  --save_as_preset "my-webapp-with-docs" \
  --template_name security-audit
```

### Полный анализ кода (рекомендуется)
```bash
# Используя preset core-only (242,661 токенов)
mcp_neira-code-analyzer_code_review \
  --path /Users/konstantin/Projects/neira-browser \
  --include_patterns packages/shell/src/**/*.js packages/shell/src/**/*.ts packages/neira-app/**/*.tsx packages/neira-app/**/*.ts packages/neira-app/**/*.js packages/shared-types/src/**/*.ts *.json \
  --exclude_patterns "*/node_modules/**" "**/node_modules/**" "node_modules/**" "dist/**" "out/**" "build/**" "*.log" "*.tmp" ".git/**" "yarn.lock" "package-lock.json" "*.min.js" "*.min.css" "playwright-report/**" "tests/**" "coverage/**" "tmp.iconset/**" "drizzle/migrations/**" "docs/**" "extensions/**" "certificates/**" "public/**" "*.md" "script/**" "spec/**" "examples/**" "fixtures/**" "*.lock" ".vscode/**" ".cursor/**" "tmp-*/**" "**/*.test.*" "**/*.spec.*" "**/migrations/**" "**/meta/**"
```

### Анализ архитектуры Super App 2.0
```bash
# Только Manager Architecture
mcp_neira-code-analyzer_code_review \
  --path /Users/konstantin/Projects/neira-browser \
  --include_patterns packages/shell/src/main/managers/**/*.js packages/shell/src/main/managers/**/*.ts packages/shell/src/main/super-app.js packages/shared-types/src/**/*.ts \
  --exclude_patterns "node_modules/**" "**/*.test.*" "**/*.spec.*" \
  --template_name architecture-analysis
```

### Анализ AI интеграции  
```bash
# Только neira-app с AI функциями
mcp_neira-code-analyzer_code_review \
  --path /Users/konstantin/Projects/neira-browser \
  --include_patterns packages/neira-app/**/*.tsx packages/neira-app/**/*.ts packages/neira-app/**/*.js packages/neira-app/*.json packages/shared-types/src/**/*.ts \
  --exclude_patterns "node_modules/**" "dist/**" "out/**" "build/**" "*.log" "*.tmp" ".git/**" "drizzle/migrations/**" "drizzle/meta/**" "tests/**" "spec/**" "examples/**" "**/*.test.*" "**/*.spec.*" "public/**" "certificates/**" \
  --template_name api-documentation
```

## 📁 Исключенные категории

### Полностью исключены:
- **Документация**: `docs/**`, `*.md`
- **Тесты**: `tests/**`, `**/*.test.*`, `**/*.spec.*`
- **Сборка**: `dist/**`, `out/**`, `build/**`, `node_modules/**`
- **Примеры**: `examples/**`, `fixtures/**`, `spec/**`
- **Ресурсы**: `public/**`, `certificates/**`, `tmp.iconset/**`
- **Миграции**: `drizzle/migrations/**`, `drizzle/meta/**`
- **Extensions**: `extensions/**` (Chrome extensions)
- **Конфигурация**: `.vscode/**`, `.cursor/**`, `*.lock`

### Типы файлов исключены:
- Логи: `*.log`, `*.tmp`
- Минифицированные: `*.min.js`, `*.min.css`
- Отчеты: `playwright-report/**`, `coverage/**`
- Временные: `tmp-*/**`

## 🎯 Рекомендации по использованию

### Для анализа кода:
1. **Используйте готовые пресеты** - `python-project`, `react-app`, `web-app`
2. **Создавайте свои пресеты** для часто используемых конфигураций
3. **Объединяйте пресеты** с дополнительными паттернами через `merge_with_preset`

### Для отладки:
1. **Добавьте конкретные файлы** в include_patterns при необходимости
2. **Временно уберите исключения** если нужны тесты или документация
3. **Используйте `all-code`** если нужны CSS/HTML файлы

### Для производительности:
- Встроенные пресеты оптимизированы по токенам
- `code-only` - максимальная экономия
- `python-project`, `react-app` - сбалансированные для соответствующих технологий
- Создавайте пресеты для повторяющихся проектов

## 🔧 Создание пользовательских пресетов

### Пример: Django приложение
```bash
mcp_neira-code-analyzer_manage_presets \
  --action create \
  --name "django-full" \
  --include_patterns "*.py" "*.html" "*.css" "*.js" "*.md" "*.yml" "*.yaml" "requirements*.txt" "manage.py" "*.json" \
  --exclude_patterns "*/migrations/**" "*/venv/**" "*/env/**" "*/staticfiles/**" "*/media/**" "*/logs/**" "**/__pycache__/**" "*.pyc" "*.log" "db.sqlite3" \
  --description "Полный Django проект с шаблонами и статикой"
```

### Пример: Node.js API
```bash
mcp_neira-code-analyzer_manage_presets \
  --action create \
  --name "nodejs-api" \
  --include_patterns "*.js" "*.ts" "*.json" "*.md" "*.yml" "*.yaml" \
  --exclude_patterns "node_modules/**" "dist/**" "build/**" "coverage/**" "*.log" "*.tmp" ".nyc_output/**" \
  --description "Node.js API сервер"
```

### Пример: Vue.js приложение  
```bash
mcp_neira-code-analyzer_manage_presets \
  --action create \
  --name "vue-app" \
  --include_patterns "*.vue" "*.js" "*.ts" "*.css" "*.scss" "*.json" "*.md" \
  --exclude_patterns "node_modules/**" "dist/**" "build/**" "public/**" "*.min.*" \
  --description "Vue.js приложение"
```

## 📊 Статистика оптимизации

| Категория | Токенов сэкономлено | Процент |
|-----------|--------------------|---------| 
| Документация | ~50,000 | 11.5% |
| Тесты | ~45,000 | 10.4% |
| Примеры/Fixtures | ~30,000 | 6.9% |
| Build артефакты | ~25,000 | 5.7% |
| Статические ресурсы | ~20,000 | 4.6% |
| Прочее | ~22,180 | 5.1% |
| **Итого** | **192,180** | **44.2%** |

## 💡 Полезные советы

1. **Пресет + дополнения**: Используйте `merge_with_preset: true` для добавления файлов к пресету
2. **Сохранение удачных конфигураций**: `save_as_preset` для создания пресета из текущего анализа
3. **Экспорт/импорт**: Делитесь пресетами между проектами и командой
4. **Встроенные пресеты как основа**: Начинайте с `python-project`, `react-app` и модифицируйте
5. **Тестирование пресетов**: Используйте `analyze_filters` для проверки перед `code_review`

---

*Конфигурация оптимизирована для проекта NEIRA Browser Super App 2.0 архитектуры с новой системой пресетов* 