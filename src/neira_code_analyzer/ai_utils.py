"""
Neira Utilities Module
Общие утилиты для работы с Neira сервисами

Этот модуль содержит общие функции для работы с Neira,
чтобы избежать циклических зависимостей между модулями.

АРХИТЕКТУРНОЕ УЛУЧШЕНИЕ: Добавлена поддержка асинхронных AI вызовов
для предотвращения блокировки event loop в асинхронной архитектуре.
"""

import asyncio
import os
import threading
from typing import Optional

import httpx
from google import genai
from google.genai import types


def load_env_file():
    """
    Загружает переменные окружения из .env файла

    ИСПРАВЛЕНО: Упрощено для использования встроенного поиска dotenv
    Стандартный load_dotenv() уже эффективно ищет файл в текущей и родительских директориях.
    """
    try:
        from dotenv import load_dotenv

        # ИСПРАВЛЕНО: Используем единственный вызов load_dotenv() - он сам найдет .env файл
        if load_dotenv():
            print("✅ Загружены переменные окружения из .env")
            return True
        else:
            print("⚠️ .env файл не найден или пустой")
            return False

    except ImportError:
        print("⚠️ python-dotenv не установлен, переменные окружения не загружены")
        return False
    except Exception:
        print("⚠️ Ошибка при загрузке .env файла: {e}")
        return False

# load_env_file() убран из автоматического импорта - теперь вызывается явно при старте сервера

# ИСПРАВЛЕНО: Singleton для AI клиента с connection pooling
class AIClientSingleton:
    """
    Thread-safe singleton для AI клиента с переиспользованием соединений
    Решает проблему создания новых соединений для каждого запроса
    """
    _instance: Optional['AIClientSingleton'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._client: genai.Client | None = None
            self._http_client: httpx.AsyncClient | None = None
            self._semaphore = asyncio.Semaphore(5)  # Лимит concurrent запросов
            self._initialized = True

    def get_client(self) -> genai.Client:
        """Получить AI клиента (ленивая инициализация)"""
        if self._client is None:
            api_key = check_api_key()
            self._client = genai.Client(api_key=api_key)
        return self._client

    async def get_http_client(self) -> httpx.AsyncClient:
        """Получить HTTP клиента с connection pooling"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
        return self._http_client

    async def acquire_semaphore(self):
        """Получить семафор для rate limiting"""
        return await self._semaphore.acquire()

    def release_semaphore(self):
        """Освободить семафор"""
        self._semaphore.release()

    async def close(self):
        """Закрыть соединения"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

# Глобальный экземпляр singleton
_ai_client_singleton = AIClientSingleton()

async def generate_ai_review_async(prompt_text: str, model_name: str = "gemini-2.5-pro-preview-06-05") -> str:
    """
    ИСПРАВЛЕНО: Асинхронная функция с переиспользованием соединений и rate limiting

    Предотвращает блокировку event loop при ожидании ответа от API,
    что критично для производительности в асинхронной архитектуре.

    Args:
        prompt_text: Текст промпта с кодом для анализа
        model_name: Название модели Google AI/Gemini

    Returns:
        str: Результат анализа от Google AI

    Raises:
        ValueError: Если API ключ не установлен
        Exception: При ошибках API
    """
    # ИСПРАВЛЕНО: Rate limiting для предотвращения превышения квот
    await _ai_client_singleton.acquire_semaphore()

    try:
        # ИСПРАВЛЕНО: Используем singleton клиента с connection pooling
        client = _ai_client_singleton.get_client()

        contents = types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_text)]
        )

        config = types.GenerateContentConfig(
            response_mime_type="text/plain",
        )

        # АРХИТЕКТУРНОЕ УЛУЧШЕНИЕ: Выполняем синхронный вызов в thread pool
        # чтобы не блокировать event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,  # Используем default thread pool
            lambda: client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
        )

        # Извлекаем текст из ответа
        if response and response.text:
            return response.text.strip()
        else:
            raise Exception("Получен пустой ответ от Google AI API")

    except Exception as e:
        raise Exception(f"Ошибка при вызове Google AI API: {str(e)}")
    finally:
        # ИСПРАВЛЕНО: Всегда освобождаем семафор
        _ai_client_singleton.release_semaphore()



def check_api_key():
    """
    Центральная проверка API ключа для устранения дублирования кода

    Returns:
        str: API ключ

    Raises:
        ValueError: Если API ключ не установлен
    """
    # Пытаемся получить API ключ из различных переменных окружения
    api_key = (os.environ.get("GOOGLE_API_KEY") or
               os.environ.get("GEMINI_API_KEY") or
               os.environ.get("NEIRA_API_KEY"))  # Оставляем для обратной совместимости

    if not api_key:
        raise ValueError(
            "КРИТИЧЕСКАЯ ОШИБКА: API ключ Google AI не найден!\n\n"
            "🔑 Как получить и установить API ключ:\n"
            "1. Получите бесплатный API ключ от Google AI Studio: https://ai.google.dev/\n"
            "2. Установите API ключ одним из способов:\n"
            "   📄 В .env файле: GOOGLE_API_KEY=ваш_ключ\n"
            "   🔧 Переменная окружения:\n"
            "      • Linux/macOS: export GOOGLE_API_KEY='ваш_ключ'\n"
            "      • Windows: set GOOGLE_API_KEY=ваш_ключ\n"
            "      • PowerShell: $env:GOOGLE_API_KEY='ваш_ключ'\n\n"
            "💡 Поддерживаются также: GEMINI_API_KEY, NEIRA_API_KEY"
        )

    return api_key
