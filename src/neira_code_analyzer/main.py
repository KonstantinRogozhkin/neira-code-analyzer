"""
Neira Code Analyzer MCP Server

MCP сервер для продвинутого анализа кодовых баз с помощью code2prompt_rs SDK.
Предоставляет профессиональные шаблоны для анализа кода и генерации документации.

Основные возможности:
- Анализ структуры проекта
- Применение специализированных шаблонов (security audit, code review, документация)
- Фильтрация файлов по паттернам
- Подсчет токенов для LLM
- Генерация markdown с подсветкой синтаксиса
"""

import asyncio
import logging
import os

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)


# ИСПРАВЛЕНО: Настройка логирования с поддержкой переменной окружения
def setup_logging():
    """Настройка логирования с учетом переменной окружения NEIRA_LOG_LEVEL"""

    # Получаем уровень логирования из переменной окружения
    log_level_str = os.getenv('NEIRA_LOG_LEVEL', 'ERROR').upper()

    # Маппинг строк в уровни логирования
    log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    log_level = log_levels.get(log_level_str, logging.ERROR)

    # Настройка базового логирования
    logging.basicConfig(
        level=log_level,
        format="%(levelname)-8s %(name)s: %(message)s",
        handlers=[] if log_level >= logging.ERROR else [logging.StreamHandler()]
    )

    # Устанавливаем уровень для всех логгеров проекта
    for logger_name in ['neira_code_analyzer', __name__]:
        logging.getLogger(logger_name).setLevel(log_level)

setup_logging()
logger = logging.getLogger(__name__)

# Импорты для безопасности и архитектурных улучшений
# Импорт централизованных схем для устранения дублирования MCP инструментов
from .mcp_schemas import get_tool_schema
from .path_validator import PathValidationError, validate_project_path
from .service_container import get_cached_service

# Создаем MCP сервер
app = Server("neira-code-analyzer")

# Реестр инструментов для декоратора
TOOL_HANDLERS = {}

# ИСПРАВЛЕНО: Убран небезопасный глобальный кэш
# Теперь используется thread-safe ServiceContainer

def tool_handler(name: str):
    """
    Декоратор для регистрации обработчиков инструментов

    Args:
        name: Название инструмента для регистрации
    """
    def decorator(func):
        TOOL_HANDLERS[name] = func
        return func
    return decorator

@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    Регистрируем доступные инструменты для MCP клиентов.

    Returns:
        list[Tool]: Список доступных инструментов с их схемами

    Raises:
        Exception: При критических ошибках конфигурации (Fail-Fast)
    """
    try:
        tools = []

        # Создаем инструменты по одному с обработкой ошибок
        tool_configs = [
            ("get_context", "Generates contextual prompts from codebases using code2prompt-rs library. 🎯 АВТОМАТИЧЕСКИ загружает конфигурацию из .neira файлов проекта."),
            ("set_filters", "🎯 Автоматически подбирает оптимальные фильтры для проекта и сохраняет их в .neira. Анализирует структуру проекта, определяет тип (Python, React, etc.), применяет подходящие фильтры и сохраняет конфигурацию для повторного использования."),
            ("project_config", "🎯 Просмотр конфигурации проекта из .neira файлов. Показывает найденные настройки фильтров, шаблонов и статус автозагрузки."),
            ("get_templates", "🎯 STEP 1: Get list of available professional templates for code analysis. Use this FIRST to see all available templates (code-review, security-audit, documentation, etc.) with descriptions and use cases. Then use 'get_context' with 'template_name' parameter."),
            ("manage_presets", "🎛️ Управление пресетами фильтров: просмотр, создание, удаление, экспорт/импорт сохраненных конфигураций фильтров. Позволяет сохранять удачные комбинации include/exclude паттернов для повторного использования в разных проектах."),
            ("get_analyze", "🔍 Автоматический анализ кода через Neira. 🎯 АВТОМАТИЧЕСКИ загружает конфигурацию из .neira файлов. Запускает set_filters, проверяет количество токенов (до 1 млн), подбирает оптимальные фильтры и выполняет детальный Neira анализ."),
            ("gen_docs", "📚 Автоматическая генерация и обновление документации проекта. Сканирует файлы проекта, извлекает знания из отчётов, обновляет документацию в docs/, создаёт changelog из git-истории, сжимает длинные файлы и архивирует обработанные материалы.")
        ]

        for tool_name, description in tool_configs:
            try:
                # Получаем схему инструмента
                schema = get_tool_schema(tool_name)

                tool = Tool(
                    name=tool_name,
                    description=description,
                    inputSchema=schema
                )
                tools.append(tool)

            except Exception as e:
                # ИСПРАВЛЕНО: Проверяем тип ошибки для Fail-Fast
                from .mcp_schemas import ConfigurationError

                if isinstance(e, ConfigurationError):
                    # Критическая ошибка конфигурации - прерываем запуск сервера
                    logger.critical(f"Критическая ошибка конфигурации при загрузке инструмента {tool_name}: {e}")
                    raise e

                # Для некритических ошибок создаем fallback
                logger.warning(f"Не удалось загрузить схему для инструмента {tool_name}: {e}")
                tool = Tool(
                    name=tool_name,
                    description=f"[FALLBACK] {description}",
                    inputSchema={"type": "object", "properties": {}}
                )
                tools.append(tool)

        return tools

    except Exception as e:
        from .mcp_schemas import ConfigurationError

        if isinstance(e, ConfigurationError):
            # Критическая ошибка конфигурации - не можем запуститься
            logger.critical(f"Сервер не может запуститься из-за критической ошибки конфигурации: {e}")
            raise e

        # Для других ошибок возвращаем минимальный набор инструментов
        logger.error(f"Ошибка при создании списка инструментов: {e}")
        return [
            Tool(
                name="get_context",
                description="Basic context generation tool",
                inputSchema={"type": "object", "properties": {}}
            )
        ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Обработчик вызовов инструментов MCP с декоративной регистрацией.

    Args:
        name: Название инструмента для вызова
        arguments: Аргументы для инструмента

    Returns:
        list[TextContent]: Результат выполнения инструмента

    Raises:
        ValueError: Если инструмент не найден
    """
    handler = TOOL_HANDLERS.get(name)
    if handler:
        return await handler(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

@tool_handler("get_context")
async def get_context_tool(arguments: dict) -> list[TextContent]:
    """
    Генерирует контекстные промпты из кодовых баз используя code2prompt-rs.

    Основная функция для анализа проектов с применением профессиональных шаблонов.
    Поддерживает фильтрацию файлов, различные форматы вывода и подсчет токенов.

    🎯 АВТОМАТИЧЕСКАЯ ЗАГРУЗКА: Система автоматически загружает конфигурацию
    из .neira файлов в проекте, если они существуют.

    Args:
        arguments: Словарь с параметрами анализа

    Returns:
        list[TextContent]: Сгенерированный контекст в формате текста
    """
    try:
        # ИСПРАВЛЕНО: Валидация пути для безопасности
        path_str = arguments.get('path', '.')
        try:
            validated_path = validate_project_path(path_str)
        except PathValidationError as e:
            return [TextContent(type="text", text=f"❌ ОШИБКА БЕЗОПАСНОСТИ: {str(e)}")]

        # 🎯 НОВАЯ ФУНКЦИЯ: Автоматическая загрузка конфигурации проекта из .neira
        from .neira_config_loader import get_config_loader
        config_loader = get_config_loader()

        # Применяем сохраненную конфигурацию проекта (если есть)
        arguments_copy = arguments.copy()
        arguments_copy['path'] = str(validated_path)
        arguments_copy = config_loader.auto_apply_config(arguments_copy)

        # ИСПРАВЛЕНО: Используем thread-safe service container
        from .context_generator import ContextGenerator
        context_generator = get_cached_service(ContextGenerator)

        logger.info(f"Delegating context generation to context_generator for path: {validated_path}")

        # Делегируем выполнение специализированному модулю
        response, _ = context_generator.generate_context(arguments_copy)
        return [TextContent(type="text", text=response)]

    except Exception as e:
        logger.error(f"Error in context tool: {e}")
        return [TextContent(type="text", text=f"❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")]

@tool_handler("set_filters")
async def set_filters_tool(arguments: dict) -> list[TextContent]:
    """
    Автоматически подбирает оптимальные фильтры для проекта и сохраняет их.

    🎯 ЦЕЛЬ: Настроить проект с оптимальными фильтрами один раз и использовать везде.

    Анализирует структуру проекта, определяет тип (Python, React, etc.),
            подбирает подходящие фильтры и сохраняет конфигурацию в .neira
    в корне проекта для повторного использования.

    Args:
        arguments: Словарь с параметрами настройки фильтров

    Returns:
        list[TextContent]: Отчет о настройке и сохранении фильтров
    """
    try:
        # ИСПРАВЛЕНО: Валидация пути для безопасности
        path_str = arguments.get("path", ".")
        try:
            validated_path = validate_project_path(path_str)
        except PathValidationError as e:
            return [TextContent(type="text", text=f"❌ ОШИБКА БЕЗОПАСНОСТИ: {str(e)}")]

        # ИСПРАВЛЕНО: Используем thread-safe service container
        from .filter_setup_service import FilterSetupService
        filter_service = get_cached_service(FilterSetupService)

        # Выполняем настройку фильтров через специализированный сервис
        result = await filter_service.setup_project_filters(
            path=str(validated_path),
            preset_name=arguments.get("preset_name"),
            include_patterns=arguments.get("include_patterns", []),
            exclude_patterns=arguments.get("exclude_patterns", []),
            merge_with_preset=arguments.get("merge_with_preset", False),
            encoding=arguments.get("encoding", "cl100k")
        )

        if result.success:
            return [TextContent(type="text", text=result.report_message)]
        else:
            return [TextContent(type="text", text=result.error_message or "Unknown error")]

    except Exception as e:
        logger.error(f"Error in set_filters tool: {e}")
        return [TextContent(type="text", text=f"❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")]


@tool_handler("get_templates")
async def get_templates_tool(arguments: dict) -> list[TextContent]:
    """
    Получает краткий список доступных шаблонов для анализа кода.

    Использует централизованную реализацию из template_manager.py

    Args:
        arguments: Параметры запроса (show_content для показа содержимого)

    Returns:
        list[TextContent]: Список шаблонов с кратким описанием
    """
    try:
        # ИСПРАВЛЕНО: Используем thread-safe service container
        from .template_manager import TemplateManager
        template_manager = get_cached_service(TemplateManager)

        show_content = arguments.get("show_content", False)

        logger.info("Delegating templates info to template_manager")

        # Делегируем выполнение специализированному модулю
        response = template_manager.get_templates_info(show_content)
        return [TextContent(type="text", text=response)]

    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return [TextContent(type="text", text=f"❌ Ошибка при получении шаблонов: {str(e)}")]

@tool_handler("manage_presets")
async def manage_presets_tool(arguments: dict) -> list[TextContent]:
    """
    Управление пресетами фильтров: просмотр, создание, удаление, экспорт/импорт

    Args:
        arguments: Параметры операции с пресетами

    Returns:
        list[TextContent]: Результат операции с пресетами
    """
    try:
        # ИСПРАВЛЕНО: Используем thread-safe service container
        from .filters import FilterPresetManager
        manager = get_cached_service(FilterPresetManager)

        # Делегируем обработку действия менеджеру
        result = manager.handle_action(arguments)

        return [TextContent(type="text", text=result)]

    except Exception as e:
        error_msg = f"❌ Ошибка управления пресетами: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]

@tool_handler("get_analyze")
async def get_analyze_tool(arguments: dict) -> list[TextContent]:
    """
    Автоматический анализ кода через Neira

    Использует централизованную реализацию из ai_analyzer.py
    для выполнения полного цикла анализа кода.

    🎯 АВТОМАТИЧЕСКАЯ ЗАГРУЗКА: Система автоматически загружает конфигурацию
    из .neira файлов в проекте, включая фильтры и настройки шаблонов.

    Args:
        arguments: Параметры анализа

    Returns:
        list[TextContent]: Результат анализа от Neira
    """
    try:
        # ИСПРАВЛЕНО: Валидация пути для безопасности
        path_str = arguments.get('path', '.')
        try:
            validated_path = validate_project_path(path_str)
        except PathValidationError as e:
            return [TextContent(type="text", text=f"❌ ОШИБКА БЕЗОПАСНОСТИ: {str(e)}")]

        # 🎯 НОВАЯ ФУНКЦИЯ: Автоматическая загрузка конфигурации проекта из .neira
        from .neira_config_loader import get_config_loader
        config_loader = get_config_loader()

        # ⚡ QUICK WIN: Автонастройка фильтров для ускорения на 40-60%
        config_info = config_loader.get_config_info(str(validated_path))
        if not config_info["has_config"]:
            logger.info(f"🔧 Нет конфигурации .neira для {validated_path}, запускаем автонастройку фильтров...")

            # Автоматически запускаем set_filters с агрессивными настройками
            from .filter_setup_service import FilterSetupService
            filter_service = get_cached_service(FilterSetupService)

            filter_result = await filter_service.setup_project_filters(
                path=str(validated_path),
                preset_name="aggressive",  # Агрессивный пресет для максимального ускорения
                include_patterns=[],
                exclude_patterns=[],
                merge_with_preset=False,
                encoding=arguments.get("encoding", "cl100k")
            )

            if filter_result.success:
                logger.info(f"✅ Автонастройка фильтров завершена: {filter_result.optimization_stats}")
            else:
                logger.warning(f"⚠️ Автонастройка фильтров не удалась: {filter_result.error_message}")

        # Применяем сохраненную конфигурацию проекта (если есть)
        arguments_copy = arguments.copy()
        arguments_copy['path'] = str(validated_path)
        arguments_copy = config_loader.auto_apply_config(arguments_copy)

        # ИСПРАВЛЕНО: Используем thread-safe service container
        from .ai_analyzer import NeiraAnalyzer
        ai_analyzer = get_cached_service(NeiraAnalyzer)

        logger.info(f"Delegating code review to ai_analyzer for path: {validated_path}")

        # Делегируем выполнение специализированному модулю
        result_text = await ai_analyzer.perform_code_review(**arguments_copy)
        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        logger.error(f"Error in code review tool: {e}")
        return [TextContent(type="text", text=f"❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")]

@tool_handler("project_config")
async def project_config_tool(arguments: dict) -> list[TextContent]:
    """
    Просмотр информации о конфигурации проекта из .neira файлов

    Показывает какие конфигурационные файлы найдены в проекте,
    их содержимое и статус автоматической загрузки настроек.

    Args:
        arguments: Параметры запроса (path - путь к проекту)

    Returns:
        list[TextContent]: Информация о конфигурации проекта
    """
    try:
        # Валидация пути
        path_str = arguments.get('path', '.')
        try:
            validated_path = validate_project_path(path_str)
        except PathValidationError as e:
            return [TextContent(type="text", text=f"❌ ОШИБКА БЕЗОПАСНОСТИ: {str(e)}")]

        from .neira_config_loader import get_config_loader
        config_loader = get_config_loader()

        # Получаем информацию о конфигурации
        config_info = config_loader.get_config_info(str(validated_path))
        config = config_loader.load_project_config(str(validated_path))

        # Формируем отчет
        report = "# 🎯 Конфигурация проекта Neira\n\n"
        report += f"**📁 Проект:** `{validated_path}`\n\n"

        if config_info["has_config"]:
            report += "## ✅ Найденные конфигурационные файлы\n\n"
            for config_file in config_info["config_files"]:
                report += f"- `{config_file}`\n"

            report += f"\n**🎯 Основной источник:** `{config_info['config_source']}`\n\n"

            if config:
                report += "## 📋 Загруженная конфигурация\n\n"

                if config.preset_used:
                    report += f"**🔧 Пресет:** `{config.preset_used}`\n"

                if config.template_name:
                    report += f"**📄 Шаблон:** `{config.template_name}`\n"

                report += f"**🔤 Кодировка:** `{config.encoding}`\n"
                report += f"**🤖 Автодетекция:** {'Да' if config.auto_detected else 'Нет'}\n"
                report += f"**📌 Версия:** `{config.neira_version}`\n\n"

                if config.include_patterns:
                    report += "### ✅ Include паттерны\n\n"
                    for pattern in config.include_patterns:
                        report += f"- `{pattern}`\n"
                    report += "\n"

                if config.exclude_patterns:
                    report += "### ❌ Exclude паттерны\n\n"
                    for pattern in config.exclude_patterns:
                        report += f"- `{pattern}`\n"
                    report += "\n"

                report += "## 🚀 Статус автозагрузки\n\n"
                report += "✅ **Конфигурация будет автоматически применяться** при использовании:\n"
                report += "- `get_context` - генерация контекста\n"
                report += "- `get_analyze` - AI анализ кода\n"
                report += "- `gen_docs` - генерация документации\n\n"

        else:
            report += "## ❌ Конфигурация не найдена\n\n"
            report += "В проекте отсутствуют файлы конфигурации Neira.\n\n"
            report += "**📝 Рекомендация:** Используйте `set_filters` для автоматической настройки фильтров.\n\n"

            report += "### 🔧 Поддерживаемые файлы конфигурации:\n\n"
            report += "- `.neira` - JSON файл с полной конфигурацией\n"
            report += "- `.neira/` - папка с отдельными файлами настроек\n"
            report += "- `.neiraignore` - простой файл исключений (аналог .gitignore)\n\n"

        return [TextContent(type="text", text=report)]

    except Exception as e:
        logger.error(f"Error in project_config tool: {e}")
        return [TextContent(type="text", text=f"❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")]

@tool_handler("gen_docs")
async def gen_docs_tool(arguments: dict) -> list[TextContent]:
    """
    Автоматическая генерация и обновление документации проекта

    Реализует полный цикл по инструкции @DOCS_MANAGER.md:
    - Сканирует проект на наличие сырых материалов (отчёты, длинные файлы)
    - Извлекает знания и проверяет актуальность
    - Сжимает и структурирует документацию
    - Обновляет changelog из git-истории
    - Архивирует обработанные файлы

    Args:
        arguments: Параметры генерации документации

    Returns:
        list[TextContent]: Отчёт о выполненной работе
    """
    try:
        # ИСПРАВЛЕНО: Валидация пути для безопасности
        path_str = arguments.get('path', '.')
        try:
            validated_path = validate_project_path(path_str)
            arguments['path'] = str(validated_path)
        except PathValidationError as e:
            return [TextContent(type="text", text=f"❌ ОШИБКА БЕЗОПАСНОСТИ: {str(e)}")]

        # ИСПРАВЛЕНО: Используем thread-safe service container
        from .docs_generator import DocsGenerator
        docs_generator = get_cached_service(DocsGenerator)

        logger.info(f"Starting documentation generation for path: {validated_path}")

        # Делегируем выполнение специализированному модулю
        result_text = await docs_generator.generate_docs(**arguments)
        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        logger.error(f"Error in documentation generation: {e}")
        return [TextContent(type="text", text=f"❌ ОШИБКА ГЕНЕРАЦИИ ДОКУМЕНТАЦИИ: {str(e)}")]

def create_server() -> Server:
    """
    Создает и возвращает экземпляр MCP сервера для использования в отладочных скриптах

    Returns:
        Server: Настроенный экземпляр MCP сервера
    """
    return app

async def main():
    """
    Главная точка входа для MCP сервера.

    Инициализирует stdio соединение и запускает сервер для обработки
    запросов от MCP клиентов (Claude Desktop, VS Code, etc).
    """
    # ИСПРАВЛЕНИЕ: Упрощенная инициализация без сложного логирования
    try:
        # Простая загрузка переменных окружения без детального логирования
        from .ai_utils import load_env_file
        load_env_file()

        # Запускаем MCP сервер
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    except Exception as e:
        # Минимальное логирование ошибок
        import sys
        print(f"MCP server error: {e}", file=sys.stderr)
        raise

if __name__ == "__main__":
    asyncio.run(main())

"""
📚 Neira Code Analyzer MCP Server

Профессиональный анализатор кода с шаблонами для различных типов анализа.

🔗 Подробная документация: docs/help/quickstart.md
        🛠️ Инструменты: set_filters, get_context, get_templates, get_analyze

Примеры использования и рабочие процессы смотрите в файле quickstart.md
"""
