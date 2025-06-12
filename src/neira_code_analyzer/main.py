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

# Инициализация DI контейнера для устранения циклических зависимостей
from .container import setup_container
setup_container()

# Импорт централизованных схем для устранения дублирования MCP инструментов
from .mcp_schemas import get_tool_schema



# Создаем MCP сервер
app = Server("neira-code-analyzer")

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
            ("get_context", "Generate contextual prompts from codebases using code2prompt-rs library. Analyzes codebases and produces structured summaries optimized for AI consumption with glob pattern filtering, custom templates, and token counting."),
            ("analyze_filters", "🔍 Analyze and test file filters to optimize codebase selection for AI analysis. Shows file structure, token counts, and statistics by file types to help create perfect filters that exclude unnecessary files and reduce context size.\n\n💡 PRINCIPLE: \"Provide as little context as possible, but as much as necessary\" - максимально исключить ненужные файлы, включить только необходимые для анализа."),
            ("get_templates", "🎯 STEP 1: Get list of available professional templates for code analysis. Use this FIRST to see all available templates (code-review, security-audit, documentation, etc.) with descriptions and use cases. Then use 'get_context' with 'template_name' parameter."),
            ("code_review", "🔍 Автоматический анализ кода через Neira . Запускает analyze_filters, проверяет количество токенов (до 1 млн), подбирает оптимальные фильтры и выполняет детальный AI-анализ через Gemini AI. Поддерживает различные шаблоны анализа. Сохраняет результаты в файл *.analyze.md.")
        ]
        
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
                # Создаем инструмент с базовой схемой
                tool = Tool(
                    name=tool_name,
                    description=description,
                    inputSchema={"type": "object", "properties": {}}
                )
                tools.append(tool)
                logger.warning(f"⚠️ Инструмент {tool_name} создан с базовой схемой")
        
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
    Обработчик вызовов инструментов MCP.
    
    Args:
        name: Название инструмента для вызова
        arguments: Аргументы для инструмента
        
    Returns:
        list[TextContent]: Результат выполнения инструмента
        
    Raises:
        ValueError: Если инструмент не найден
    """
    # Словарь-диспетчер для масштабируемости
    tool_handlers = {
        "get_context": get_context_tool,
        "analyze_filters": analyze_filters_tool,
        "get_templates": get_templates_tool,
        "code_review": code_review_tool
    }
    
    handler = tool_handlers.get(name)
    if handler:
        return await handler(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

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
    # Получаем context_generator через DI контейнер для устранения циклических зависимостей
    from .container import get_context_generator
    context_generator = get_context_generator()
    
    # Перенаправляем вызов на реализацию в context_generator
    return await context_generator.get_context(arguments)

async def analyze_filters_tool(arguments: dict) -> list[TextContent]:
    """
    Анализирует и тестирует фильтры файлов для оптимизации выбора кодовой базы.
    
    💡 ПРИНЦИП: "Provide as little context as possible, but as much as necessary"
    
    Цель: МАКСИМАЛЬНО ИСКЛЮЧИТЬ ненужные файлы, ВКЛЮЧИТЬ только необходимые.
    Показывает структуру файлов, подсчет токенов и статистику по типам файлов
    для создания идеальных фильтров, отсеивающих лишний код.
    
    Args:
        arguments: Словарь с параметрами анализа фильтров
        
    Returns:
        list[TextContent]: Детальный анализ файловой структуры и рекомендации
    """
    # Получаем context_generator через DI контейнер для устранения циклических зависимостей  
    from .container import get_context_generator
    context_generator = get_context_generator()
    
    # Используем MCP обертку для совместимости
    return await context_generator.analyze_filters_tool(arguments)


async def get_templates_tool(arguments: dict) -> list[TextContent]:
    """
    Получает краткий список доступных шаблонов для анализа кода.
    
    Использует централизованную реализацию из template_manager.py
    
    Args:
        arguments: Параметры запроса (show_content для показа содержимого)
        
    Returns:
        list[TextContent]: Список шаблонов с кратким описанием
    """
    # Получаем template_manager через DI контейнер для устранения циклических зависимостей
    from .container import get_template_manager  
    template_manager = get_template_manager()
    
    try:
        show_content = arguments.get("show_content", False)
        
        logger.info("Delegating templates info to template_manager")
        
        # Делегируем выполнение специализированному модулю
        response = template_manager.get_templates_info(show_content)
        return [TextContent(type="text", text=response)]
        
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return [TextContent(type="text", text=f"❌ Ошибка при получении шаблонов: {str(e)}")]

async def code_review_tool(arguments: dict) -> list[TextContent]:
    """
    Автоматический анализ кода через Neira
    
    Использует централизованную реализацию из ai_analyzer.py
    для выполнения полного цикла анализа кода.
    
    Args:
        arguments: Параметры анализа
        
    Returns:
        list[TextContent]: Результат анализа от Neira
    """
    # Получаем ai_analyzer через DI контейнер для устранения циклических зависимостей
    from .container import get_ai_analyzer
    ai_analyzer = get_ai_analyzer()
    
    try:
        logger.info(f"Delegating code review to ai_analyzer for path: {arguments.get('path', '.')}")
        
        # Делегируем выполнение специализированному модулю
        result_text = await ai_analyzer.perform_code_review(**arguments)
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.error(f"Error in code review tool: {e}")
        return [TextContent(type="text", text=f"❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")]

async def main():
    """
    Главная точка входа для MCP сервера.
    
    Инициализирует stdio соединение и запускает сервер для обработки
    запросов от MCP клиентов (Claude Desktop, VS Code, etc).
    """
    # Добавляем базовое логирование для диагностики
    import logging
    import tempfile
    from pathlib import Path
    
    # Кроссплатформенный путь к логам
    log_dir = Path(tempfile.gettempdir())
    log_file = log_dir / "neira_mcp_server.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(str(log_file)),
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
🛠️ Инструменты: analyze_filters, get_context, get_templates, code_review

Примеры использования и рабочие процессы смотрите в файле quickstart.md
"""