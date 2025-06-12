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
            ("get_context", "Generates contextual prompts from codebases using code2prompt-rs library. Analyzes codebases and produces structured summaries optimized for Neira consumption with glob pattern filtering, custom templates, and token counting."),
            ("set_filters", "🎯 Автоматически подбирает оптимальные фильтры для проекта и сохраняет их в .neira. Анализирует структуру проекта, определяет тип (Python, React, etc.), применяет подходящие фильтры и сохраняет конфигурацию для повторного использования."),
            ("get_templates", "🎯 STEP 1: Get list of available professional templates for code analysis. Use this FIRST to see all available templates (code-review, security-audit, documentation, etc.) with descriptions and use cases. Then use 'get_context' with 'template_name' parameter."),
            ("manage_presets", "🎛️ Управление пресетами фильтров: просмотр, создание, удаление, экспорт/импорт сохраненных конфигураций фильтров. Позволяет сохранять удачные комбинации include/exclude паттернов для повторного использования в разных проектах."),
            ("code_review", "🔍 Автоматический анализ кода через Neira. Запускает set_filters, проверяет количество токенов (до 1 млн), подбирает оптимальные фильтры и выполняет детальный Neira-анализ. Поддерживает различные шаблоны анализа. Сохраняет результаты в файл *.analyze.md.")
        ]
        
        # 🔒 CRITICAL TOOLS: Эти инструменты критичны для работы сервера
        critical_tools = {"get_context", "code_review"}
        
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
        "set_filters": set_filters_tool,
        "get_templates": get_templates_tool,
        "manage_presets": manage_presets_tool,
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
    # Получаем context_generator через DI контейнер для устранения циклических зависимостей  
    from .container import get_context_generator
    context_generator = get_context_generator()
    
    # Используем MCP обертку для совместимости
    return await context_generator.set_filters_tool(arguments)


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

async def manage_presets_tool(arguments: dict) -> list[TextContent]:
    """
    Управление пресетами фильтров: просмотр, создание, удаление, экспорт/импорт
    
    Args:
        arguments: Параметры операции с пресетами
        
    Returns:
        list[TextContent]: Результат операции с пресетами
    """
    try:
        from .filters import get_preset_manager, list_available_presets, get_preset_details
        
        action = arguments.get("action", "list")
        
        if action == "list":
            # Список всех доступных пресетов
            presets = list_available_presets()
            
            response = "# 🎛️ Управление пресетами фильтров\n\n"
            response += f"## 📋 Доступные пресеты ({len(presets)})\n\n"
            
            for name, description in presets.items():
                # Определяем тип пресета
                if name in ["default", "aggressive", "code-only", "python-project", "web-app", "react-app", "electron-app"]:
                    preset_type = "🏗️ Встроенный"
                else:
                    preset_type = "👤 Пользовательский"
                
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
            
            return [TextContent(type="text", text=response)]
            
        elif action == "create":
            # Создание нового пресета
            name = arguments.get("name")
            include_patterns = arguments.get("include_patterns", [])
            exclude_patterns = arguments.get("exclude_patterns", [])
            description = arguments.get("description", "")
            
            if not name:
                return [TextContent(type="text", text="❌ Ошибка: необходимо указать 'name' для создания пресета")]
            
            from .filters import save_preset
            success = save_preset(name, include_patterns, exclude_patterns, description)
            
            if success:
                response = f"✅ Пресет '{name}' успешно создан!\n\n"
                response += f"**Описание:** {description}\n"
                response += f"**Include паттерны:** {include_patterns}\n"
                response += f"**Exclude паттерны:** {exclude_patterns}\n"
            else:
                response = f"❌ Ошибка создания пресета '{name}'"
                
            return [TextContent(type="text", text=response)]
            
        elif action == "details":
            # Подробная информация о пресете
            name = arguments.get("name")
            if not name:
                return [TextContent(type="text", text="❌ Ошибка: необходимо указать 'name' для получения деталей")]
            
            details = get_preset_details(name)
            if not details:
                return [TextContent(type="text", text=f"❌ Пресет '{name}' не найден")]
            
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
            
            return [TextContent(type="text", text=response)]
            
        elif action == "delete":
            # Удаление пресета
            name = arguments.get("name")
            if not name:
                return [TextContent(type="text", text="❌ Ошибка: необходимо указать 'name' для удаления")]
            
            manager = get_preset_manager()
            success = manager.delete_preset(name)
            
            if success:
                response = f"✅ Пресет '{name}' успешно удален"
            else:
                response = f"❌ Ошибка удаления пресета '{name}' (возможно, это встроенный пресет или он не существует)"
                
            return [TextContent(type="text", text=response)]
            
        elif action == "export":
            # Экспорт пресета
            name = arguments.get("name")
            file_path = arguments.get("file_path")
            
            if not name or not file_path:
                return [TextContent(type="text", text="❌ Ошибка: необходимо указать 'name' и 'file_path' для экспорта")]
            
            manager = get_preset_manager()
            success = manager.export_preset(name, file_path)
            
            if success:
                response = f"✅ Пресет '{name}' экспортирован в {file_path}"
            else:
                response = f"❌ Ошибка экспорта пресета '{name}'"
                
            return [TextContent(type="text", text=response)]
            
        elif action == "import":
            # Импорт пресета
            file_path = arguments.get("file_path")
            
            if not file_path:
                return [TextContent(type="text", text="❌ Ошибка: необходимо указать 'file_path' для импорта")]
            
            manager = get_preset_manager()
            imported_name = manager.import_preset(file_path)
            
            if imported_name:
                response = f"✅ Пресет '{imported_name}' успешно импортирован из {file_path}"
            else:
                response = f"❌ Ошибка импорта пресета из {file_path}"
                
            return [TextContent(type="text", text=response)]
            
        else:
            return [TextContent(type="text", text=f"❌ Неизвестное действие: {action}. Доступные: list, create, details, delete, export, import")]
        
    except Exception as e:
        error_msg = f"❌ Ошибка управления пресетами: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]

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
🛠️ Инструменты: set_filters, get_context, get_templates, code_review

Примеры использования и рабочие процессы смотрите в файле quickstart.md
"""