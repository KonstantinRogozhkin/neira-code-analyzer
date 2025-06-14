"""
Filter Setup Service - выделенный сервис для настройки фильтров проекта

ИСПРАВЛЕНИЕ: Рефакторинг context_generator.py для решения нарушения принципа единственной ответственности (SRP).
Метод set_filters был перегружен и выполнял слишком много задач.

Теперь FilterSetupService отвечает только за:
- Анализ структуры проекта
- Автоопределение типа проекта
- Настройку и сохранение .neira конфигурации
- Генерацию отчетов о настройке фильтров
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class FilterSetupResult:
    """Результат настройки фильтров"""
    success: bool
    detected_preset: str | None
    final_include_patterns: list[str]
    final_exclude_patterns: list[str]
    neira_config_path: str | None
    report_message: str
    error_message: str | None = None

class FilterSetupService:
    """
    Сервис для автоматической настройки оптимальных фильтров проекта

    Отвечает исключительно за настройку фильтров, без генерации контекста
    или других ответственностей, которые были в context_generator.
    """

    def __init__(self):
        """Инициализация сервиса настройки фильтров"""
        pass

    async def setup_project_filters(
        self,
        path: str = ".",
        preset_name: str | None = None,
        include_patterns: list[str] = None,
        exclude_patterns: list[str] = None,
        merge_with_preset: bool = False,
        encoding: str = "cl100k"
    ) -> FilterSetupResult:
        """
        Основной метод настройки фильтров для проекта

        Args:
            path: Путь к проекту
            preset_name: Название пресета (если не указан, автоопределяется)
            include_patterns: Пользовательские include паттерны
            exclude_patterns: Пользовательские exclude паттерны
            merge_with_preset: Объединять ли с пресетом
            encoding: Кодировка для подсчета токенов

        Returns:
            FilterSetupResult: Результат настройки фильтров
        """
        if include_patterns is None:
            include_patterns = []
        if exclude_patterns is None:
            exclude_patterns = []

        logger.info(f"Setting up optimal filters for {path}")

        try:
            # 1. Автоопределение типа проекта, если пресет не указан
            detected_preset = None
            if not preset_name and not include_patterns:
                detected_preset = self._detect_project_type(path)
                if detected_preset:
                    preset_name = detected_preset
                    logger.info(f"Auto-detected project type: {preset_name}")

            # 2. Разрешение паттернов с учетом пресетов
            final_include, final_exclude = self._resolve_patterns(
                preset_name, include_patterns, exclude_patterns, merge_with_preset
            )

            # 3. Сохранение конфигурации в .neira
            config_path = self._save_neira_config(
                path, preset_name, final_include, final_exclude, encoding
            )

            # 4. Генерация отчета
            report = self._generate_setup_report(
                path, detected_preset, preset_name, final_include, final_exclude, config_path
            )

            return FilterSetupResult(
                success=True,
                detected_preset=detected_preset,
                final_include_patterns=final_include,
                final_exclude_patterns=final_exclude,
                neira_config_path=config_path,
                report_message=report
            )

        except Exception as e:
            error_msg = f"❌ Ошибка настройки фильтров: {str(e)}"
            logger.error(error_msg)
            return FilterSetupResult(
                success=False,
                detected_preset=None,
                final_include_patterns=[],
                final_exclude_patterns=[],
                neira_config_path=None,
                report_message="",
                error_message=error_msg
            )

    def _detect_project_type(self, path: str) -> str | None:
        """
        Автоматическое определение типа проекта по структуре файлов

        Args:
            path: Путь к проекту

        Returns:
            Optional[str]: Название подходящего пресета или None
        """
        project_path = Path(path)

        if not project_path.exists():
            logger.warning(f"Path does not exist: {path}")
            return None

        # Собираем информацию о проекте
        files = []
        dirs = []

        try:
            for item in project_path.iterdir():
                if item.is_file():
                    files.append(item.name.lower())
                elif item.is_dir():
                    dirs.append(item.name.lower())
        except PermissionError:
            logger.warning(f"Permission denied for {path}")
            return None

        # Логика определения типа проекта

        # Python проект
        if any(f in files for f in ['setup.py', 'pyproject.toml', 'requirements.txt']) or \
           any(d in dirs for d in ['venv', '.venv', '__pycache__']):
            return "python-project"

        # React проект (Next.js, CRA, Vite)
        if 'package.json' in files:
            package_json_path = project_path / 'package.json'
            try:
                with open(package_json_path, encoding='utf-8') as f:
                    package_data = json.load(f)

                dependencies = {}
                dependencies.update(package_data.get('dependencies', {}))
                dependencies.update(package_data.get('devDependencies', {}))

                # React/Next.js
                if any(dep in dependencies for dep in ['react', 'next', '@remix-run']):
                    return "react-app"

                # Electron
                if 'electron' in dependencies:
                    return "electron-app"

                # Обычное веб-приложение
                return "web-app"

            except (OSError, json.JSONDecodeError):
                # Если не можем прочитать package.json, но он есть - веб-проект
                return "web-app"

        # Проект с множеством документации
        md_files = [f for f in files if f.endswith('.md')]
        if len(md_files) > 10:
            return "aggressive"  # Много документации - нужны агрессивные фильтры

        # По умолчанию - базовые фильтры
        return "default"

    def _resolve_patterns(
        self,
        preset_name: str | None,
        include_patterns: list[str],
        exclude_patterns: list[str],
        merge_with_preset: bool
    ) -> tuple[list[str], list[str]]:
        """
        ИСПРАВЛЕНИЕ: Используем централизованную функцию разрешения пресетов
        """
        from .filters import resolve_patterns_with_preset
        return resolve_patterns_with_preset(preset_name, include_patterns, exclude_patterns, merge_with_preset)

    def _save_neira_config(
        self,
        path: str,
        preset_name: str | None,
        include_patterns: list[str],
        exclude_patterns: list[str],
        encoding: str
    ) -> str:
        """
        Сохраняет конфигурацию в .neira файл или .neira/config.json

        Args:
            path: Путь к проекту
            preset_name: Использованный пресет
            include_patterns: Финальные include паттерны
            exclude_patterns: Финальные exclude паттерны
            encoding: Кодировка

        Returns:
            str: Путь к сохраненному файлу конфигурации
        """
        config_data = {
            "project_path": str(Path(path).resolve()),
            "setup_date": "auto-generated",
            "preset_used": preset_name,
            "include_patterns": include_patterns,
            "exclude_patterns": exclude_patterns,
            "encoding": encoding,
            "neira_version": "1.0",
            "auto_generated": True
        }

        project_path = Path(path)
        neira_path = project_path / ".neira"

        # ИСПРАВЛЕНИЕ: Проверяем, что .neira - директория или файл
        if neira_path.exists() and neira_path.is_dir():
            # Если .neira это директория, сохраняем в config.json внутри
            config_path = neira_path / "config.json"
            logger.info("📁 .neira is directory, saving to config.json inside")
        else:
            # Если .neira файл или не существует, используем как файл
            config_path = neira_path

        # Создаем директорию если нужно
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Saved .neira config to {config_path}")
        return str(config_path)

    def _generate_setup_report(
        self,
        path: str,
        detected_preset: str | None,
        used_preset: str | None,
        include_patterns: list[str],
        exclude_patterns: list[str],
        config_path: str
    ) -> str:
        """
        Генерирует отчет о настройке фильтров

        Args:
            path: Путь к проекту
            detected_preset: Автоопределенный пресет
            used_preset: Использованный пресет
            include_patterns: Финальные include паттерны
            exclude_patterns: Финальные exclude паттерны
            config_path: Путь к конфигурации

        Returns:
            str: Markdown отчет
        """
        report = "# 🎯 Настройка фильтров проекта\n\n"

        # Информация о проекте
        project_name = Path(path).name
        report += f"**📁 Проект:** `{project_name}`\n"
        report += f"**📂 Путь:** `{path}`\n\n"

        # Автоопределение
        if detected_preset:
            report += f"**🤖 Автоопределение:** {detected_preset}\n"

        if used_preset:
            report += f"**⚙️ Использованный пресет:** {used_preset}\n"

        report += "\n"

        # Финальные паттерны
        if include_patterns:
            report += "## ✅ Include patterns\n\n"
            for pattern in include_patterns:
                report += f"- `{pattern}`\n"
            report += "\n"
        else:
            report += "## ✅ Include patterns: *(все файлы)*\n\n"

        if exclude_patterns:
            report += "## ❌ Exclude patterns\n\n"
            for pattern in exclude_patterns:
                report += f"- `{pattern}`\n"
            report += "\n"
        else:
            report += "## ❌ Exclude patterns: *(нет исключений)*\n\n"

        # Конфигурация
        report += "## 💾 Сохраненная конфигурация\n\n"
        report += f"**📁 Файл:** `{config_path}`\n"
        report += "**🔄 Переиспользование:** Конфигурация автоматически применится для будущих анализов этого проекта\n\n"

        # Следующие шаги
        report += "## 🚀 Следующие шаги\n\n"
        report += "1. **Анализ кода:** Используйте `get_analyze` для полного AI-анализа\n"
        report += "2. **Генерация контекста:** Используйте `get_context` для создания промптов\n"
        report += "3. **Настройка:** При необходимости измените паттерны в `.neira` файле\n\n"

        return report
