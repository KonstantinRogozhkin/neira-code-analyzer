"""
Генератор контекста для Neira Code Analyzer

Централизованная логика генерации контекста из кодовых баз.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.types import TextContent

# Убираем прямые импорты глобальных экземпляров для устранения циклических зависимостей
# Используем DI контейнер для получения зависимостей

logger = logging.getLogger(__name__)

# 🎯 Константы для алгоритма оптимизации (устранение "магических чисел")
LARGE_PROJECT_TOKEN_THRESHOLD = 500000  # Порог для определения большого проекта
HEAVY_FILE_TYPE_PERCENTAGE_THRESHOLD = 20  # Процент токенов для признания типа файла "тяжелым"
HEAVY_FILE_ABSOLUTE_TOKEN_THRESHOLD = 50000  # Абсолютный порог токенов для файла

# ИСПРАВЛЕНО: Лимиты безопасности для предотвращения DoS атак
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB максимальный размер файла
MAX_FILES_COUNT = 10000  # Максимальное количество файлов для обработки
MAX_TOTAL_SIZE_BYTES = 100 * 1024 * 1024  # 100MB максимальный общий размер

# 🚀 PERFORMANCE WIN: Предкомпилированные паттерны для избежания создания на каждый вызов
# Улучшенные паттерны включения по умолчанию
DEFAULT_INCLUDE_PATTERNS = [
    # Python
    '*.py', '*.pyi', '*.pyw',
    # JavaScript/TypeScript
    '*.js', '*.jsx', '*.ts', '*.tsx', '*.vue',
    # Web
    '*.html', '*.htm', '*.css', '*.scss', '*.sass', '*.less',
    # Конфигурация
    '*.json', '*.yaml', '*.yml', '*.toml', '*.ini', '*.cfg',
    # Документация
    '*.md', '*.rst', '*.txt',
    # Shell scripts
    '*.sh', '*.bash', '*.zsh', '*.fish',
    # Другие популярные языки
    '*.rs', '*.go', '*.java', '*.kt', '*.swift', '*.rb', '*.php',
    # Dockerfile и инфраструктура
    'Dockerfile*', '*.dockerfile', '*.env*',
    # Конфиг файлы без расширений
    'Makefile', 'CMakeLists.txt', 'requirements*.txt', 'package.json', 'pyproject.toml'
]

# Глобальные исключения для всех типов проектов (оптимизация производительности)
# ENHANCED_EXCLUDE_PATTERNS_BASE удален - используем централизованный источник из filters.py

@dataclass
class ContextConfig:
    """Конфигурация для генерации контекста - решает проблему множества параметров"""
    path: str = "."
    template_name: str | None = None
    custom_template: str | None = None
    preset_name: str | None = None
    include_patterns: list[str] = None
    exclude_patterns: list[str] = None
    merge_with_preset: bool = False
    save_as_preset: str | None = None
    include_priority: bool = False
    line_numbers: bool = True
    absolute_paths: bool = False
    full_directory_tree: bool = False
    code_blocks: bool = True
    follow_symlinks: bool = False
    include_hidden: bool = False
    encoding: str = "cl100k"
    save_to_file: str | None = None
    auto_analyze: bool = True

    def __post_init__(self):
        """Инициализация значений по умолчанию для списков"""
        if self.include_patterns is None:
            self.include_patterns = []
        if self.exclude_patterns is None:
            self.exclude_patterns = []

@dataclass
class AnalysisResult:
    """Структурированный результат анализа фильтров"""
    total_tokens: int
    total_files: int
    markdown_report: str
    file_stats: dict[str, Any] = None

    def __post_init__(self):
        if self.file_stats is None:
            self.file_stats = {}

class ContextGenerator:
    """Генерация контекста из кодовых баз"""

    def __init__(self):
        """
        Инициализация генератора контекста

        АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: ContextGenerator теперь создает свои зависимости напрямую
        вместо использования DI-контейнера. Это устраняет циклические зависимости.
        """
        logger.info("ContextGenerator initialized with direct dependencies")

        # Ленивая инициализация low-level зависимостей
        self._template_manager = None
        self._project_manager = None

    def _get_template_manager(self):
        """
        Ленивое создание TemplateManager

        АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: Создаем зависимость напрямую вместо DI-контейнера
        """
        if self._template_manager is None:
            from .template_manager import TemplateManager
            self._template_manager = TemplateManager()
        return self._template_manager

    def _get_project_manager(self):
        """
        Ленивое создание ProjectManager

        АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: Создаем зависимость напрямую вместо DI-контейнера
        """
        if self._project_manager is None:
            from .project_manager import ProjectManager
            self._project_manager = ProjectManager()
        return self._project_manager

    def generate_context(self, arguments: dict[str, Any]) -> tuple[str, str | None]:
        """
        Генерирует контекстные промпты из кодовых баз используя code2prompt-rs

        Args:
            arguments: Словарь с параметрами анализа

        Returns:
            tuple[str, Optional[str]]: (generated_content, saved_file_path)
        """
        # Создаем конфигурацию из аргументов для улучшения читаемости и поддержки
        config = ContextConfig(
            path=arguments.get("path", "."),
            template_name=arguments.get("template_name"),
            custom_template=arguments.get("template"),
            preset_name=arguments.get("preset_name"),
            include_patterns=arguments.get("include_patterns", []),
            exclude_patterns=arguments.get("exclude_patterns", []),
            merge_with_preset=arguments.get("merge_with_preset", False),
            save_as_preset=arguments.get("save_as_preset"),
            include_priority=arguments.get("include_priority", False),
            line_numbers=arguments.get("line_numbers", True),
            absolute_paths=arguments.get("absolute_paths", False),
            full_directory_tree=arguments.get("full_directory_tree", False),
            code_blocks=arguments.get("code_blocks", True),
            follow_symlinks=arguments.get("follow_symlinks", False),
            include_hidden=arguments.get("include_hidden", False),
            encoding=arguments.get("encoding", "cl100k"),
            save_to_file=arguments.get("save_to_file"),
            auto_analyze=arguments.get("auto_analyze", True)
        )

        # Обрабатываем пресеты если указаны
        final_include_patterns, final_exclude_patterns = self._resolve_preset_patterns(config)

        # Определяем какой шаблон использовать
        template = self._resolve_template(config.template_name, config.custom_template)
        if template is None and config.template_name:
            # Шаблон не найден
            template_manager = self._get_template_manager()
            available = template_manager.get_available_templates()
            raise ValueError(f"Template '{config.template_name}' not found. Available: {', '.join(available)}")

        logger.info(f"Getting context from {config.path} with include patterns: {config.include_patterns}, exclude patterns: {config.exclude_patterns}")

        # Инициализируем Code2Prompt с расширенными возможностями
        prompt = self._create_code2prompt(
            path=config.path,
            include_patterns=final_include_patterns,
            exclude_patterns=final_exclude_patterns,
            include_priority=config.include_priority,
            line_numbers=config.line_numbers,
            absolute_paths=config.absolute_paths,
            full_directory_tree=config.full_directory_tree,
            code_blocks=config.code_blocks,
            follow_symlinks=config.follow_symlinks,
            include_hidden=config.include_hidden,
        )

        # Генерируем промпт с указанным шаблоном и энкодингом
        result = prompt.generate(template=template, encoding=config.encoding)

        # Сохраняем как пресет если указано
        if config.save_as_preset:
            self._save_as_preset(config.save_as_preset, final_include_patterns, final_exclude_patterns, config.path, result.token_count)

        # Готовим ответ
        response = ""
        saved_file_path = None

        # Сохраняем в файл если указано
        if config.save_to_file:
            saved_file_path = self._save_context_to_file(
                result, config.path, config.save_to_file, config.template_name, config.custom_template,
                arguments, config.encoding
            )

            # Создаем ответ с информацией о сохранении
            response = self._create_save_response(
                saved_file_path, result.token_count, config.template_name,
                config.custom_template, config.encoding, config.path
            )
        else:
            # Возвращаем только контент без сохранения
            response = result.prompt

        return response, saved_file_path

    def _resolve_template(self, template_name: str | None,
                         custom_template: str | None) -> str | None:
        """
        Определить какой шаблон использовать

        Args:
            template_name: Название предопределенного шаблона
            custom_template: Пользовательский шаблон

        Returns:
            Optional[str]: Содержимое шаблона или None для стандартного
        """
        if template_name:
            # Загружаем предопределенный шаблон
            template_manager = self._get_template_manager()
            template = template_manager.load_template(template_name)
            if template is None:
                logger.error(f"Template '{template_name}' not found")
                return None
            logger.info(f"Loaded template: {template_name}")
            return template
        elif custom_template:
            # Используем пользовательский шаблон
            logger.info("Using custom template")
            return custom_template
        else:
            # Используем стандартный шаблон (None)
            logger.info("Using default template")
            return None

    def _resolve_preset_patterns(self, config: ContextConfig) -> tuple[list[str], list[str]]:
        """
        ИСПРАВЛЕНИЕ: Используем централизованную функцию разрешения пресетов
        """
        from .filters import resolve_patterns_with_preset
        return resolve_patterns_with_preset(
            config.preset_name,
            config.include_patterns,
            config.exclude_patterns,
            config.merge_with_preset
        )

    def _save_as_preset(self, preset_name: str, include_patterns: list[str],
                       exclude_patterns: list[str], project_path: str, token_count: int):
        """
        Сохраняет текущую конфигурацию как пресет

        Args:
            preset_name: Название пресета
            include_patterns: Включаемые паттерны
            exclude_patterns: Исключаемые паттерны
            project_path: Путь к проекту
            token_count: Количество токенов
        """
        from .filters import save_preset

        description = f"Пресет, созданный из проекта {Path(project_path).name} ({token_count:,} токенов)"

        success = save_preset(
            preset_name,
            include_patterns,
            exclude_patterns,
            description,
            project_path=project_path,
            token_count=token_count,
            created_from_context=True
        )

        if success:
            logger.info(f"Пресет '{preset_name}' успешно сохранен")
        else:
            logger.error(f"Не удалось сохранить пресет '{preset_name}'")

    def _save_context_to_file(self, result, path: str, save_to_file: str,
                             template_name: str | None, custom_template: str | None,
                             arguments: dict[str, Any], encoding: str) -> str:
        """
        Сохранить контекст в файл

        Returns:
            str: Путь к сохраненному файлу
        """
        # Получаем зависимости напрямую
        template_manager = self._get_template_manager()
        project_manager = self._get_project_manager()

        # Определяем тип файла
        file_type = template_manager.get_file_type_from_template(
            template_name if template_name else "code"
        )

        # Создаем версионированный путь
        save_path = project_manager.create_versioned_path(
            path, save_to_file, file_type
        )

        # Сохраняем основной файл контекста
        save_path.write_text(result.prompt, encoding='utf-8')
        saved_file_path = str(save_path)

        logger.info(f"Context saved to: {saved_file_path}")

        # Сохраняем информацию о примененных фильтрах
        self._save_filters_info(save_path, path, template_name, custom_template,
                               arguments, encoding, result.token_count)

        return saved_file_path

    def _save_filters_info(self, save_path: Path, path: str, template_name: str | None,
                          custom_template: str | None, arguments: dict[str, Any],
                          encoding: str, token_count: int):
        """Сохранить информацию о примененных фильтрах"""
        try:
            project_manager = self._get_project_manager()
            project_name = project_manager.get_project_name(path)
            filters_filename = f"{project_name}.filters-used.md"
            filters_save_path = save_path.parent / filters_filename

            # Формируем содержимое файла с фильтрами
            filters_content = self._create_filters_content(
                path, template_name, custom_template, arguments,
                encoding, token_count, str(save_path)
            )

            # Сохраняем файл с фильтрами
            filters_save_path.write_text(filters_content, encoding='utf-8')
            logger.info(f"Filters config saved to: {filters_save_path}")

        except Exception as filter_error:
            logger.error(f"Error saving filters config: {filter_error}")

    def _create_filters_content(self, path: str, template_name: str | None,
                               custom_template: str | None, arguments: dict[str, Any],
                               encoding: str, token_count: int, main_file_path: str) -> str:
        """Создать содержимое файла с информацией о фильтрах"""
        filters_content = "# 🔧 Примененные фильтры\n\n"
        filters_content += f"**📁 Проект:** `{path}`\n"
        filters_content += f"**📅 Дата:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        filters_content += f"**🎯 Шаблон:** {template_name if template_name else 'custom' if custom_template else 'default'}\n"
        filters_content += f"**📝 Кодировка:** {encoding}\n"
        filters_content += f"**🎯 Токенов сгенерировано:** {token_count:,}\n\n"

        filters_content += "## ⚙️ Конфигурация фильтров\n\n"

        include_patterns = arguments.get("include_patterns", [])
        exclude_patterns = arguments.get("exclude_patterns", [])

        if include_patterns:
            filters_content += "### ✅ Include patterns:\n"
            for pattern in include_patterns:
                filters_content += f"- `{pattern}`\n"
            filters_content += "\n"
        else:
            filters_content += "### ✅ Include patterns: *(все файлы)*\n\n"

        if exclude_patterns:
            filters_content += "### ❌ Exclude patterns:\n"
            for pattern in exclude_patterns:
                filters_content += f"- `{pattern}`\n"
            filters_content += "\n"
        else:
            filters_content += "### ❌ Exclude patterns: *(нет исключений)*\n\n"

        filters_content += "### 🔧 Дополнительные параметры:\n"
        filters_content += f"- **Include priority:** {arguments.get('include_priority', False)}\n"
        filters_content += f"- **Line numbers:** {arguments.get('line_numbers', True)}\n"
        filters_content += f"- **Absolute paths:** {arguments.get('absolute_paths', False)}\n"
        filters_content += f"- **Full directory tree:** {arguments.get('full_directory_tree', False)}\n"
        filters_content += f"- **Code blocks:** {arguments.get('code_blocks', True)}\n"
        filters_content += f"- **Follow symlinks:** {arguments.get('follow_symlinks', False)}\n"
        filters_content += f"- **Include hidden:** {arguments.get('include_hidden', False)}\n\n"

        filters_content += "## 📋 JSON конфигурация для повторного использования\n\n"
        filters_content += "```json\n"
        config_json = {
            "path": path,
            "template_name": template_name,
            "include_patterns": include_patterns,
            "exclude_patterns": exclude_patterns,
            "include_priority": arguments.get('include_priority', False),
            "line_numbers": arguments.get('line_numbers', True),
            "absolute_paths": arguments.get('absolute_paths', False),
            "full_directory_tree": arguments.get('full_directory_tree', False),
            "code_blocks": arguments.get('code_blocks', True),
            "follow_symlinks": arguments.get('follow_symlinks', False),
            "include_hidden": arguments.get('include_hidden', False),
            "encoding": encoding
        }
        filters_content += json.dumps(config_json, indent=2, ensure_ascii=False)
        filters_content += "\n```\n\n"

        filters_content += "## 🎯 Результат\n\n"
        filters_content += f"Конфигурация использована для генерации {token_count:,} токенов кода.\n"
        filters_content += f"Основной файл: `{main_file_path}`"

        return filters_content

    def _create_save_response(self, saved_file_path: str, token_count: int,
                             template_name: str | None, custom_template: str | None,
                             encoding: str, path: str) -> str:
        """Создать ответ с информацией о сохранении"""
        response = "# 💾 Контекст и фильтры сохранены\n\n"
        response += "## 📄 Основной файл контекста\n"
        response += f"**📁 Путь к файлу:** `{saved_file_path}`\n"
        response += f"**📊 Размер:** {token_count:,} токенов\n"
        response += f"**🎯 Шаблон:** {template_name if template_name else 'custom' if custom_template else 'default'}\n"
        response += f"**📝 Кодировка:** {encoding}\n\n"

        # Информация о файле с фильтрами
        project_manager = self._get_project_manager()
        project_name = project_manager.get_project_name(path)
        filters_path = Path(saved_file_path).parent / f"{project_name}.filters-used.md"
        response += "## 🔧 Файл с конфигурацией фильтров\n"
        response += f"**📁 Путь:** `{filters_path}`\n"
        response += "**📋 Содержимое:** JSON конфигурация для повторного использования\n\n"

        return response

    def _create_simple_stats(self, result, path: str):
        """Создаёт объект статистики из результата Code2Prompt используя реальные данные"""
        class SimpleStats:
            def __init__(self, result, path):
                self.total_tokens = result.token_count
                self.total_characters = len(result.prompt)
                self.total_lines = result.prompt.count('\n')
                # ИСПРАВЛЕНИЕ: Явно указываем None для недоступных данных
                self.total_files = None  # Неизвестно из code2prompt-rs
                self.top_files_by_size = None  # Нет детальной информации
                self.file_type_stats = None  # Нет детальной информации

        return SimpleStats(result, path)

    def _generate_optimization_recommendations(self, stats, include_patterns: list[str],
                                             exclude_patterns: list[str], path: str) -> str:
        """
        Генерирует проактивные рекомендации по оптимизации фильтров

        Quick Performance Win: Автоматические рекомендации для экономии токенов
        """
        from .filters import DEFAULT_EXCLUDES, get_code_only_patterns

        # ИСПРАВЛЕНИЕ: Явная проверка доступности детальной статистики
        if not hasattr(stats, 'file_type_stats') or stats.file_type_stats is None:
            return "## 💡 Рекомендации по оптимизации\n\n" \
                   "⚠️ **Детальная статистика по файлам недоступна.** Невозможно дать точные рекомендации по оптимизации.\n\n" \
                   "**🔧 Общие рекомендации для оптимизации:**\n" \
                   "- Используйте базовые исключения: `node_modules/**`, `dist/**`, `__pycache__/**`\n" \
                   "- Исключите файлы тестов: `tests/**`, `*.test.js`, `*.spec.ts`\n" \
                   "- Уберите lock-файлы: `package-lock.json`, `yarn.lock`, `poetry.lock`\n" \
                   "- Исключите медиа и шрифты: `*.png`, `*.jpg`, `*.woff`, `*.ttf`\n\n" \
                   "💡 **Для детального анализа:** Попробуйте использовать другие фильтры или убедитесь, что code2prompt-rs может обработать файлы проекта.\n\n"

        recommendations = []
        ready_filters = []

        # Анализируем количество токенов
        total_tokens = stats.total_tokens

        # 1. Базовые рекомендации если не применены DEFAULT_EXCLUDES
        missing_default_excludes = []
        for pattern in DEFAULT_EXCLUDES:
            if pattern not in exclude_patterns:
                missing_default_excludes.append(pattern)

        if missing_default_excludes:
            recommendations.append(
                f"🔧 **Добавьте базовые исключения** ({len(missing_default_excludes)} паттернов)"
            )
            ready_filters.extend(missing_default_excludes[:5])  # Первые 5 для краткости

        # 2. Рекомендации для больших проектов
        if total_tokens > LARGE_PROJECT_TOKEN_THRESHOLD:
            recommendations.append(
                f"⚠️ **Большой проект** ({total_tokens:,} токенов) - используйте агрессивные фильтры"
            )

            # Предлагаем code-only фильтры
            code_includes, code_excludes = get_code_only_patterns()
            if not include_patterns:  # Если нет include паттернов
                recommendations.append(
                    "💡 **Ограничьте типы файлов** - используйте include_patterns для кода"
                )
                ready_filters.extend(code_includes[:3])

        # 3. Интеллектуальный анализ типов файлов - адаптивные рекомендации
        if hasattr(stats, 'file_type_stats') and stats.file_type_stats and total_tokens > 0:
            heavy_non_code_extensions = []
            for ext, ext_stats in stats.file_type_stats.items():
                # Вычисляем процентное соотношение токенов этого типа файлов
                token_percentage = (ext_stats.total_tokens / total_tokens) * 100

                # Адаптивная логика: если тип файла занимает много процентов токенов и это не код
                if token_percentage > HEAVY_FILE_TYPE_PERCENTAGE_THRESHOLD and ext in ['.json', '.log', '.xml', '.svg', '.md', '.txt', '.csv', '.yaml', '.yml']:
                    heavy_non_code_extensions.append(f"*{ext} ({token_percentage:.0f}%)")
                    ready_filters.append(f"*{ext}")
                # Дополнительно: файлы с большим абсолютным количеством токенов и низкой ценностью
                elif ext_stats.total_tokens > HEAVY_FILE_ABSOLUTE_TOKEN_THRESHOLD and ext in ['.lock', '.min.js', '.min.css', '.map', '.ico', '.woff', '.woff2']:
                    heavy_non_code_extensions.append(f"*{ext} ({ext_stats.total_tokens:,} токенов)")
                    ready_filters.append(f"*{ext}")

            if heavy_non_code_extensions:
                recommendations.append(
                    f"📊 **Исключите тяжёлые файлы данных:** {', '.join(heavy_non_code_extensions)}"
                )

        # 4. Автоматическое определение типа проекта и специфичные рекомендации
        project_type_recommendations = self._detect_project_type_and_recommend(stats, path)
        if project_type_recommendations:
            recommendations.extend(project_type_recommendations)

        # Формируем итоговый раздел рекомендаций
        if not recommendations:
            return "## 💡 Оптимизация\n\n✅ **Фильтры уже оптимальны** - дополнительная настройка не требуется.\n\n"

        response = "## 💡 Рекомендации по оптимизации\n\n"
        response += f"**📊 Текущий размер:** {total_tokens:,} токенов\n"
        response += "**🎯 Принцип:** «Максимально исключить ненужные файлы, включить только необходимые»\n\n"

        # Список рекомендаций
        for i, rec in enumerate(recommendations, 1):
            response += f"{i}. {rec}\n"

        # Готовые фильтры для копирования
        if ready_filters:
            response += "\n### 📋 Готовые exclude_patterns для копирования:\n\n"
            response += "```json\n"
            response += '"exclude_patterns": [\n'
            for pattern in ready_filters:
                response += f'  "{pattern}",\n'
            response += "]\n"
            response += "```\n\n"

        # Расчётная экономия
        estimated_reduction = min(len(ready_filters) * 10000, total_tokens * 0.3)  # Примерная оценка
        if estimated_reduction > 0:
            response += f"**💰 Ожидаемая экономия:** ~{estimated_reduction:,.0f} токенов ({estimated_reduction/total_tokens*100:.1f}%)\n\n"

        return response

    def _detect_project_type_and_recommend(self, stats, path: str) -> list[str]:
        """Определяет тип проекта и даёт специфичные рекомендации с предложением пресетов"""
        recommendations = []

        if not hasattr(stats, 'file_type_stats') or not stats.file_type_stats:
            return recommendations

        file_types = set(stats.file_type_stats.keys())

        # Python проект
        if '.py' in file_types:
            py_files = stats.file_type_stats['.py'].total_files
            if py_files > 10:
                recommendations.append(
                    f"🐍 **Python проект** ({py_files} файлов) - рекомендуем пресет `python-project`"
                )

        # React/TypeScript проект
        if '.tsx' in file_types or '.jsx' in file_types:
            recommendations.append(
                "⚛️ **React проект** - рекомендуем пресет `react-app`"
            )
        # JavaScript/Node.js проект (но не React)
        elif '.js' in file_types or '.ts' in file_types or 'package.json' in str(path).lower():
            recommendations.append(
                "🟨 **JS/Node.js проект** - рекомендуем пресет `web-app`"
            )

        # Electron проект (многопакетная архитектура)
        if 'packages' in str(path).lower() and ('.js' in file_types or '.ts' in file_types):
            recommendations.append(
                "🖥️ **Electron/монорепо** - рекомендуем пресет `electron-app`"
            )

        # Веб-проект (много CSS/HTML)
        if '.css' in file_types and '.html' in file_types:
            recommendations.append(
                "🌐 **Веб-проект** - рекомендуем пресет `web-app`"
            )

        # Проект с большим количеством документации - предложить агрессивные фильтры
        if '.md' in file_types:
            md_files = stats.file_type_stats['.md'].total_files
            if md_files > 20:
                recommendations.append(
                    f"📚 **Много документации** ({md_files} .md файлов) - рекомендуем пресет `aggressive` для экономии токенов"
                )

        # Если ничего не определилось, предложить базовые пресеты
        if not recommendations:
            recommendations.append(
                "🔧 **Неопределённый тип проекта** - попробуйте пресет `default` или `code-only`"
            )

        return recommendations

    # УДАЛЕН: God Method analyze_filters (196 строк) - логика перенесена в FilterAnalyzer и AnalysisReporter
    # Используйте FilterAnalyzer.analyze() и AnalysisReporter.generate_report() вместо этого метода

    async def analyze_filters_tool(self, arguments: dict) -> list[TextContent]:
        """
        MCP обертка для анализа фильтров - переписано для использования новой архитектуры

        АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: Использует FilterAnalyzer + AnalysisReporter вместо God Method

        ⚠️ УСТАРЕВШИЙ ИНСТРУМЕНТ: Рекомендуется использовать `set_filters` для настройки фильтров.
        `analyze_filters` предназначен только для отладки и анализа существующих конфигураций.

        Для полного AI анализа используйте `get_analyze`.
        """
        try:
            # ИСПРАВЛЕНО: Используем новые специализированные сервисы вместо God Method
            from .analysis_reporter import AnalysisReporter
            from .filter_analyzer import FilterAnalyzer

            # Создаем экземпляры сервисов
            analyzer = FilterAnalyzer()
            reporter = AnalysisReporter()

            # Извлекаем параметры
            path = arguments.get("path", ".")
            include_patterns = arguments.get("include_patterns", [])
            exclude_patterns = arguments.get("exclude_patterns", [])
            encoding = arguments.get("encoding", "cl100k")

            # Обрабатываем пресеты если указаны
            preset_name = arguments.get("preset_name")
            merge_with_preset = arguments.get("merge_with_preset", False)

            if preset_name:
                from .filters import load_preset
                preset_patterns = load_preset(preset_name)
                if preset_patterns:
                    preset_include, preset_exclude = preset_patterns

                    if merge_with_preset:
                        include_patterns = list(set(preset_include + include_patterns))
                        exclude_patterns = list(set(preset_exclude + exclude_patterns))
                        logger.info(f"Merged preset '{preset_name}' with custom patterns")
                    else:
                        include_patterns = preset_include
                        exclude_patterns = preset_exclude
                        logger.info(f"Using preset '{preset_name}' patterns")
                else:
                    logger.warning(f"Preset '{preset_name}' not found, using original patterns")

            # Выполняем анализ через новый сервис
            analysis_result = await analyzer.analyze(
                path=path,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
                encoding=encoding
            )

            if not analysis_result.success:
                return [TextContent(type="text", text=f"❌ {analysis_result.error_message}")]

            # Генерируем отчет через новый сервис
            report = reporter.generate_report(analysis_result)

            # Обрабатываем сохранение пресета если указано
            save_as_preset = arguments.get("save_as_preset")
            if save_as_preset:
                from pathlib import Path  # Импорт для работы с путями

                from .filters import save_preset
                description = f"Пресет, созданный из анализа проекта {Path(path).name} ({analysis_result.total_tokens:,} токенов)"
                success = save_preset(
                    save_as_preset,
                    include_patterns,
                    exclude_patterns,
                    description,
                    project_path=path,
                    token_count=analysis_result.total_tokens,
                    created_from_analysis=True
                )

                if success:
                    report += "\n\n## ✅ Пресет сохранен\n\n"
                    report += f"**Название:** `{save_as_preset}`\n"
                    report += f"**Описание:** {description}\n"
                    logger.info(f"Пресет '{save_as_preset}' успешно сохранен")
                else:
                    report += "\n\n## ❌ Ошибка сохранения пресета\n\n"
                    report += f"Не удалось сохранить пресет `{save_as_preset}`\n"
                    logger.error(f"Не удалось сохранить пресет '{save_as_preset}'")

            # Добавляем предупреждение в начало отчёта
            deprecated_warning = "## ⚠️ Устаревший инструмент\n\n"
            deprecated_warning += "**Этот инструмент устарел.** Рекомендуется использовать:\n"
            deprecated_warning += "- **`set_filters`** - для настройки и оптимизации фильтров\n"
            deprecated_warning += "- **`get_analyze`** - для полного автоматического AI анализа кода\n\n"
            deprecated_warning += "---\n\n"

            enhanced_report = deprecated_warning + report
            return [TextContent(type="text", text=enhanced_report)]

        except Exception as e:
            error_msg = f"❌ Ошибка анализа фильтров: {str(e)}"
            logger.error(error_msg)
            return [TextContent(type="text", text=error_msg)]

    async def get_context(self, arguments: dict) -> list[TextContent]:
        """
        Получение контекста - оригинальная функция get_context_tool
        """

        try:
            # Используем основной метод generate_context
            response, saved_file_path = self.generate_context(arguments)

            logger.info("Context generated successfully")

            return [TextContent(type="text", text=response)]

        except Exception as e:
            error_msg = f"❌ Ошибка генерации контекста: {str(e)}"
            logger.error(error_msg)
            return [TextContent(type="text", text=error_msg)]

    # УДАЛЕН: Метод set_filters перенесен в FilterSetupService для соблюдения принципа единственной ответственности
    # Используйте FilterSetupService.setup_project_filters() вместо этого метода

    # УДАЛЕН: Метод _detect_project_type перенесен в FilterSetupService
    # Используйте FilterSetupService._detect_project_type() если нужна эта функциональность

    # УДАЛЕН: Метод set_filters_tool перенесен в FilterSetupService
    # Используйте FilterSetupService.setup_project_filters() в main.py

    def _validate_project_size(self, path: str, exclude_patterns: list = None) -> None:
        """
        ИСПРАВЛЕНО: Валидация размера проекта с учетом фильтров исключения

        Args:
            path: Путь к проекту
            exclude_patterns: Список паттернов для исключения файлов

        Raises:
            ValueError: При превышении лимитов безопасности
        """
        import fnmatch
        from pathlib import Path

        project_path = Path(path)
        total_size = 0
        file_count = 0

        # Если нет exclude паттернов, получаем базовые исключения
        if exclude_patterns is None:
            from .filters import get_default_excludes
            exclude_patterns = get_default_excludes()

        def _should_exclude_file(file_path: Path) -> bool:
            """Проверяет, должен ли файл быть исключен по паттернам"""
            if not exclude_patterns:
                return False

            # Получаем относительный путь от корня проекта
            try:
                relative_path = file_path.relative_to(project_path)
                relative_path_str = str(relative_path).replace('\\', '/')

                # Проверяем все exclude паттерны
                for pattern in exclude_patterns:
                    # Поддержка glob паттернов
                    if fnmatch.fnmatch(relative_path_str, pattern):
                        return True
                    # Поддержка паттернов с директориями
                    if '/' in pattern and fnmatch.fnmatch(relative_path_str, pattern):
                        return True
                    # Поддержка простых паттернов имен файлов
                    if fnmatch.fnmatch(file_path.name, pattern):
                        return True
                return False
            except ValueError:
                # Файл находится вне проекта
                return False

        for file_path in project_path.rglob('*'):
            if file_path.is_file():
                # Проверяем, нужно ли исключить файл
                if _should_exclude_file(file_path):
                    continue

                try:
                    file_size = file_path.stat().st_size

                    # Проверка максимального размера файла
                    if file_size > MAX_FILE_SIZE_BYTES:
                        raise ValueError(f"File too large: {file_path.name} ({file_size / 1024 / 1024:.1f}MB > {MAX_FILE_SIZE_BYTES / 1024 / 1024:.1f}MB)")

                    total_size += file_size
                    file_count += 1

                    # Проверка максимального количества файлов
                    if file_count > MAX_FILES_COUNT:
                        raise ValueError(f"Too many files: {file_count} > {MAX_FILES_COUNT}")

                    # Проверка общего размера
                    if total_size > MAX_TOTAL_SIZE_BYTES:
                        raise ValueError(f"Project too large: {total_size / 1024 / 1024:.1f}MB > {MAX_TOTAL_SIZE_BYTES / 1024 / 1024:.1f}MB")

                except (OSError, PermissionError):
                    # Пропускаем файлы, к которым нет доступа
                    continue

        logger.info(f"Project validation passed: {file_count} files, {total_size / 1024 / 1024:.1f}MB")

    def _create_code2prompt(self, path: str, include_patterns: list, exclude_patterns: list, **kwargs) -> Any:
        """Создает объект Code2Prompt с расширенными возможностями из code2prompt-rs"""
        try:
            from code2prompt_rs import Code2Prompt

            from .filters import get_default_excludes

            # 🚀 PERFORMANCE WIN: Используем централизованный источник фильтров

            # Используем предкомпилированные паттерны включения если не указаны
            if not include_patterns:
                include_patterns = DEFAULT_INCLUDE_PATTERNS

            # Объединяем централизованные default excludes с пользовательскими exclude patterns
            default_excludes = get_default_excludes()
            enhanced_exclude_patterns = default_excludes + (exclude_patterns or [])

            # ИСПРАВЛЕНО: Валидация размера проекта с учетом фильтров исключения
            self._validate_project_size(path, enhanced_exclude_patterns)

            # Извлекаем дополнительные опции из kwargs
            line_numbers = kwargs.get('line_numbers', False)
            absolute_paths = kwargs.get('absolute_paths', False)
            full_directory_tree = kwargs.get('full_directory_tree', False)
            code_blocks = kwargs.get('code_blocks', True)
            follow_symlinks = kwargs.get('follow_symlinks', False)
            include_hidden = kwargs.get('include_hidden', False)
            include_priority = kwargs.get('include_priority', False)

            logger.info("🚀 Создание Code2Prompt с расширенными возможностями:")
            logger.info(f"   📁 Path: {path}")
            logger.info(f"   📥 Include patterns: {len(include_patterns)} patterns")
            logger.info(f"   🚫 Exclude patterns: {len(enhanced_exclude_patterns)} patterns")
            logger.info(f"   🔢 Line numbers: {line_numbers}")
            logger.info(f"   📍 Absolute paths: {absolute_paths}")
            logger.info(f"   🌳 Full directory tree: {full_directory_tree}")
            logger.info(f"   📦 Code blocks: {code_blocks}")
            logger.info(f"   🔗 Follow symlinks: {follow_symlinks}")
            logger.info(f"   👁️ Include hidden: {include_hidden}")

            return Code2Prompt(
                path=path,
                include_patterns=include_patterns,
                exclude_patterns=enhanced_exclude_patterns,
                include_priority=include_priority,
                line_numbers=line_numbers,
                absolute_paths=absolute_paths,
                full_directory_tree=full_directory_tree,
                code_blocks=code_blocks,
                follow_symlinks=follow_symlinks,
                include_hidden=include_hidden
            )
        except ImportError:
            logger.error("code2prompt_rs не установлен. Установите его: pip install code2prompt-rs")
            raise


# Глобальный экземпляр убран - используем DI контейнер для получения экземпляра
