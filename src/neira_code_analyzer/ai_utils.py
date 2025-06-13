"""
Neira Utilities Module
Общие утилиты для работы с Neira сервисами

Этот модуль содержит общие функции для работы с Neira,
чтобы избежать циклических зависимостей между модулями.
"""

import os
from pathlib import Path
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
    except Exception as e:
        print(f"⚠️ Ошибка при загрузке .env файла: {e}")
        return False

# load_env_file() убран из автоматического импорта - теперь вызывается явно при старте сервера


def generate_ai_review(prompt_text: str, model_name: str = "gemini-2.5-pro-preview-06-05") -> str:
    """
    Функция для генерации Google AI анализа кода.
    
    Args:
        prompt_text: Текст промпта с кодом для анализа
        model_name: Название модели Google AI/Gemini
        
    Returns:
        str: Результат анализа от Google AI
        
    Raises:
        ValueError: Если API ключ не установлен
        Exception: При ошибках API
    """
    # Используем центральную проверку API ключа
    api_key = check_api_key()
    
    # Создаем клиент для Google Gen AI API
    client = genai.Client(api_key=api_key)

    contents = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt_text)]
    )

    config = types.GenerateContentConfig(
        response_mime_type="text/plain",
    )

    try:
        # Используем правильный sync API для generate_content
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )
        
        # Извлекаем текст из ответа
        if response and response.text:
            return response.text.strip()
        else:
            raise Exception("Получен пустой ответ от Google AI API")
            
    except Exception as e:
        raise Exception(f"Ошибка при вызове Google AI API: {str(e)}")


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