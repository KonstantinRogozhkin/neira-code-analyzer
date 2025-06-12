#!/usr/bin/env python3
"""
Скрипт для диагностики проблем с импортами
"""

print("🔍 Testing imports...")

try:
    from src.neira_code_analyzer.main import app
    print("✅ Main module imported successfully")
except Exception as e:
    print(f"❌ Main module import error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

try:
    from src.neira_code_analyzer.context_generator import context_generator
    print("✅ context_generator imported successfully")
except Exception as e:
    print(f"❌ context_generator import error: {e}")
    import traceback
    traceback.print_exc()

try:
    from src.neira_code_analyzer.template_manager import template_manager
    print("✅ template_manager imported successfully")
except Exception as e:
    print(f"❌ template_manager import error: {e}")
    import traceback
    traceback.print_exc()

try:
    from src.neira_code_analyzer.ai_analyzer import ai_analyzer
    print("✅ ai_analyzer imported successfully")
except Exception as e:
    print(f"❌ ai_analyzer import error: {e}")
    import traceback
    traceback.print_exc()

print("🔍 Testing MCP components...")

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
    print("✅ MCP imports successful")
except Exception as e:
    print(f"❌ MCP import error: {e}")
    import traceback
    traceback.print_exc()

print("✅ All imports tested!") 