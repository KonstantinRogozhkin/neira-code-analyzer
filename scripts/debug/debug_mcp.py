#!/usr/bin/env python3
"""
Минимальный отладочный MCP сервер для диагностики проблем подключения
"""

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Создаем минимальный MCP сервер
debug_app = Server("debug-neira")

@debug_app.list_tools()
async def list_tools() -> list[Tool]:
    """Возвращает один простой инструмент для теста"""
    return [
        Tool(
            name="test_tool",
            description="Простой тестовый инструмент",
            inputSchema={
                "type": "object", 
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Тестовое сообщение"
                    }
                }
            }
        )
    ]

@debug_app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Обрабатывает вызовы инструментов"""
    if name == "test_tool":
        message = arguments.get("message", "Hello World!")
        return [TextContent(type="text", text=f"Debug response: {message}")]
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    """Главная функция отладочного сервера"""
    async with stdio_server() as (read_stream, write_stream):
        await debug_app.run(read_stream, write_stream, debug_app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main()) 