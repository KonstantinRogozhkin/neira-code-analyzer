#!/usr/bin/env python3

"""
Отладочный скрипт для запуска и тестирования MCP сервера neira-code-analyzer

ИСПРАВЛЕНИЕ: Вместо дублирования логики, используем реальное приложение из main.py
"""

import asyncio
import argparse
import logging
import os

from mcp.server.stdio import stdio_server

# Импортируем реальное приложение
from neira_code_analyzer.main import create_server as create_real_server

# Настройка логирования для отладки
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_neira.log')
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Главная функция с поддержкой аргументов командной строки"""
    parser = argparse.ArgumentParser(description="Debug MCP Server for Neira Code Analyzer")
    parser.add_argument("--debug", action="store_true", 
                       help="Enable debug mode with extended logging")
    parser.add_argument("--simple", action="store_true",
                       help="Run in simple mode (minimal functionality)")
    
    args = parser.parse_args()
    
    # Устанавливаем уровень логирования в зависимости от режима
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("🐛 Debug mode enabled")
    
    logger.info("🚀 Debug Neira Code Analyzer MCP Server starting...")
    logger.info(f"📁 Working directory: {os.getcwd()}")
    logger.info("🔌 Waiting for MCP client connection...")
    
    # Используем реальное приложение (DI-контейнер больше не нужен)
    app = create_real_server()
    logger.info("✅ Server initialized successfully")
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            logger.info("✅ MCP client connected successfully!")
            
            if args.debug:
                logger.debug("🔧 Running in debug mode with extended logging")
            
            await app.run(read_stream, write_stream, app.create_initialization_options())
    except Exception as e:
        logger.error(f"❌ MCP server error: {e}")
        if args.debug:
            logger.exception("Full exception traceback:")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 