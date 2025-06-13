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

from typing import Dict, List, Optional, Any
import asyncio
import logging
import os
import json
import fnmatch
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from code2prompt_rs import Code2Prompt

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)

# Настройка простого логирования для MCP сервера
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: DI-контейнер больше не нужен
# Все зависимости создаются напрямую при необходимости

# Импорт централизованных схем для устранения дублирования MCP инструментов
from .mcp_schemas import get_tool_schema



# Создаем MCP сервер
app = Server("neira-code-analyzer")

# Реестр инструментов для декоратора
TOOL_HANDLERS = {}

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
    """
    logger.info("📋 Вызов list_tools() для регистрации инструментов")
    
    try:
        tools = []
        
        # Создаем инструменты по одному с обработкой ошибок
        tool_configs = [
            ("get_context", "Generates contextual prompts from codebases using code2prompt-rs library. Analyzes codebases and produces structured summaries optimized for Neira consumption with glob pattern filtering, custom templates, and token counting."),
            ("set_filters", "🎯 Автоматически подбирает оптимальные фильтры для проекта и сохраняет их в .neira. Анализирует структуру проекта, определяет тип (Python, React, etc.), применяет подходящие фильтры и сохраняет конфигурацию для повторного использования."),
            ("get_templates", "🎯 STEP 1: Get list of available professional templates for code analysis. Use this FIRST to see all available templates (code-review, security-audit, documentation, etc.) with descriptions and use cases. Then use 'get_context' with 'template_name' parameter."),
            ("manage_presets", "🎛️ Управление пресетами фильтров: просмотр, создание, удаление, экспорт/импорт сохраненных конфигураций фильтров. Позволяет сохранять удачные комбинации include/exclude паттернов для повторного использования в разных проектах."),
            ("get_analyze", "🔍 Автоматический анализ кода через Neira. Запускает set_filters, проверяет количество токенов (до 1 млн), подбирает оптимальные фильтры и выполняет детальный Neira анализ. Поддерживает различные шаблоны анализа. Сохраняет результаты в файл *.analyze.md."),
            ("gen_docs", "📚 Автоматическая генерация и обновление документации проекта. Сканирует файлы проекта, извлекает знания из отчётов, обновляет документацию в docs/, создаёт changelog из git-истории, сжимает длинные файлы и архивирует обработанные материалы.")
        ]
        
        # 🔒 CRITICAL TOOLS: Эти инструменты критичны для работы сервера
        critical_tools = {"get_context", "get_analyze"}
        
        for tool_name, description in tool_configs:
            try:
                schema = get_tool_schema(tool_name)
                tool = Tool(
                    name=tool_name,
                    description=description,
                    inputSchema=schema
                )
                tools.append(tool)
                logger.info(f"✅ Инструмент {tool_name} успешно создан")
            except Exception as e:
                logger.error(f"❌ Ошибка создания инструмента {tool_name}: {e}")
                
                # 🚨 FAIL-FAST: Если критический инструмент не может быть создан, останавливаем сервер
                if tool_name in critical_tools:
                    logger.critical(f"💥 КРИТИЧЕСКАЯ ОШИБКА: Не удается создать обязательный инструмент '{tool_name}'")
                    logger.critical("Сервер не может работать без критических инструментов. Проверьте схемы и зависимости.")  
                    import traceback
                    traceback.print_exc()
                    raise RuntimeError(f"Failed to create critical tool '{tool_name}': {e}")
                
                # Для некритических инструментов создаем fallback с базовой схемой
                logger.warning(f"⚠️ Создаем fallback для некритического инструмента {tool_name}")
                tool = Tool(
                    name=tool_name,
                    description=f"[FALLBACK] {description}",
                    inputSchema={"type": "object", "properties": {}}
                )
                tools.append(tool)
                logger.warning(f"⚠️ Инструмент {tool_name} создан с базовой схемой (fallback mode)")
        
        logger.info(f"📋 Возвращаем {len(tools)} инструментов")
        return tools
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в list_tools(): {e}")
        import traceback
        traceback.print_exc()
        # Возвращаем пустой список чтобы сервер не падал
        return []

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
    
    Args:
        arguments: Словарь с параметрами анализа
        
    Returns:
        list[TextContent]: Сгенерированный контекст в формате текста
    """
    # АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: Создаем context_generator напрямую
    from .context_generator import ContextGenerator
    context_generator = ContextGenerator()
    
    # Перенаправляем вызов на реализацию в context_generator
    return await context_generator.get_context(arguments)

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
    # Используем новый FilterSetupService вместо устаревшего метода из context_generator  
    from .filter_setup_service import FilterSetupService
    filter_service = FilterSetupService()
    
    # Выполняем настройку фильтров через специализированный сервис
    result = await filter_service.setup_project_filters(
        path=arguments.get("path", "."),
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
    # АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: Создаем template_manager напрямую
    from .template_manager import TemplateManager  
    template_manager = TemplateManager()
    
    try:
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
        # Получаем менеджер пресетов и делегируем ему всю логику
        from .filters import FilterPresetManager
        manager = FilterPresetManager()
        
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
    
    Args:
        arguments: Параметры анализа
        
    Returns:
        list[TextContent]: Результат анализа от Neira
    """
    # АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: Создаем ai_analyzer напрямую
    from .ai_analyzer import NeiraAnalyzer
    ai_analyzer = NeiraAnalyzer()
    
    try:
        logger.info(f"Delegating code review to ai_analyzer for path: {arguments.get('path', '.')}")
        
        # Делегируем выполнение специализированному модулю
        result_text = await ai_analyzer.perform_code_review(**arguments)
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.error(f"Error in code review tool: {e}")
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
    # АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: Создаем docs_generator напрямую
    from .docs_generator import DocsGenerator
    
    try:
        logger.info(f"Starting documentation generation for path: {arguments.get('path', '.')}")
        
        # Создаем генератор документации напрямую
        docs_generator = DocsGenerator()
        
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
    # Загружаем переменные окружения при старте сервера
    from .ai_utils import load_env_file
    load_env_file()
    
    # Добавляем базовое логирование для диагностики с ротацией
    import logging
    import logging.handlers
    import tempfile
    from pathlib import Path
    
    # Кроссплатформенный путь к логам
    log_dir = Path(tempfile.gettempdir())
    log_file = log_dir / "neira_mcp_server.log"
    
    # Создаем обработчик с ротацией: макс 5MB, 3 файла бэкапа
    file_handler = logging.handlers.RotatingFileHandler(
        str(log_file), 
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            file_handler,
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 Neira Code Analyzer MCP Server starting...")
    logger.info(f"📁 Working directory: {os.getcwd()}")
    logger.info("🔌 Waiting for MCP client connection...")
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            logger.info("✅ MCP client connected successfully!")
            await app.run(read_stream, write_stream, app.create_initialization_options())
    except Exception as e:
        logger.error(f"❌ MCP server error: {e}")
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