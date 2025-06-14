#!/usr/bin/env python3
"""
Минимальный MCP сервер для диагностики проблем
"""
import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

# Создаем минимальный сервер
app = Server("test-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Возвращает список инструментов"""
    return [
        Tool(
            name="test_tool",
            description="A simple test tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Test message"
                    }
                }
            }
        )
    ]

async def main():
    """Запуск сервера"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
