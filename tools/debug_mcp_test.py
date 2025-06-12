#!/usr/bin/env python3
"""
Простой тест MCP протокола для отладки проблем с сервером
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

async def test_mcp_server():
    """Тестирует MCP сервер, отправляя базовые команды"""
    
    print("🔍 Запуск теста MCP сервера...")
    
    # Автоопределение путей
    current_dir = Path(__file__).parent.absolute()
    venv_python = current_dir / ".venv" / "bin" / "python"
    
    # Если виртуальное окружение не найдено, используем системный Python
    if not venv_python.exists():
        venv_python = "python"  # Используем системный Python
        print(f"⚠️ Виртуальное окружение не найдено, используем системный Python")
    
    # Команда для запуска сервера
    cmd = [
        str(venv_python),
        "-m", "src.neira_code_analyzer.main"
    ]
    
    cwd = str(current_dir)
    
    print(f"📂 Working directory: {cwd}")
    print(f"🚀 Command: {' '.join(cmd)}")
    
    try:
        # Запускаем процесс
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        
        print("✅ Процесс запущен")
        
        # Отправляем initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("📤 Отправляем initialize request...")
        request_str = json.dumps(init_request) + "\n"
        process.stdin.write(request_str.encode())
        await process.stdin.drain()
        
        # Читаем ответ с таймаутом
        try:
            response_line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=10.0
            )
            
            if response_line:
                response = json.loads(response_line.decode().strip())
                print("📥 Получен ответ:")
                print(json.dumps(response, indent=2))
                
                # Если инициализация прошла успешно, запрашиваем tools
                if "result" in response:
                    print("📤 Отправляем tools/list request...")
                    
                    tools_request = {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list",
                        "params": {}
                    }
                    
                    request_str = json.dumps(tools_request) + "\n"
                    process.stdin.write(request_str.encode())
                    await process.stdin.drain()
                    
                    # Читаем ответ с tools
                    tools_response_line = await asyncio.wait_for(
                        process.stdout.readline(),
                        timeout=10.0
                    )
                    
                    if tools_response_line:
                        tools_response = json.loads(tools_response_line.decode().strip())
                        print("📥 Получен список tools:")
                        print(json.dumps(tools_response, indent=2))
                        
                        if "result" in tools_response and "tools" in tools_response["result"]:
                            tools = tools_response["result"]["tools"]
                            print(f"✅ Найдено {len(tools)} инструментов:")
                            for tool in tools:
                                print(f"  - {tool['name']}")
                        else:
                            print("❌ Неожиданный формат ответа tools")
                    else:
                        print("❌ Нет ответа на tools/list")
                        
            else:
                print("❌ Нет ответа на initialize")
                
        except asyncio.TimeoutError:
            print("⏰ Таймаут ожидания ответа (10 секунд)")
        
        # Завершаем процесс
        process.terminate()
        await process.wait()
        
        print("🏁 Тест завершен")
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        if process:
            process.terminate()
            await process.wait()

if __name__ == "__main__":
    asyncio.run(test_mcp_server()) 