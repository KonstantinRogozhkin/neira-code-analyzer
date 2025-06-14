"""
Neira Configuration Loader - автоматическая загрузка конфигурации проектов

Этот модуль отвечает за загрузку и применение сохраненных настроек проекта
из файлов .neira и .neiraignore в корне проекта.

Поддерживаемые конфигурации:
- .neira - JSON файл с полными настройками проекта
- .neira/ папка с отдельными конфигурационными файлами
- .neiraignore - простой файл с паттернами исключений (аналог .gitignore)
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class NeiraConfig:
    """Класс для хранения загруженной конфигурации Neira"""
    project_path: str
    include_patterns: list[str]
    exclude_patterns: list[str]
    preset_used: str | None = None
    encoding: str = "cl100k"
    template_name: str | None = None
    auto_detected: bool = False
    neira_version: str = "1.0"
    config_source: str = "unknown"  # .neira, .neira/, .neiraignore

    def __post_init__(self):
        """Валидация после инициализации"""
        if not isinstance(self.include_patterns, list):
            self.include_patterns = []
        if not isinstance(self.exclude_patterns, list):
            self.exclude_patterns = []

class NeiraConfigLoader:
    """Загрузчик конфигурации Neira проектов"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def load_project_config(self, project_path: str) -> NeiraConfig | None:
        """
        Загружает конфигурацию проекта из различных источников

        Приоритет загрузки:
        1. .neira (JSON файл) - наивысший приоритет
        2. .neira/ (папка с файлами)
        3. .neiraignore - простые исключения

        Args:
            project_path: Путь к проекту

        Returns:
            NeiraConfig или None если конфигурация не найдена
        """
        path = Path(project_path).resolve()

        # 1. Пробуем загрузить .neira JSON файл
        neira_file = path / ".neira"
        if neira_file.exists() and neira_file.is_file():
            config = self._load_neira_json_file(neira_file, project_path)
            if config:
                self.logger.info(f"✅ Загружена конфигурация из .neira файла: {neira_file}")
                return config

        # 2. Пробуем загрузить .neira папку
        neira_dir = path / ".neira"
        if neira_dir.exists() and neira_dir.is_dir():
            config = self._load_neira_directory(neira_dir, project_path)
            if config:
                self.logger.info(f"✅ Загружена конфигурация из .neira/ папки: {neira_dir}")
                return config

        # 3. Пробуем загрузить .neiraignore файл
        neiraignore_file = path / ".neiraignore"
        if neiraignore_file.exists():
            config = self._load_neiraignore_file(neiraignore_file, project_path)
            if config:
                self.logger.info(f"✅ Загружена конфигурация из .neiraignore: {neiraignore_file}")
                return config

        self.logger.debug(f"Конфигурация Neira не найдена в проекте: {project_path}")
        return None

    def _load_neira_json_file(self, neira_file: Path, project_path: str) -> NeiraConfig | None:
        """Загружает конфигурацию из .neira JSON файла"""
        try:
            with open(neira_file, encoding='utf-8') as f:
                data = json.load(f)

            # Проверяем обязательные поля
            if not isinstance(data, dict):
                self.logger.warning(f"Неверный формат .neira файла: {neira_file}")
                return None

            return NeiraConfig(
                project_path=project_path,
                include_patterns=data.get("include_patterns", []),
                exclude_patterns=data.get("exclude_patterns", []),
                preset_used=data.get("preset_used"),
                encoding=data.get("encoding", "cl100k"),
                template_name=data.get("template_name"),
                auto_detected=data.get("auto_detected", False),
                neira_version=data.get("neira_version", "1.0"),
                config_source=".neira"
            )

        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка парсинга .neira файла {neira_file}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Ошибка загрузки .neira файла {neira_file}: {e}")
            return None

    def _load_neira_directory(self, neira_dir: Path, project_path: str) -> NeiraConfig | None:
        """Загружает конфигурацию из .neira/ папки"""
        try:
            include_patterns = []
            exclude_patterns = []
            preset_used = None
            encoding = "cl100k"
            template_name = None

            # Загружаем отдельные файлы конфигурации
            config_file = neira_dir / "config.json"
            if config_file.exists():
                with open(config_file, encoding='utf-8') as f:
                    config_data = json.load(f)

                include_patterns = config_data.get("include_patterns", [])
                exclude_patterns = config_data.get("exclude_patterns", [])
                preset_used = config_data.get("preset_used")
                encoding = config_data.get("encoding", "cl100k")
                template_name = config_data.get("template_name")

            # Загружаем include паттерны из отдельного файла
            include_file = neira_dir / "include.txt"
            if include_file.exists():
                include_patterns.extend(self._read_patterns_file(include_file))

            # Загружаем exclude паттерны из отдельного файла
            exclude_file = neira_dir / "exclude.txt"
            if exclude_file.exists():
                exclude_patterns.extend(self._read_patterns_file(exclude_file))

            # Загружаем из .neiraignore внутри папки
            ignore_file = neira_dir / ".neiraignore"
            if ignore_file.exists():
                exclude_patterns.extend(self._read_patterns_file(ignore_file))

            if include_patterns or exclude_patterns:
                return NeiraConfig(
                    project_path=project_path,
                    include_patterns=include_patterns,
                    exclude_patterns=exclude_patterns,
                    preset_used=preset_used,
                    encoding=encoding,
                    template_name=template_name,
                    config_source=".neira/"
                )

            return None

        except Exception as e:
            self.logger.error(f"Ошибка загрузки .neira/ папки {neira_dir}: {e}")
            return None

    def _load_neiraignore_file(self, neiraignore_file: Path, project_path: str) -> NeiraConfig | None:
        """Загружает конфигурацию из .neiraignore файла (аналог .gitignore)"""
        try:
            exclude_patterns = self._read_patterns_file(neiraignore_file)

            if exclude_patterns:
                return NeiraConfig(
                    project_path=project_path,
                    include_patterns=[],
                    exclude_patterns=exclude_patterns,
                    config_source=".neiraignore"
                )

            return None

        except Exception as e:
            self.logger.error(f"Ошибка загрузки .neiraignore файла {neiraignore_file}: {e}")
            return None

    def _read_patterns_file(self, patterns_file: Path) -> list[str]:
        """Читает паттерны из текстового файла (одна строка = один паттерн)"""
        patterns = []

        try:
            with open(patterns_file, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Пропускаем пустые строки и комментарии
                    if line and not line.startswith('#'):
                        patterns.append(line)

        except Exception as e:
            self.logger.error(f"Ошибка чтения файла паттернов {patterns_file}: {e}")

        return patterns

    def auto_apply_config(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Автоматически применяет сохраненную конфигурацию проекта к аргументам

        Если в проекте есть .neira конфигурация, автоматически загружает и применяет ее,
        если пользователь явно не указал свои фильтры.

        Args:
            arguments: Словарь аргументов MCP инструмента

        Returns:
            Dict: Обновленные аргументы с применененной конфигурацией
        """
        project_path = arguments.get("path", ".")

        # Загружаем конфигурацию проекта
        config = self.load_project_config(project_path)
        if not config:
            return arguments

        # Создаем копию аргументов
        updated_args = arguments.copy()

        # Применяем конфигурацию, если пользователь не указал свои настройки
        if not arguments.get("include_patterns") and config.include_patterns:
            updated_args["include_patterns"] = config.include_patterns
            self.logger.info(f"📥 Применены include паттерны из {config.config_source}: {len(config.include_patterns)} паттернов")

        if not arguments.get("exclude_patterns") and config.exclude_patterns:
            updated_args["exclude_patterns"] = config.exclude_patterns
            self.logger.info(f"📥 Применены exclude паттерны из {config.config_source}: {len(config.exclude_patterns)} паттернов")

        if not arguments.get("preset_name") and config.preset_used:
            updated_args["preset_name"] = config.preset_used
            self.logger.info(f"📥 Применен пресет из {config.config_source}: {config.preset_used}")

        if not arguments.get("encoding") and config.encoding:
            updated_args["encoding"] = config.encoding

        if not arguments.get("template_name") and config.template_name:
            updated_args["template_name"] = config.template_name
            self.logger.info(f"📥 Применен шаблон из {config.config_source}: {config.template_name}")

        return updated_args

    def get_config_info(self, project_path: str) -> dict[str, Any]:
        """
        Получает информацию о конфигурации проекта без загрузки

        Args:
            project_path: Путь к проекту

        Returns:
            Dict: Информация о найденной конфигурации
        """
        path = Path(project_path).resolve()

        config_info = {
            "has_config": False,
            "config_files": [],
            "config_source": None
        }

        # Проверяем .neira файл
        neira_file = path / ".neira"
        if neira_file.exists() and neira_file.is_file():
            config_info["has_config"] = True
            config_info["config_files"].append(".neira")
            config_info["config_source"] = ".neira"

        # Проверяем .neira папку
        neira_dir = path / ".neira"
        if neira_dir.exists() and neira_dir.is_dir():
            config_info["has_config"] = True
            config_info["config_files"].append(".neira/")
            if not config_info["config_source"]:
                config_info["config_source"] = ".neira/"

        # Проверяем .neiraignore
        neiraignore_file = path / ".neiraignore"
        if neiraignore_file.exists():
            config_info["has_config"] = True
            config_info["config_files"].append(".neiraignore")
            if not config_info["config_source"]:
                config_info["config_source"] = ".neiraignore"

        return config_info

# Глобальный экземпляр загрузчика конфигурации
_config_loader = None

def get_config_loader() -> NeiraConfigLoader:
    """Получает глобальный экземпляр загрузчика конфигурации"""
    global _config_loader
    if _config_loader is None:
        _config_loader = NeiraConfigLoader()
    return _config_loader
