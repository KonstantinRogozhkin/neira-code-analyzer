"""
Централизованная конфигурация фильтров для анализа кода.

Содержит константы со списками исключений для различных типов проектов
и задач анализа, избегая дублирования кода.

Новые возможности:
- Система пресетов для сохранения и загрузки конфигураций фильтров
- Автоматическое сохранение удачных конфигураций
- Загрузка готовых пресетов для популярных проектов
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Базовые исключения - применяются везде для разумного анализа
DEFAULT_EXCLUDES: list[str] = [
    # Зависимости - все уровни вложенности (КРИТИЧНО!)
    "node_modules/**", "*/node_modules/**", "**/node_modules/**",
    "tmp-*/**/node_modules/**", "*/tmp-*/**/node_modules/**",

    # Временные билды (очень много мусора!)
    "tmp-*/**", "*/tmp-*/**", "**/tmp-*/**",

    # Медиа файлы
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.ico", "*.webp",
    "*.wav", "*.mp3", "*.mp4", "*.avi", "*.mov",

    # Файлы иконок (занимают много токенов)
    "*.icns", "*.icl", "*.cur",

    # Шрифты (много токенов для анализа)
    "*.woff", "*.woff2", "*.ttf", "*.eot", "*.otf",

    # Бинарные и специальные файлы
    "*.blob", "*.bin", "*.exe", "*.dll", "*.db", "*.sqlite", "*.sqlite3",

    # Сборка и компиляция
    "dist/**", "**/dist/**", "build/**", "**/build/**", "out/**", "**/out/**",
    ".webpack/**", "*/.webpack/**", "**/.webpack/**",
    "*.tsbuildinfo", "*.map", "*.min.js", "*.min.css", "*.bundle.js", "*.chunk.js",

    # Системные и IDE файлы
    ".git/**", ".DS_Store", "Thumbs.db", "*.log", "*.tmp", "*.cache", "*.lock", "uv.lock", "*.backup",
    ".idea/**", ".vscode/**", ".devcontainer/**", "*.pyc", "*.pyo", "*.pyd",

    # Lock-файлы менеджеров пакетов (очень большие)
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Pipfile.lock",

    # Дополнительные кэши инструментов разработки (Quick Performance Win)
    ".mypy_cache/**", ".pytest_cache/**", ".tox/**", ".ruff_cache/**",

    # Специфичные для IDE и окружений файлы
    "nbproject/**", "*.swp", "*.swo",

    # Бинарные файлы (скомпилированные библиотеки)
    "*.so", "*.dll", "*.dylib", "*.pyd",

    # Специфичные для Electron/Tauri артефакты сборки
    "src-tauri/target/**", "**/src-tauri/target/**",

    # Тесты - основные паттерны
    "test/**", "tests/**", "__tests__/**", "spec/**",
    "**/test/**", "**/tests/**", "**/spec/**",

    # Тестовые данные и записи (КРИТИЧНО!)
    "**/test/**/recordings/**", "**/test/**/fixtures/**", "**/test/**/results/**",
    "**/test/**/data/**", "**/perf-tests/**", "**/colorize-tests/**",
    "**/colorize-perf-tests/**", "**/browser/recordings/**",

    # Тестовые файлы по именам
    "*.test.js", "*.test.ts", "*.test.jsx", "*.test.tsx",
    "*.spec.js", "*.spec.ts", "*.spec.jsx", "*.spec.tsx",
    "*test*.json", "*fixture*.json", "*recording*.ts", "*perf-data*.ts",

    # Отчеты тестов (все варианты + более точные паттерны)
    "playwright-report/**", "**/playwright-report/**", "*/playwright-report/**",
    "test-results/**", "**/test-results/**", "*/test-results/**",
    "coverage/**", "**/coverage/**", "*/coverage/**",
    ".nyc_output/**", "**/.nyc_output/**",

    # Конкретные файлы отчетов
    "playwright-report/index.html", "**/playwright-report/index.html",
    "*/playwright-report/index.html",

    # Кэши сборки и временные папки
    "/.build-cache/", "/.cache/", "/cache/", "/caches/",
    "/.next/", "/.nuxt/", "/.output/", "/.vercel/", "/.netlify/",
    "/.turbo/", "/.parcel-cache/", "/.swc/", "/.vite/", "/.rollup.cache/",
    "/.npm/", "/.yarn/", "/.pnpm-store/", "/.pnpm/",
    "/.mypy_cache/", "/.tox/", "/.coverage/",
    "/.gradle/", "/.m2/",
    "/.ccls-cache/", "/.clangd/", "/cmake-build-",
    "/DerivedData/", "/Pods/",
    "/Library/", "/Temp/", "/Binaries/", "/Intermediate/", "/Saved/",
    "/tmp/", "/temp/", "/temporary/",

    # Quick Performance Win: дополнительные кэши JS инструментов и современных фреймворков
    "/.nuxt/", ".nuxt/**",
    "/.vite/", ".vite/**",
    "/.rollup.cache/", ".rollup.cache/**",
    "/.pnpm-store/", ".pnpm-store/**",
    "/.turbo/", ".turbo/**",
    "/.svelte-kit/", ".svelte-kit/**",
    "/.astro/", ".astro/**",
    "/.solid/", ".solid/**",
    "/.angular/", ".angular/**",
    "/storybook-static/", "storybook-static/**",
    "/.storybook/public/", ".storybook/public/**",
]

# 🚀 НОВЫЙ ФИЛЬТР: Исключение больших файлов для оптимизации производительности
# Quick Feature Add - Константы для фильтрации по размеру файла
MAX_FILE_SIZE_KB = 500  # По умолчанию исключаем файлы больше 500KB
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_KB * 1024

# Паттерны больших файлов, которые обычно не нужны для анализа кода
LARGE_FILE_EXTENSIONS = [
    # Большие данные и ресурсы
    "*.pdf", "*.doc", "*.docx", "*.ppt", "*.pptx", "*.xls", "*.xlsx",
    # Архивы и пакеты
    "*.zip", "*.tar", "*.gz", "*.7z", "*.rar", "*.deb", "*.rpm",
    # Большие файлы данных
    "*.csv", "*.json", "*.xml", "*.yaml", "*.yml",  # если >500KB
    # Большие лог файлы
    "*.log", "*.out", "*.err",  # если >500KB
]

# Агрессивные исключения для code review (когда нужно сократить токены)
AGGRESSIVE_EXCLUDES: list[str] = DEFAULT_EXCLUDES + [
    # Документация
    "*.md", "README*", "CHANGELOG*", "LICENSE*",
    "docs/**", "documentation/**",

    # Конфигурационные файлы
    "*.json", "package*.json", "*.yaml", "*.yml",
    "scripts/**", "tools/**", "*.sh", "*.bat",

    # Стили и разметка
    "*.css", "*.scss", "*.less", "*.html",
    "assets/**", "public/**", "static/**",
]

# Паттерны для включения только основных файлов кода
CODE_ONLY_INCLUDES: list[str] = [
    "*.py", "*.js", "*.ts", "*.tsx", "*.jsx", "*.java", "*.cpp", "*.c", "*.h", "*.go", "*.rs", "*.php"
]

# 🎯 ВСТРОЕННЫЕ ПРЕСЕТЫ ФИЛЬТРОВ

# Определяем встроенные пресеты
BUILTIN_PRESETS: dict[str, dict[str, Any]] = {
    "default": {
        "description": "Базовые исключения для большинства проектов",
        "include_patterns": [],
        "exclude_patterns": DEFAULT_EXCLUDES.copy(),
        "token_estimate": "Средний размер проекта"
    },

    "aggressive": {
        "description": "Агрессивные исключения для экономии токенов",
        "include_patterns": [],
        "exclude_patterns": AGGRESSIVE_EXCLUDES.copy(),
        "token_estimate": "Значительная экономия токенов"
    },

    "code-only": {
        "description": "Только основной код без документации и тестов",
        "include_patterns": CODE_ONLY_INCLUDES.copy(),
        "exclude_patterns": AGGRESSIVE_EXCLUDES.copy(),
        "token_estimate": "Максимальная экономия токенов"
    },

    "python-project": {
        "description": "Оптимизировано для Python проектов",
        "include_patterns": ["*.py", "*.pyi", "*.pyx", "requirements*.txt", "setup.py", "pyproject.toml", "*.cfg", "*.ini"],
        "exclude_patterns": DEFAULT_EXCLUDES + [
            "__pycache__/**", "*.pyc", "*.pyo", "*.pyd",
            ".pytest_cache/**", ".mypy_cache/**", ".tox/**",
            "venv/**", ".venv/**", "env/**", ".env/**",
            "*.egg-info/**", "dist/**", "build/**"
        ],
        "token_estimate": "Оптимизировано для Python"
    },

    "web-app": {
        "description": "Веб-приложения (JS/TS + Python/PHP)",
        "include_patterns": ["*.js", "*.ts", "*.tsx", "*.jsx", "*.py", "*.php", "*.html", "*.css", "*.json", "*.md"],
        "exclude_patterns": DEFAULT_EXCLUDES + [
            "*.min.js", "*.min.css", "*.bundle.js", "*.chunk.js",
            "public/**", "assets/**", "uploads/**",
            "__pycache__/**", "*.pyc"
        ],
        "token_estimate": "Сбалансировано для веб-разработки"
    },

    "react-app": {
        "description": "React/Next.js приложения",
        "include_patterns": ["*.js", "*.ts", "*.tsx", "*.jsx", "*.json", "*.css", "*.scss", "*.md"],
        "exclude_patterns": DEFAULT_EXCLUDES + [
            "public/**", "assets/**", "*.min.js", "*.min.css",
            ".next/**", ".nuxt/**", ".output/**"
        ],
        "token_estimate": "Оптимизировано для React"
    },

    "electron-app": {
        "description": "Electron приложения с мульти-пакетной архитектурой",
        "include_patterns": [
            "packages/*/src/**/*.js", "packages/*/src/**/*.ts",
            "packages/*/**/*.tsx", "packages/*/**/*.jsx",
            "*.json", "*.md"
        ],
        "exclude_patterns": DEFAULT_EXCLUDES + [
            "packages/*/dist/**", "packages/*/build/**", "packages/*/out/**",
            "*.min.js", "*.min.css", "public/**", "certificates/**"
        ],
        "token_estimate": "Оптимизировано для Electron"
    }
}

# 🔧 КЛАСС ДЛЯ УПРАВЛЕНИЯ ПРЕСЕТАМИ

class FilterPresetManager:
    """Менеджер для работы с пресетами фильтров"""

    def __init__(self, presets_dir: str | None = None):
        """
        Инициализация менеджера пресетов

        Args:
            presets_dir: Директория для сохранения пользовательских пресетов
        """
        if presets_dir:
            self.presets_dir = Path(presets_dir)
        else:
            # По умолчанию сохраняем в домашнюю директорию пользователя
            self.presets_dir = Path.home() / ".neira-filters"

        # Создаем директорию если она не существует
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        self.presets_file = self.presets_dir / "presets.json"

        # Загружаем пользовательские пресеты
        self._user_presets = self._load_user_presets()

    def _load_user_presets(self) -> dict[str, dict[str, Any]]:
        """Загружает пользовательские пресеты из файла"""
        if not self.presets_file.exists():
            return {}

        try:
            with open(self.presets_file, encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Не удалось загрузить пользовательские пресеты: {e}")
            return {}

    def _save_user_presets(self) -> bool:
        """Сохраняет пользовательские пресеты в файл"""
        try:
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(self._user_presets, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Не удалось сохранить пресеты: {e}")
            return False

    def list_presets(self) -> dict[str, dict[str, Any]]:
        """
        Возвращает все доступные пресеты (встроенные + пользовательские)

        Returns:
            Dict: Словарь всех пресетов с их конфигурациями
        """
        all_presets = BUILTIN_PRESETS.copy()
        all_presets.update(self._user_presets)
        return all_presets

    def get_preset(self, name: str) -> dict[str, Any] | None:
        """
        Получает конфигурацию пресета по имени

        Args:
            name: Название пресета

        Returns:
            Dict: Конфигурация пресета или None если не найден
        """
        all_presets = self.list_presets()
        return all_presets.get(name)

    def save_preset(self, name: str, include_patterns: list[str],
                   exclude_patterns: list[str], description: str = "",
                   metadata: dict[str, Any] | None = None) -> bool:
        """
        Сохраняет новый пресет

        Args:
            name: Название пресета
            include_patterns: Паттерны для включения
            exclude_patterns: Паттерны для исключения
            description: Описание пресета
            metadata: Дополнительные метаданные

        Returns:
            bool: True если успешно сохранен
        """
        preset_config = {
            "description": description,
            "include_patterns": include_patterns,
            "exclude_patterns": exclude_patterns,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self._user_presets[name] = preset_config
        return self._save_user_presets()

    def delete_preset(self, name: str) -> bool:
        """
        Удалить пользовательский пресет

        Args:
            name: Имя пресета для удаления

        Returns:
            bool: True если пресет удален успешно
        """
        # Нельзя удалять встроенные пресеты
        if name in BUILTIN_PRESETS:
            logger.warning(f"Cannot delete builtin preset: {name}")
            return False

        if name in self._user_presets:
            del self._user_presets[name]
            self._save_user_presets()
            logger.info(f"Deleted preset: {name}")
            return True
        else:
            logger.warning(f"Preset not found for deletion: {name}")
            return False

    def handle_action(self, arguments: dict) -> str:
        """
        Обрабатывает действия с пресетами (создание, удаление, просмотр и т.д.)

        Args:
            arguments: Словарь с параметрами действия

        Returns:
            str: Результат обработки действия
        """
        action = arguments.get("action", "list")

        if action == "list":
            return self._handle_list_action()
        elif action == "create":
            return self._handle_create_action(arguments)
        elif action == "details":
            return self._handle_details_action(arguments)
        elif action == "delete":
            return self._handle_delete_action(arguments)
        elif action == "export":
            return self._handle_export_action(arguments)
        elif action == "import":
            return self._handle_import_action(arguments)
        else:
            return f"❌ Неизвестное действие: {action}. Доступные: list, create, details, delete, export, import"

    def _handle_list_action(self) -> str:
        """Обработка действия 'list' - просмотр всех пресетов"""
        presets = self.list_presets()

        response = "# 🎛️ Управление пресетами фильтров\n\n"
        response += f"## 📋 Доступные пресеты ({len(presets)})\n\n"

        for name, details in presets.items():
            # Определяем тип пресета
            if name in BUILTIN_PRESETS:
                preset_type = "🏗️ Встроенный"
            else:
                preset_type = "👤 Пользовательский"

            description = details.get("description", "Без описания")
            response += f"### {preset_type}: `{name}`\n"
            response += f"**Описание:** {description}\n\n"

        # Инструкции по использованию
        response += "## 🚀 Как использовать пресеты\n\n"
        response += "**Загрузка пресета:**\n"
        response += "```json\n"
        response += '{"preset_name": "python-project"}\n'
        response += "```\n\n"

        response += "**Создание пресета:**\n"
        response += "```json\n"
        response += '{\n  "action": "create",\n  "name": "my-preset",\n  "include_patterns": ["*.py", "*.md"],\n  "exclude_patterns": ["tests/**"],\n  "description": "Мой пресет"\n}\n'
        response += "```\n\n"

        return response

    def _handle_create_action(self, arguments: dict) -> str:
        """Обработка действия 'create' - создание нового пресета"""
        name = arguments.get("name")
        include_patterns = arguments.get("include_patterns", [])
        exclude_patterns = arguments.get("exclude_patterns", [])
        description = arguments.get("description", "")

        if not name:
            return "❌ Ошибка: необходимо указать 'name' для создания пресета"

        success = self.save_preset(name, include_patterns, exclude_patterns, description)

        if success:
            response = f"✅ Пресет '{name}' успешно создан!\n\n"
            response += f"**Описание:** {description}\n"
            response += f"**Include паттерны:** {include_patterns}\n"
            response += f"**Exclude паттерны:** {exclude_patterns}\n"
        else:
            response = f"❌ Ошибка создания пресета '{name}'"

        return response

    def _handle_details_action(self, arguments: dict) -> str:
        """Обработка действия 'details' - подробная информация о пресете"""
        name = arguments.get("name")
        if not name:
            return "❌ Ошибка: необходимо указать 'name' для получения деталей"

        details = self.get_preset(name)
        if not details:
            return f"❌ Пресет '{name}' не найден"

        response = f"# 🔍 Детали пресета: `{name}`\n\n"
        response += f"**Описание:** {details['description']}\n\n"

        if details['include_patterns']:
            response += "## ✅ Include patterns:\n"
            for pattern in details['include_patterns']:
                response += f"- `{pattern}`\n"
            response += "\n"

        if details['exclude_patterns']:
            response += "## ❌ Exclude patterns:\n"
            for pattern in details['exclude_patterns']:
                response += f"- `{pattern}`\n"
            response += "\n"

        # Метаданные если есть
        if 'created_at' in details:
            response += f"**Создан:** {details['created_at']}\n"
        if 'metadata' in details and details['metadata']:
            response += f"**Метаданные:** {details['metadata']}\n"

        return response

    def _handle_delete_action(self, arguments: dict) -> str:
        """Обработка действия 'delete' - удаление пресета"""
        name = arguments.get("name")
        if not name:
            return "❌ Ошибка: необходимо указать 'name' для удаления"

        success = self.delete_preset(name)

        if success:
            return f"✅ Пресет '{name}' успешно удален"
        else:
            return f"❌ Ошибка удаления пресета '{name}' (возможно, это встроенный пресет или он не существует)"

    def _handle_export_action(self, arguments: dict) -> str:
        """Обработка действия 'export' - экспорт пресета"""
        name = arguments.get("name")
        file_path = arguments.get("file_path")

        if not name or not file_path:
            return "❌ Ошибка: необходимо указать 'name' и 'file_path' для экспорта"

        success = self.export_preset(name, file_path)

        if success:
            return f"✅ Пресет '{name}' экспортирован в {file_path}"
        else:
            return f"❌ Ошибка экспорта пресета '{name}'"

    def _handle_import_action(self, arguments: dict) -> str:
        """Обработка действия 'import' - импорт пресета"""
        file_path = arguments.get("file_path")

        if not file_path:
            return "❌ Ошибка: необходимо указать 'file_path' для импорта"

        imported_name = self.import_preset(file_path)

        if imported_name:
            return f"✅ Пресет '{imported_name}' успешно импортирован из {file_path}"
        else:
            return f"❌ Ошибка импорта пресета из {file_path}"

    def export_preset(self, name: str, file_path: str) -> bool:
        """
        Экспортирует пресет в отдельный JSON файл

        Args:
            name: Название пресета
            file_path: Путь для сохранения

        Returns:
            bool: True если успешно экспортирован
        """
        preset = self.get_preset(name)
        if not preset:
            return False

        # БЕЗОПАСНОСТЬ: Проверяем что file_path находится в разрешенной зоне
        try:
            file_path_resolved = Path(file_path).resolve()
            # Разрешаем только в поддиректории presets/ или в текущей директории проекта
            allowed_dirs = [
                Path.cwd().resolve(),  # Текущая директория
                Path.cwd().resolve() / "presets",  # Поддиректория presets
                Path(self.presets_dir).resolve() if self.presets_dir else None
            ]
            allowed_dirs = [d for d in allowed_dirs if d is not None]

            # Используем pathlib.Path.is_relative_to() для более безопасной проверки пути
            is_allowed = any(
                file_path_resolved.is_relative_to(allowed)
                for allowed in allowed_dirs
            )

            if not is_allowed:
                logger.error(f"Небезопасный путь для экспорта: {file_path}")
                return False

        except Exception as e:
            logger.error(f"Ошибка проверки пути: {e}")
            return False

        try:
            export_data = {
                "preset_name": name,
                "preset_config": preset,
                "exported_at": datetime.now().isoformat(),
                "neira_version": "1.0"
            }

            # Создаем директорию если не существует
            file_path_resolved.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path_resolved, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Ошибка экспорта пресета: {e}")
            return False

# 🏭 ПОЛУЧЕНИЕ МЕНЕДЖЕРА ЧЕРЕЗ DI КОНТЕЙНЕР

def get_preset_manager() -> FilterPresetManager:
    """
    Получить экземпляр менеджера пресетов

    АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: Создаем экземпляр напрямую вместо DI-контейнера
    """
    return FilterPresetManager()

# 🔧 ОБНОВЛЕННЫЕ ФУНКЦИИ ДЛЯ ОБРАТНОЙ СОВМЕСТИМОСТИ

def get_default_excludes() -> list[str]:
    """Возвращает базовые исключения для большинства случаев."""
    return DEFAULT_EXCLUDES.copy()

def get_aggressive_excludes() -> list[str]:
    """Возвращает агрессивные исключения для экономии токенов."""
    return AGGRESSIVE_EXCLUDES.copy()

def get_code_only_patterns() -> tuple[list[str], list[str]]:
    """Возвращает паттерны для анализа только кода (includes, excludes)."""
    return CODE_ONLY_INCLUDES.copy(), AGGRESSIVE_EXCLUDES.copy()

# 🎯 НОВЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С ПРЕСЕТАМИ

def load_preset(name: str) -> tuple[list[str], list[str]] | None:
    """
    Загружает пресет по имени

    Args:
        name: Название пресета

    Returns:
        Tuple: (include_patterns, exclude_patterns) или None если не найден
    """
    manager = get_preset_manager()
    preset = manager.get_preset(name)

    if preset:
        return preset["include_patterns"], preset["exclude_patterns"]
    return None

def save_preset(name: str, include_patterns: list[str], exclude_patterns: list[str],
               description: str = "", **kwargs) -> bool:
    """
    Сохраняет новый пресет

    Args:
        name: Название пресета
        include_patterns: Паттерны для включения
        exclude_patterns: Паттерны для исключения
        description: Описание пресета
        **kwargs: Дополнительные метаданные

    Returns:
        bool: True если успешно сохранен
    """
    manager = get_preset_manager()
    return manager.save_preset(name, include_patterns, exclude_patterns, description, kwargs)

def list_available_presets() -> dict[str, str]:
    """
    Возвращает список всех доступных пресетов с описаниями

    Returns:
        Dict: {preset_name: description}
    """
    manager = get_preset_manager()
    presets = manager.list_presets()
    return {name: config["description"] for name, config in presets.items()}

def get_preset_details(name: str) -> dict[str, Any] | None:
    """
    Получает полную информацию о пресете

    Args:
        name: Название пресета

    Returns:
        Dict: Полная конфигурация пресета
    """
    manager = get_preset_manager()
    return manager.get_preset(name)

def resolve_patterns_with_preset(
    preset_name: str | None,
    include_patterns: list[str],
    exclude_patterns: list[str],
    merge_with_preset: bool = False
) -> tuple[list[str], list[str]]:
    """
    ИСПРАВЛЕНИЕ: Единая функция разрешения паттернов с учетом пресетов

    Устраняет дублирование логики между ai_analyzer.py, context_generator.py и filter_setup_service.py

    Args:
        preset_name: Название пресета
        include_patterns: Пользовательские include паттерны
        exclude_patterns: Пользовательские exclude паттерны
        merge_with_preset: Объединять ли с пресетом (True) или заменить (False)

    Returns:
        Tuple[List[str], List[str]]: (final_include, final_exclude)
    """
    logger.info(f"Resolving patterns with preset: {preset_name}, merge: {merge_with_preset}")

    final_include = include_patterns.copy()
    final_exclude = exclude_patterns.copy()

    if preset_name:
        preset_patterns = load_preset(preset_name)
        if preset_patterns:
            preset_include, preset_exclude = preset_patterns

            if merge_with_preset:
                # Объединяем с пользовательскими паттернами, убираем дубликаты
                final_include = list(set(preset_include + include_patterns))
                final_exclude = list(set(preset_exclude + exclude_patterns))
                logger.info(f"Merged preset '{preset_name}' with custom patterns")
            else:
                # Заменяем пользовательские паттерны на пресет
                final_include = preset_include
                final_exclude = preset_exclude
                logger.info(f"Using preset '{preset_name}' patterns (replacement mode)")
        else:
            logger.warning(f"Preset '{preset_name}' not found, using custom patterns")

    logger.info(f"Final patterns - include: {len(final_include)}, exclude: {len(final_exclude)}")
    return final_include, final_exclude

def create_project_preset(project_path: str, include_patterns: list[str],
                         exclude_patterns: list[str],
                         estimated_tokens: int | None = None) -> str:
    """
    Создает пресет на основе конкретного проекта

    Args:
        project_path: Путь к проекту
        include_patterns: Успешные include паттерны
        exclude_patterns: Успешные exclude паттерны
        estimated_tokens: Примерное количество токенов

    Returns:
        str: Название созданного пресета
    """
    project_name = Path(project_path).name
    preset_name = f"project-{project_name}"

    description = f"Автоматически созданный пресет для проекта {project_name}"

    metadata = {
        "project_path": project_path,
        "estimated_tokens": estimated_tokens,
        "auto_generated": True
    }

    manager = get_preset_manager()
    manager.save_preset(preset_name, include_patterns, exclude_patterns, description, metadata)

    return preset_name


# 🚀 НОВЫЙ ФИЛЬТР: Quick Feature Add - Фильтрация по размеру файла
class FileSizeFilter:
    """
    Фильтр для исключения файлов, превышающих определенный размер

    Quick Feature Add: Позволяет исключать большие файлы из анализа,
    что улучшает производительность и снижает количество токенов.
    """

    def __init__(self, max_size_kb: int = MAX_FILE_SIZE_KB):
        """
        Инициализация фильтра размера файлов

        Args:
            max_size_kb: Максимальный размер файла в килобайтах
        """
        self.max_size_bytes = max_size_kb * 1024
        self.max_size_kb = max_size_kb
        self.logger = logging.getLogger(self.__class__.__name__)

    def should_exclude_file(self, file_path: Path) -> tuple[bool, str]:
        """
        Проверяет, нужно ли исключить файл из анализа по размеру

        Args:
            file_path: Путь к файлу для проверки

        Returns:
            Tuple[bool, str]: (True если исключить, причина исключения)
        """
        try:
            if not file_path.exists() or not file_path.is_file():
                return False, ""

            file_size = file_path.stat().st_size

            if file_size > self.max_size_bytes:
                size_mb = file_size / (1024 * 1024)
                reason = f"Файл слишком большой: {size_mb:.2f}MB (лимит: {self.max_size_kb}KB)"
                self.logger.debug(f"🚫 Исключен большой файл: {file_path} ({reason})")
                return True, reason

            return False, ""

        except Exception as e:
            self.logger.warning(f"⚠️ Не удалось проверить размер файла {file_path}: {e}")
            return False, ""

    def filter_file_list(self, file_paths: list[Path]) -> tuple[list[Path], list[str]]:
        """
        Фильтрует список файлов по размеру

        Args:
            file_paths: Список путей к файлам

        Returns:
            Tuple[List[Path], List[str]]: (Оставшиеся файлы, Исключенные файлы с причинами)
        """
        remaining_files = []
        excluded_files = []

        for file_path in file_paths:
            should_exclude, reason = self.should_exclude_file(file_path)

            if should_exclude:
                excluded_files.append(f"{file_path}: {reason}")
            else:
                remaining_files.append(file_path)

        if excluded_files:
            self.logger.info(f"🚫 Исключено {len(excluded_files)} больших файлов (>{self.max_size_kb}KB)")

        return remaining_files, excluded_files

    def get_stats(self, file_paths: list[Path]) -> dict[str, Any]:
        """
        Возвращает статистику по размерам файлов

        Args:
            file_paths: Список файлов для анализа

        Returns:
            Dict со статистикой
        """
        stats = {
            "total_files": len(file_paths),
            "large_files_count": 0,
            "total_size_mb": 0.0,
            "large_files_size_mb": 0.0,
            "max_file_size_mb": 0.0,
            "largest_file": None
        }

        for file_path in file_paths:
            try:
                if file_path.exists() and file_path.is_file():
                    size = file_path.stat().st_size
                    size_mb = size / (1024 * 1024)

                    stats["total_size_mb"] += size_mb

                    if size > self.max_size_bytes:
                        stats["large_files_count"] += 1
                        stats["large_files_size_mb"] += size_mb

                    if size_mb > stats["max_file_size_mb"]:
                        stats["max_file_size_mb"] = size_mb
                        stats["largest_file"] = str(file_path)

            except Exception as e:
                self.logger.warning(f"⚠️ Ошибка при анализе размера {file_path}: {e}")

        return stats


def create_file_size_filter(max_size_kb: int = MAX_FILE_SIZE_KB) -> FileSizeFilter:
    """
    Factory функция для создания фильтра размера файлов

    Args:
        max_size_kb: Максимальный размер файла в килобайтах

    Returns:
        FileSizeFilter: Настроенный фильтр
    """
    return FileSizeFilter(max_size_kb=max_size_kb)
