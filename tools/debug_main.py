#!/usr/bin/env python3
"""
Универсальный отладочный MCP сервер для Neira Code Analyzer

Объединяет функционал minimal_main.py и simple_main.py для упрощения отладки.
Запуск: python tools/debug_main.py [--mode=simple|minimal]
"""

import asyncio
import argparse
import logging
import os
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_server(mode: str = "simple") -> Server:
    """Создает MCP сервер в зависимости от режима"""
    server_name = f"neira-code-analyzer-debug-{mode}"
    app = Server(server_name)
    
    @app.list_tools()
    async def list_tools() -> list[Tool]:
        """Список инструментов в зависимости от режима"""
        logger.info(f"📋 Listing tools in {mode} mode...")
        
        base_tools = [
            Tool(
                name="hello",
                description="Simple hello world tool for testing MCP connection",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name to greet",
                            "default": "World"
                        }
                    }
                }
            )
        ]
        
        if mode == "simple":
            base_tools.extend([
                Tool(
                    name="analyze_directory",
                    description="Simple directory analysis tool",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to analyze",
                                "default": "."
                            }
                        }
                    }
                ),
                Tool(
                    name="get_templates",
                    description="List available templates",
                    inputSchema={"type": "object", "properties": {}}
                )
            ])
        elif mode == "minimal":
            base_tools.append(
                Tool(
                    name="test_connection",
                    description="Test MCP connection",
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
            )
        
        logger.info(f"✅ Returning {len(base_tools)} tools")
        return base_tools
    
    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Обработчик вызовов инструментов"""
        logger.info(f"🔧 Tool called: {name} with args: {arguments}")
        
        try:
            if name == "hello":
                name_arg = arguments.get("name", "World")
                return [TextContent(type="text", text=f"Hello, {name_arg}! MCP server ({mode} mode) is working! 🎉")]
            
            elif name == "analyze_directory":
                path = arguments.get("path", ".")
                try:
                    files = os.listdir(path)
                    result = f"📁 Directory: {path}\n📄 Files found: {len(files)}\n\nFirst 10 files:\n"
                    for i, file in enumerate(files[:10], 1):
                        result += f"{i}. {file}\n"
                    return [TextContent(type="text", text=result)]
                except Exception as e:
                    return [TextContent(type="text", text=f"❌ Error analyzing path: {e}")]
            
            elif name == "get_templates":
                templates = [
                    "code-review.hbs",
                    "documentation.hbs", 
                    "security-audit.hbs",
                    "refactoring.hbs",
                    "migration-guide.hbs",
                    "api-documentation.hbs",
                    "performance-analysis.hbs"
                ]
                
                result = "📚 **Доступные шаблоны:**\n\n"
                for template in templates:
                    result += f"- {template}\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "test_connection":
                message = arguments.get("message", "Connection test successful!")
                return [TextContent(type="text", text=f"✅ Test result: {message}")]
            
            else:
                return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]
                
        except Exception as e:
            logger.error(f"❌ Error in tool {name}: {e}")
            return [TextContent(type="text", text=f"❌ Error in tool {name}: {str(e)}")]
    
    return app

async def main():
    """Главная функция с поддержкой аргументов командной строки"""
    parser = argparse.ArgumentParser(description="Debug MCP Server for Neira Code Analyzer")
    parser.add_argument("--mode", choices=["simple", "minimal"], default="simple",
                       help="Server mode: simple (more tools) or minimal (basic tools only)")
    
    args = parser.parse_args()
    
    logger.info(f"🚀 Debug Neira Code Analyzer MCP Server starting in {args.mode} mode...")
    logger.info(f"📁 Working directory: {os.getcwd()}")
    logger.info("🔌 Waiting for MCP client connection...")
    
    app = create_server(args.mode)
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            logger.info("✅ MCP client connected successfully!")
            await app.run(read_stream, write_stream, app.create_initialization_options())
    except Exception as e:
        logger.error(f"❌ MCP server error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 