"""
AI Utilities Module
Общие утилиты для работы с AI сервисами

Этот модуль содержит общие функции для работы с AI,
чтобы избежать циклических зависимостей между модулями.
"""

import os
from pathlib import Path
from google import genai
from google.genai import types

def load_env_file():
    """
    Загружает переменные окружения из .env файла
    Использует стандартную библиотеку python-dotenv для надёжности
    """
    try:
        from dotenv import load_dotenv
        
        # Ищем .env файлы в текущей директории и корне проекта
        env_paths = [
            Path(".env"),  # Текущая директория
            Path(__file__).parent.parent.parent / ".env",  # Корень проекта
        ]
        
        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(env_path)
                print(f"✅ Загружены переменные окружения из {env_path}")
                return True
        
        # Если конкретные файлы не найдены, попробуем автопоиск
        if load_dotenv():
            print("✅ Загружены переменные окружения из .env")
            return True
            
        return False
        
    except ImportError:
        print("⚠️ python-dotenv не установлен, используем базовую загрузку")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка при загрузке .env файла: {e}")
        return False

# Автоматически загружаем .env при импорте модуля
load_env_file()


def generate_ai_review(prompt_text: str, model_name: str = "gemini-2.5-pro-preview-06-05") -> str:
    """
    Асинхронная функция для генерации AI анализа кода.
    
    Args:
        prompt_text: Текст промпта с кодом для анализа
        model_name: Название модели 
        
    Returns:
        str: Результат анализа от AI
        
    Raises:
        ValueError: Если API ключ не установлен
        Exception: При ошибках API
    """
    # Используем центральную проверку API ключа
    api_key = check_api_key()
    
    # Создаем клиент для Google Gen AI
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
            raise Exception("Получен пустой ответ от Neira AI API")
            
    except Exception as e:
        raise Exception(f"Ошибка при вызове Neira AI API: {str(e)}")


def check_api_key():
    """
    Центральная проверка API ключа для устранения дублирования кода
    
    Returns:
        str: API ключ
        
    Raises:
        ValueError: Если API ключ не установлен
    """
    api_key = os.environ.get("GOOGLE_AI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "КРИТИЧЕСКАЯ ОШИБКА: переменная окружения GOOGLE_AI_API_KEY не установлена!\n\n"
            "🔑 Как получить и установить API ключ:\n"
            "1. Получите бесплатный API ключ: https://makersuite.google.com/app/apikey\n"  
            "2. Установите API ключ одним из способов:\n"
            "   📄 В .env файле: GOOGLE_AI_API_KEY=ваш_ключ\n"
            "   🔧 Переменная окружения:\n"
            "      • Linux/macOS: export GOOGLE_AI_API_KEY='ваш_ключ'\n"
            "      • Windows: set GOOGLE_AI_API_KEY=ваш_ключ\n"
            "      • PowerShell: $env:GOOGLE_AI_API_KEY='ваш_ключ'\n\n"
            "💡 Рекомендуется использовать .env файл в корне проекта."
        )
    
    return api_key 