#!/usr/bin/env python3
"""
Отладочный скрипт для проверки доступных MCP инструментов
"""

# Исправлено: убран sys.path хак - используем правильный импорт из корня проекта

async def debug_tools():
    """Проверяем какие инструменты доступны"""

    print("🔍 Проверяем доступные MCP инструменты...")

    try:
        from src.neira_code_analyzer.main import list_tools

        # Получаем список инструментов
        tools = await list_tools()

        print(f"✅ Найдено {len(tools)} инструментов:")

        for i, tool in enumerate(tools, 1):
            print(f"\n{i}. 📋 **{tool.name}**")
            print(f"   📝 Описание: {tool.description[:100]}...")

            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                properties = tool.inputSchema.get('properties', {})
                print(f"   🔧 Параметров: {len(properties)}")

                for param_name, param_info in properties.items():
                    param_type = param_info.get('type', 'unknown')
                    param_desc = param_info.get('description', 'No description')[:50]
                    print(f"      - {param_name} ({param_type}): {param_desc}...")

        return tools

    except Exception as e:
        print(f"❌ Ошибка при получении инструментов: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    import asyncio
    asyncio.run(debug_tools())
