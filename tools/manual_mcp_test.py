#!/usr/bin/env python3
"""
Ручной MCP сервер без декораторов для отладки
"""

import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Простое логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем сервер
app = Server("manual-test")

async def manual_list_tools() -> list[Tool]:
    """Ручная функция для списка инструментов"""
    print("🔍 [DEBUG] Manual list_tools called!")
    logger.info("Loading manual tools...")
    
    tools = [
        Tool(
            name="manual_tool",
            description="Ручной тестовый инструмент",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "default": "test"}
                }
            }
        )
    ]
    
    print(f"🔍 [DEBUG] Created {len(tools)} manual tools")
    return tools

async def manual_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Ручная функция для вызова инструментов"""
    print(f"🔍 [DEBUG] Manual tool called: {name}")
    
    if name == "manual_tool":
        text = arguments.get("text", "test")
        return [TextContent(type="text", text=f"Manual response: {text}")]
    else:
        return [TextContent(type="text", text=f"Unknown manual tool: {name}")]

# Ручная регистрация обработчиков
app._list_tools_handler = manual_list_tools
app._call_tool_handler = manual_call_tool

async def main():
    """Запуск сервера"""
    print("🚀 [DEBUG] Starting manual MCP server...")
    logger.info("Starting manual server...")
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            print("✅ [DEBUG] stdio_server ready, running manual app...")
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    except Exception as e:
        print(f"❌ [DEBUG] Manual error: {e}")
        logger.error(f"Manual server error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 