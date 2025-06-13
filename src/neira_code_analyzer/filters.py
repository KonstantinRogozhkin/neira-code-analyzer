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
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Базовые исключения - применяются везде для разумного анализа
DEFAULT_EXCLUDES: List[str] = [
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
    
    # Quick Performance Win: дополнительные кэши JS инструментов
    "/.nuxt/", ".nuxt/**", 
    "/.vite/", ".vite/**",
    "/.rollup.cache/", ".rollup.cache/**",
]

# Агрессивные исключения для code review (когда нужно сократить токены)
AGGRESSIVE_EXCLUDES: List[str] = DEFAULT_EXCLUDES + [
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
CODE_ONLY_INCLUDES: List[str] = [
    "*.py", "*.js", "*.ts", "*.tsx", "*.jsx", "*.java", "*.cpp", "*.c", "*.h", "*.go", "*.rs", "*.php"
]

# 🎯 ВСТРОЕННЫЕ ПРЕСЕТЫ ФИЛЬТРОВ

# Определяем встроенные пресеты
BUILTIN_PRESETS: Dict[str, Dict[str, Any]] = {
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
    
    def __init__(self, presets_dir: Optional[str] = None):
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
    
    def _load_user_presets(self) -> Dict[str, Dict[str, Any]]:
        """Загружает пользовательские пресеты из файла"""
        if not self.presets_file.exists():
            return {}
        
        try:
            with open(self.presets_file, 'r', encoding='utf-8') as f:
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
    
    def list_presets(self) -> Dict[str, Dict[str, Any]]:
        """
        Возвращает все доступные пресеты (встроенные + пользовательские)
        
        Returns:
            Dict: Словарь всех пресетов с их конфигурациями
        """
        all_presets = BUILTIN_PRESETS.copy()
        all_presets.update(self._user_presets)
        return all_presets
    
    def get_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Получает конфигурацию пресета по имени
        
        Args:
            name: Название пресета
            
        Returns:
            Dict: Конфигурация пресета или None если не найден
        """
        all_presets = self.list_presets()
        return all_presets.get(name)
    
    def save_preset(self, name: str, include_patterns: List[str], 
                   exclude_patterns: List[str], description: str = "",
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
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
        Удаляет пользовательский пресет
        
        Args:
            name: Название пресета для удаления
            
        Returns:
            bool: True если успешно удален
        """
        # Нельзя удалять встроенные пресеты
        if name in BUILTIN_PRESETS:
            logger.warning(f"Нельзя удалить встроенный пресет: {name}")
            return False
        
        if name in self._user_presets:
            del self._user_presets[name]
            return self._save_user_presets()
        
        return False
    
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
            
            is_allowed = any(
                str(file_path_resolved).startswith(str(allowed)) 
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
    
    def import_preset(self, file_path: str) -> Optional[str]:
        """
        Импортирует пресет из JSON файла
        
        Args:
            file_path: Путь к файлу с пресетом
            
        Returns:
            str: Название импортированного пресета или None при ошибке
        """
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
            
            is_allowed = any(
                str(file_path_resolved).startswith(str(allowed)) 
                for allowed in allowed_dirs
            )
            
            if not is_allowed:
                logger.error(f"Небезопасный путь для импорта: {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка проверки пути: {e}")
            return None
        
        try:
            with open(file_path_resolved, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            preset_name = data.get("preset_name")
            preset_config = data.get("preset_config")
            
            if not preset_name or not preset_config:
                logger.error("Неверный формат файла пресета")
                return None
            
            # БЕЗОПАСНОСТЬ: Проверяем структуру пресета
            required_keys = {"include_patterns", "exclude_patterns", "description"}
            if not all(key in preset_config for key in required_keys):
                logger.error("Неполная структура пресета")
                return None
            
            # Добавляем метаданные об импорте
            preset_config["metadata"] = preset_config.get("metadata", {})
            preset_config["metadata"]["imported_at"] = datetime.now().isoformat()
            preset_config["metadata"]["imported_from"] = str(file_path_resolved)
            
            self._user_presets[preset_name] = preset_config
            
            if self._save_user_presets():
                return preset_name
            
        except Exception as e:
            logger.error(f"Ошибка импорта пресета: {e}")
        
        return None

# 🏭 ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР МЕНЕДЖЕРА
_preset_manager = None

def get_preset_manager() -> FilterPresetManager:
    """Получить глобальный экземпляр менеджера пресетов"""
    global _preset_manager
    if _preset_manager is None:
        _preset_manager = FilterPresetManager()
    return _preset_manager

# 🔧 ОБНОВЛЕННЫЕ ФУНКЦИИ ДЛЯ ОБРАТНОЙ СОВМЕСТИМОСТИ

def get_default_excludes() -> List[str]:
    """Возвращает базовые исключения для большинства случаев."""
    return DEFAULT_EXCLUDES.copy()

def get_aggressive_excludes() -> List[str]:
    """Возвращает агрессивные исключения для экономии токенов."""
    return AGGRESSIVE_EXCLUDES.copy()

def get_code_only_patterns() -> Tuple[List[str], List[str]]:
    """Возвращает паттерны для анализа только кода (includes, excludes)."""
    return CODE_ONLY_INCLUDES.copy(), AGGRESSIVE_EXCLUDES.copy()

# 🎯 НОВЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С ПРЕСЕТАМИ

def load_preset(name: str) -> Optional[Tuple[List[str], List[str]]]:
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

def save_preset(name: str, include_patterns: List[str], exclude_patterns: List[str],
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

def list_available_presets() -> Dict[str, str]:
    """
    Возвращает список всех доступных пресетов с описаниями
    
    Returns:
        Dict: {preset_name: description}
    """
    manager = get_preset_manager()
    presets = manager.list_presets()
    return {name: config["description"] for name, config in presets.items()}

def get_preset_details(name: str) -> Optional[Dict[str, Any]]:
    """
    Получает полную информацию о пресете
    
    Args:
        name: Название пресета
        
    Returns:
        Dict: Полная конфигурация пресета
    """
    manager = get_preset_manager()
    return manager.get_preset(name)

def create_project_preset(project_path: str, include_patterns: List[str], 
                         exclude_patterns: List[str], 
                         estimated_tokens: Optional[int] = None) -> str:
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