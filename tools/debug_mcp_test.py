#!/usr/bin/env python3
"""
Скрипт для тестирования MCP сервера
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any, Optional

# Константы для JSON-RPC запросов
INIT_REQUEST = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "clientInfo": {
            "name": "test-client",
            "version": "1.0.0"
        }
    }
}

TOOLS_REQUEST = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
}

# Команда для запуска MCP сервера
SERVER_START_COMMAND = ("uv", "run", "python", "-m", "src.neira_code_analyzer.main")

DEFAULT_TIMEOUT = 10.0

async def _validate_mcp_response(response: Optional[Dict[str, Any]], description: str) -> bool:
    """
    Валидирует ответ от MCP сервера
    
    Args:
        response: Ответ от сервера
        description: Описание операции для логирования
        
    Returns:
        bool: True если ответ валиден
    """
    if not response:
        return False
    if "error" in response:
        print(f"❌ Ошибка в '{description}': {response.get('error', 'неизвестная ошибка')}")
        return False
    if "result" not in response:
        print(f"❌ Отсутствует 'result' в ответе '{description}'")
        return False
    return True

async def send_mcp_request(process: asyncio.subprocess.Process, 
                          request_data: Dict[str, Any], 
                          timeout: float = DEFAULT_TIMEOUT) -> Optional[Dict[str, Any]]:
    """
    Отправляет JSON-RPC запрос к MCP серверу и получает ответ
    
    Args:
        process: Процесс MCP сервера
        request_data: Данные JSON-RPC запроса
        timeout: Таймаут ожидания ответа в секундах
        
    Returns:
        Dict с ответом сервера или None при ошибке
    """
    try:
        # Отправляем запрос
        request_json = json.dumps(request_data)
        process.stdin.write(request_json.encode() + b'\n')
        await process.stdin.drain()
        
        # Получаем ответ с таймаутом
        response_line = await asyncio.wait_for(
            process.stdout.readline(), 
            timeout=timeout
        )
        
        if not response_line:
            print("❌ Пустой ответ от сервера")
            return None
            
        response_text = response_line.decode().strip()
        return json.loads(response_text)
        
    except asyncio.TimeoutError:
        print(f"❌ Таймаут ({timeout}s) при ожидании ответа")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка декодирования JSON: {e}")
        return None
    except Exception as e:
        print(f"❌ Ошибка при отправке запроса: {e}")
        return None

def _build_init_request() -> Dict[str, Any]:
    """Создает запрос инициализации MCP сервера"""
    return INIT_REQUEST.copy()

def _build_tools_request() -> Dict[str, Any]:
    """Создает запрос списка инструментов"""
    return TOOLS_REQUEST.copy()

async def _start_mcp_server() -> Optional[asyncio.subprocess.Process]:
    """
    Запускает MCP сервер используя константу SERVER_START_COMMAND
    
    Returns:
        Процесс сервера или None при ошибке
    """
    try:
        print("🚀 Запуск MCP сервера...")
        
        # Используем константу для консистентности
        process = await asyncio.create_subprocess_exec(
            *SERVER_START_COMMAND,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        print(f"✅ Сервер запущен (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        return None

async def _test_initialization(process: asyncio.subprocess.Process) -> bool:
    """
    Тестирует инициализацию MCP сервера
    
    Returns:
        True если инициализация успешна
    """
    print("📡 Отправка запроса initialize...")
    init_request = _build_init_request()
    init_response = await send_mcp_request(process, init_request)
    
    if not await _validate_mcp_response(init_response, "Инициализация"):
        return False
        
    print("✅ Инициализация успешна")
    print(f"   Версия протокола: {init_response['result'].get('protocolVersion', 'неизвестно')}")
    return True

async def _test_tools_list(process: asyncio.subprocess.Process) -> bool:
    """
    Тестирует получение списка инструментов
    
    Returns:
        True если получение списка успешно
    """
    print("🔧 Запрос списка инструментов...")
    tools_request = _build_tools_request()
    tools_response = await send_mcp_request(process, tools_request)
    
    if not await _validate_mcp_response(tools_response, "Получение списка инструментов"):
        return False
        
    if "tools" in tools_response["result"]:
        tools = tools_response["result"]["tools"]
        print(f"✅ Получен список из {len(tools)} инструментов:")
        for tool in tools:
            print(f"   - {tool.get('name', 'unnamed')}: {tool.get('description', 'без описания')}")
        return True
    else:
        print("❌ Отсутствует поле 'tools' в результате")
        return False

async def _cleanup_server(process: asyncio.subprocess.Process) -> None:
    """Корректно завершает работу сервера"""
    try:
        print("🛑 Завершение работы сервера...")
        process.terminate()
        await asyncio.wait_for(process.wait(), timeout=5.0)
        print("✅ Сервер завершен корректно")
    except asyncio.TimeoutError:
        print("⚠️ Принудительное завершение сервера...")
        process.kill()
        await process.wait()
    except Exception as e:
        print(f"❌ Ошибка при завершении сервера: {e}")

async def test_mcp_server():
    """Основная функция тестирования MCP сервера"""
    print("🧪 Тестирование MCP сервера neira-code-analyzer\n")
    
    # Запускаем сервер
    process = await _start_mcp_server()
    if not process:
        return False
    
    try:
        # Тестируем инициализацию
        init_success = await _test_initialization(process)
        if not init_success:
            return False
            
        # Тестируем получение списка инструментов
        tools_success = await _test_tools_list(process)
        
        print(f"\n📊 Результат тестирования:")
        print(f"   Инициализация: {'✅ ОК' if init_success else '❌ ОШИБКА'}")
        print(f"   Список инструментов: {'✅ ОК' if tools_success else '❌ ОШИБКА'}")
        
        overall_success = init_success and tools_success
        print(f"   Общий результат: {'✅ УСПЕХ' if overall_success else '❌ НЕУДАЧА'}")
        
        return overall_success
        
    finally:
        # Всегда завершаем сервер
        await _cleanup_server(process)

def main():
    """Точка входа для запуска тестов"""
    try:
        success = asyncio.run(test_mcp_server())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 