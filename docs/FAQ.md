# FAQ - neira-code-analyzer

Часто задаваемые вопросы и решения типичных проблем.

## 🔧 Установка и настройка

### В: Как установить neira-code-analyzer?

**О**: 
```bash
# Клонируйте репозиторий
git clone https://github.com/odancona/neira-code-analyzer.git
cd neira-code-analyzer

# Установите зависимости
uv sync

# Проверьте установку
uv run python -m src.neira_code_analyzer.main --help
```

### В: Где получить Google AI API ключ?

**О**: 
1. Перейдите на [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Войдите в аккаунт Google
3. Создайте новый API ключ
4. Установите переменную окружения:
   ```bash
   export GOOGLE_AI_API_KEY="your-api-key-here"
   ```

### В: Как проверить что сервер работает?

**О**:
```bash
# Быстрая проверка
npx @modelcontextprotocol/inspector \
  uv run python -m src.neira_code_analyzer.main

# Или тест инструмента
uv run python -c "
from src.neira_code_analyzer.main import main
result = main()
print('Сервер работает!' if result else 'Ошибка')
"
```

---

## 🎯 Использование инструментов

### В: Какой инструмент лучше использовать для анализа кода?

**О**: Рекомендуем `get_analyze` - это флагманский инструмент:
- ⭐ **Новичкам**: `get_analyze` с `template_name: "code-review"`
- 🔒 **Для безопасности**: `template_name: "security-audit"`
- 📚 **Для документации**: `template_name: "documentation"`
- 🚀 **Для рефакторинга**: `template_name: "refactoring"`

### В: Как продолжить интерактивный анализ?

**О**: Используйте `session_id` из предыдущего ответа:
```json
{
  "path": "/path/to/project",
  "session_id": "20241214_143022",
  "user_query": "Теперь проанализируй модуль авторизации"
}
```

### В: Какие пресеты фильтров доступны?

**О**: Используйте `manage_presets` с `action: "list"`:
- `default` - Базовая конфигурация
- `aggressive` - Максимальное исключение файлов
- `python-project` - Для Python проектов
- `web-app` - Для веб-приложений
- `react-app` - Для React приложений

---

## ⚠️ Проблемы и ошибки

### В: Ошибка "Token limit exceeded"

**О**: Превышен лимит токенов. Решения:
1. **Используйте агрессивные фильтры**:
   ```json
   {"preset_name": "aggressive", "max_tokens": 500000}
   ```

2. **Исключите большие файлы**:
   ```json
   {"exclude_patterns": ["*.log", "dist/**", "node_modules/**"]}
   ```

3. **Уменьшите max_tokens**:
   ```json
   {"max_tokens": 300000}
   ```

### В: Ошибка "API key not found"

**О**: Не установлен Google AI API ключ:
```bash
# Проверьте переменную
echo $GOOGLE_AI_API_KEY

# Установите (Linux/macOS)
export GOOGLE_AI_API_KEY="your-key"

# Установите (Windows)
set GOOGLE_AI_API_KEY=your-key

# Перезапустите MCP-клиент
```

### В: Сервер не запускается в Claude Desktop

**О**: Проблемы с конфигурацией MCP:

1. **Проверьте путь к проекту**:
   ```json
   {
     "servers": {
       "neira-code-analyzer": {
         "cwd": "/полный/путь/к/neira-code-analyzer"
       }
     }
   }
   ```

2. **Проверьте установку uv**:
   ```bash
   which uv
   uv --version
   ```

3. **Проверьте файл конфигурации** (`~/.claude_desktop/claude_desktop_config.json`)

### В: Анализ работает очень медленно

**О**: Оптимизация производительности:

1. **Используйте подходящий пресет**:
   ```json
   {"preset_name": "code-only"}
   ```

2. **Ограничьте количество файлов**:
   ```json
   {"include_patterns": ["src/**/*.py"]}
   ```

3. **Выберите быструю модель**:
   ```json
   {"ai_model": "gemini-2.0-flash"}
   ```

---

## 🔍 Работа с фильтрами

### В: Как создать собственный пресет фильтров?

**О**: Используйте `manage_presets`:
```json
{
  "action": "create",
  "name": "my-custom-preset",
  "description": "Мой кастомный пресет",
  "include_patterns": ["*.py", "*.js"],
  "exclude_patterns": ["tests/**", "*.log"]
}
```

### В: Как узнать сколько токенов займет анализ?

**О**: Используйте `get_context` без анализа:
```json
{
  "path": "/path/to/project",
  "preset_name": "default",
  "save_to_file": "token_count.md"
}
```
В результате будет показана статистика по токенам.

### В: Как исключить определенные папки?

**О**: Используйте `exclude_patterns`:
```json
{
  "exclude_patterns": [
    "node_modules/**",
    "dist/**", 
    "build/**",
    "*.log",
    "__pycache__/**",
    ".git/**"
  ]
}
```

---

## 🤖 Работа с AI

### В: Какую модель AI лучше выбрать?

**О**: Зависит от задач:
- **`gemini-2.5-pro-preview-06-05`** - Самый мощный, лучшее качество анализа
- **`gemini-2.0-flash`** - Быстрый, подходит для простых задач
- **`gemini-1.5-pro`** - Баланс между качеством и скоростью

### В: Как задать конкретный вопрос для анализа?

**О**: Используйте параметр `user_query`:
```json
{
  "user_query": "Найди все потенциальные уязвимости безопасности и предложи исправления"
}
```

### В: Можно ли анализировать код на других языках?

**О**: Да! Поддерживаются:
- Python, JavaScript, TypeScript
- Java, C#, C++, Go, Rust
- HTML, CSS, SQL
- Markdown, JSON, YAML
- И многие другие

---

## 📊 Результаты и отчеты

### В: Где сохраняются результаты анализа?

**О**: 
- **Интерактивный анализ**: В папке `.docs_session/`
- **Генерация контекста**: Параметр `save_to_file`
- **Документация**: В папке `docs/`

### В: Как получить JSON ответ вместо текста?

**О**: `get_analyze` всегда возвращает структурированный JSON:
```json
{
  "session_id": "20241214_143022",
  "ai_response": "Текст анализа...",
  "actions_applied": [...],
  "file_stats": {...}
}
```

### В: Можно ли автоматически применять исправления кода?

**О**: Да! AI может автоматически исправлять код:
- Включено по умолчанию в `get_analyze`
- Безопасно - создается backup перед изменениями
- Применяются только безопасные исправления

---

## 🛠️ Интеграция и автоматизация

### В: Как интегрировать в CI/CD?

**О**: Пример для GitHub Actions:
```yaml
- name: Code Analysis
  env:
    GOOGLE_AI_API_KEY: ${{ secrets.GOOGLE_AI_API_KEY }}
  run: |
    git clone https://github.com/odancona/neira-code-analyzer.git
    cd neira-code-analyzer
    uv sync
    uv run python -c "
    from src.neira_code_analyzer.main import main
    result = main({
      'path': '../',
      'template_name': 'code-review'
    })
    print(result)
    "
```

### В: Можно ли использовать без MCP клиента?

**О**: Да, можно вызывать напрямую:
```python
from src.neira_code_analyzer.main import main

result = main({
    "path": "/path/to/project",
    "template_name": "code-review",
    "user_query": "Проанализируй код"
})

print(result)
```

### В: Как настроить для команды разработчиков?

**О**: 
1. **Создайте общие пресеты** для ваших проектов
2. **Настройте переменные окружения** на сервере
3. **Создайте документацию** с типовыми запросами
4. **Интегрируйте в CI/CD** для автоматического анализа

---

## 🔧 Отладка и логирование

### В: Как включить подробное логирование?

**О**:
```bash
export NEIRA_DEBUG=1
export NEIRA_LOG_LEVEL=DEBUG

# Запуск с логами
uv run python -m src.neira_code_analyzer.main 2>&1 | tee debug.log
```

### В: Как найти причину ошибки?

**О**:
1. **Включите отладку** (см. выше)
2. **Проверьте логи**:
   ```bash
   grep -i error debug.log
   ```
3. **Используйте MCP Inspector** для тестирования
4. **Проверьте права доступа** к файлам

### В: Сервер падает при анализе больших проектов

**О**: Оптимизация для больших проектов:
```json
{
  "preset_name": "aggressive",
  "max_tokens": 800000,
  "exclude_patterns": [
    "node_modules/**",
    "dist/**",
    "*.log",
    "*.min.js",
    "__pycache__/**"
  ]
}
```

---

## 💡 Лучшие практики

### В: Как получить максимально качественный анализ?

**О**:
1. **Используйте конкретные запросы**:
   ```json
   {"user_query": "Найди SQL-инъекции в модуле аутентификации"}
   ```

2. **Выберите подходящий шаблон**:
   - `security-audit` для безопасности
   - `performance-analysis` для производительности
   - `code-review` для общего анализа

3. **Оптимизируйте фильтры** - исключайте ненужные файлы

4. **Используйте интерактивные сессии** для глубоких исследований

### В: Как организовать документацию проекта?

**О**: Используйте `gen_docs`:
```json
{
  "path": "/path/to/project",
  "docs_structure": "standard",
  "update_changelog": true,
  "git_scan_days": 30
}
```

Это создаст полную структуру документации автоматически.

---

## 🚀 Продвинутое использование

### В: Можно ли создать собственные шаблоны?

**О**: Да, используйте кастомный Handlebars шаблон:
```json
{
  "template": "# Анализ {{project_name}}\n\n{{#each files}}## {{this.path}}\n```{{this.language}}\n{{this.content}}\n```\n{{/each}}"
}
```

### В: Как анализировать только измененные файлы?

**О**: Используйте git для получения списка измененных файлов:
```bash
# Получить измененные файлы
git diff --name-only HEAD~1

# Создать паттерн включения
include_patterns=$(git diff --name-only HEAD~1 | sed 's/^/"/' | sed 's/$/"/' | tr '\n' ',' | sed 's/,$//')
```

### В: Можно ли сравнить два проекта?

**О**: Да, анализируйте их по отдельности и сравните результаты:
```json
[
  {
    "path": "/path/to/project1",
    "template_name": "code-review",
    "save_to_file": "project1_analysis.md"
  },
  {
    "path": "/path/to/project2", 
    "template_name": "code-review",
    "save_to_file": "project2_analysis.md"
  }
]
```

---

## 📞 Поддержка

### В: Где сообщить об ошибке?

**О**: 
- **GitHub Issues**: [Создать issue](https://github.com/odancona/neira-code-analyzer/issues)
- **Приложите логи** с включенной отладкой
- **Опишите шаги** для воспроизведения проблемы

### В: Как предложить улучшение?

**О**:
- **GitHub Discussions**: Обсуждение идей
- **Pull Request**: Готовые изменения
- **Feature Request**: Новые возможности

### В: Есть ли примеры использования?

**О**: Да! См. документацию:
- [`docs/guides/examples/use_cases.md`](guides/examples/use_cases.md) - Детальные примеры
- [`docs/guides/integration/mcp_integration.md`](guides/integration/mcp_integration.md) - Интеграция
- [`docs/API.md`](API.md) - Справочник по API

---

*Последнее обновление: 2024-12-14*

📚 **Дополнительные ресурсы:**
- [Быстрый старт](help/quickstart.md)
- [API Reference](API.md)
- [Примеры использования](guides/examples/use_cases.md)
- [Архитектурный обзор](guides/architecture/overview.md) 