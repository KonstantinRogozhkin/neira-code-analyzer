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

# ИСПРАВЛЕНО: Команда для запуска MCP сервера (централизована в pyproject.toml)
# Использует: [tool.rye.scripts] serve = "python -m src.neira_code_analyzer.main"
SERVER_START_COMMAND = ("uv", "run", "python", "-m", "src.neira_code_analyzer.main")
MINIMAL_SERVER_COMMAND = ("uv", "run", "python", "tools/minimal_mcp_test.py")

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

def _get_server_command(use_minimal: bool = False) -> tuple:
    """Возвращает команду для запуска сервера"""
    return MINIMAL_SERVER_COMMAND if use_minimal else SERVER_START_COMMAND

async def _start_mcp_server(use_minimal: bool = False) -> Optional[asyncio.subprocess.Process]:
    """
    Запускает MCP сервер используя константу SERVER_START_COMMAND
    
    Args:
        use_minimal: Если True, запускает минимальный тестовый сервер
    
    Returns:
        Процесс сервера или None при ошибке
    """
    try:
        command = _get_server_command(use_minimal)
        server_type = "минимальный тестовый" if use_minimal else "основной"
        print(f"🚀 Запуск {server_type} MCP сервера...")
        
        # Используем выбранную команду
        # ИСПРАВЛЕНИЕ: Перенаправляем stderr в stdout для диагностики
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT  # Перенаправляем stderr в stdout
        )
        
        print(f"✅ Сервер запущен (PID: {process.pid})")
        
        # Ждем немного чтобы сервер запустился
        await asyncio.sleep(0.5)
        
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

async def _read_server_logs(process: asyncio.subprocess.Process) -> str:
    """
    Читает доступные логи из stdout/stderr сервера
    
    Returns:
        str: Логи сервера
    """
    logs = ""
    try:
        # Пытаемся прочитать все доступные данные без блокировки
        while True:
            try:
                line = await asyncio.wait_for(process.stdout.readline(), timeout=0.1)
                if not line:
                    break
                logs += line.decode().strip() + "\n"
            except asyncio.TimeoutError:
                break
    except Exception as e:
        logs += f"Ошибка чтения логов: {e}\n"
    
    return logs

async def _test_tools_list(process: asyncio.subprocess.Process) -> bool:
    """
    Тестирует получение списка инструментов
    
    Returns:
        True если получение списка успешно
    """
    print("🔧 Запрос списка инструментов...")
    tools_request = _build_tools_request()
    tools_response = await send_mcp_request(process, tools_request)
    
    # ИСПРАВЛЕНИЕ: Если произошел таймаут, читаем логи сервера
    if not tools_response:
        print("🔍 Чтение логов сервера для диагностики...")
        server_logs = await _read_server_logs(process)
        if server_logs:
            print("📄 Логи сервера:")
            print(server_logs)
        else:
            print("📄 Логи сервера пусты")
        return False
    
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

async def test_mcp_server(use_minimal: bool = False):
    """Основная функция тестирования MCP сервера"""
    server_type = "минимального тестового" if use_minimal else "основного"
    print(f"🧪 Тестирование {server_type} MCP сервера neira-code-analyzer\n")
    
    # Запускаем сервер
    process = await _start_mcp_server(use_minimal)
    if not process:
        return False
    
    try:
        # Тестируем инициализацию
        init_success = await _test_initialization(process)
        if not init_success:
            return False
            
        # Тестируем получение списка инструментов
        tools_success = await _test_tools_list(process)
        
        print(f"\n📊 Результат тестирования {server_type} сервера:")
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
    import sys
    
    # Проверяем аргументы командной строки
    use_minimal = len(sys.argv) > 1 and sys.argv[1] == "--minimal"
    
    try:
        success = asyncio.run(test_mcp_server(use_minimal))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 