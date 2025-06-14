"""
Юнит-тесты для ai_utils.py - асинхронные AI вызовы

Тестирует:
- generate_ai_review_async() - асинхронная версия
- generate_ai_review() - синхронная версия (обратная совместимость)
- check_api_key() - проверка API ключа
- load_env_file() - загрузка переменных окружения
"""

import asyncio
import os
from unittest.mock import MagicMock, patch

import pytest
from src.neira_code_analyzer.ai_utils import check_api_key, generate_ai_review_async, load_env_file


class TestAsyncAIFunctions:
    """Тесты асинхронных AI функций"""

    @pytest.mark.asyncio
    async def test_generate_ai_review_async_success(self):
        """Тест успешного асинхронного AI вызова"""
        # Arrange
        test_prompt = "Test prompt for analysis"
        test_model = "gemini-2.5-pro-preview-06-05"
        expected_response = "Test AI analysis response"

        with patch('src.neira_code_analyzer.ai_utils.check_api_key', return_value="test_api_key"), \
             patch('src.neira_code_analyzer.ai_utils._ai_client_singleton.get_client') as mock_get_client:

            # Мокируем клиент через singleton
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            # Мокируем ответ от API
            mock_response = MagicMock()
            mock_response.text = expected_response

            # Мокируем generate_content как синхронную функцию для run_in_executor
            mock_client.models.generate_content.return_value = mock_response

            # Act
            result = await generate_ai_review_async(test_prompt, test_model)

            # Assert
            assert result == expected_response
            mock_client.models.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_ai_review_async_api_key_error(self):
        """Тест обработки ошибки отсутствия API ключа"""
        # Arrange
        test_prompt = "Test prompt"

        # Убираем все API ключи из окружения и мокируем check_api_key чтобы вызвать ошибку
        with patch.dict(os.environ, {}, clear=True), \
             patch('src.neira_code_analyzer.ai_utils.check_api_key', side_effect=ValueError("API ключ не найден")):
            # Act & Assert
            # Ошибка оборачивается в Exception с префиксом "Ошибка при вызове Google AI API"
            with pytest.raises(Exception, match="Ошибка при вызове Google AI API: API ключ не найден"):
                await generate_ai_review_async(test_prompt)

    @pytest.mark.asyncio
    async def test_generate_ai_review_async_api_error(self):
        """Тест обработки ошибки API"""
        # Arrange
        test_prompt = "Test prompt"

        with patch('src.neira_code_analyzer.ai_utils.check_api_key', return_value="test_key"), \
             patch('src.neira_code_analyzer.ai_utils._ai_client_singleton.get_client') as mock_get_client:

            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.models.generate_content.side_effect = Exception("API Error")

            # Act & Assert
            with pytest.raises(Exception, match="Ошибка при вызове Google AI API"):
                await generate_ai_review_async(test_prompt)

    @pytest.mark.asyncio
    async def test_generate_ai_review_async_empty_response(self):
        """Тест обработки пустого ответа от API"""
        # Arrange
        test_prompt = "Test prompt"

        with patch('src.neira_code_analyzer.ai_utils.check_api_key', return_value="test_key"), \
             patch('src.neira_code_analyzer.ai_utils._ai_client_singleton.get_client') as mock_get_client:

            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            # Мокируем пустой ответ
            mock_response = MagicMock()
            mock_response.text = None
            mock_client.models.generate_content.return_value = mock_response

            # Act & Assert
            with pytest.raises(Exception, match="Получен пустой ответ от Google AI API"):
                await generate_ai_review_async(test_prompt)




class TestAPIKeyValidation:
    """Тесты проверки API ключа"""

    def test_check_api_key_google_api_key(self):
        """Тест успешной проверки GOOGLE_API_KEY"""
        # Arrange
        test_key = "test_google_api_key"

        with patch.dict(os.environ, {'GOOGLE_API_KEY': test_key}, clear=True):
            # Act
            result = check_api_key()

            # Assert
            assert result == test_key

    def test_check_api_key_gemini_api_key(self):
        """Тест успешной проверки GEMINI_API_KEY"""
        # Arrange
        test_key = "test_gemini_api_key"

        with patch.dict(os.environ, {'GEMINI_API_KEY': test_key}, clear=True):
            # Act
            result = check_api_key()

            # Assert
            assert result == test_key

    def test_check_api_key_neira_api_key(self):
        """Тест успешной проверки NEIRA_API_KEY (обратная совместимость)"""
        # Arrange
        test_key = "test_neira_api_key"

        with patch.dict(os.environ, {'NEIRA_API_KEY': test_key}, clear=True):
            # Act
            result = check_api_key()

            # Assert
            assert result == test_key

    def test_check_api_key_priority_order(self):
        """Тест приоритета переменных окружения"""
        # Arrange - GOOGLE_API_KEY должен иметь приоритет
        google_key = "google_key"
        gemini_key = "gemini_key"
        neira_key = "neira_key"

        with patch.dict(os.environ, {
            'GOOGLE_API_KEY': google_key,
            'GEMINI_API_KEY': gemini_key,
            'NEIRA_API_KEY': neira_key
        }, clear=True):
            # Act
            result = check_api_key()

            # Assert
            assert result == google_key

    def test_check_api_key_missing_all_keys(self):
        """Тест ошибки при отсутствии всех API ключей"""
        # Arrange
        with patch.dict(os.environ, {}, clear=True):
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                check_api_key()

            error_message = str(exc_info.value)
            assert "КРИТИЧЕСКАЯ ОШИБКА: API ключ Google AI не найден" in error_message
            assert "https://ai.google.dev/" in error_message
            assert "GOOGLE_API_KEY" in error_message


class TestEnvironmentLoading:
    """Тесты загрузки переменных окружения"""

    def test_load_env_file_success(self):
        """Тест успешной загрузки .env файла"""
        # Arrange
        with patch('dotenv.load_dotenv', return_value=True) as mock_load_dotenv:
            # Act
            result = load_env_file()

            # Assert
            assert result is True
            mock_load_dotenv.assert_called_once()

    def test_load_env_file_not_found(self):
        """Тест когда .env файл не найден"""
        # Arrange
        with patch('dotenv.load_dotenv', return_value=False) as mock_load_dotenv:
            # Act
            result = load_env_file()

            # Assert
            assert result is False
            mock_load_dotenv.assert_called_once()

    def test_load_env_file_import_error(self):
        """Тест обработки ошибки импорта python-dotenv"""
        # Arrange
        with patch('builtins.__import__', side_effect=ImportError("No module named 'dotenv'")):
            # Act
            result = load_env_file()

            # Assert
            assert result is False

    def test_load_env_file_general_error(self):
        """Тест обработки общих ошибок при загрузке .env"""
        # Arrange
        with patch('dotenv.load_dotenv', side_effect=Exception("General error")):
            # Act
            result = load_env_file()

            # Assert
            assert result is False


class TestAsyncArchitecture:
    """Тесты архитектурных аспектов асинхронности"""

    @pytest.mark.asyncio
    async def test_async_function_does_not_block_event_loop(self):
        """Тест что асинхронная функция не блокирует event loop"""
        # Arrange
        start_time = asyncio.get_event_loop().time()

        with patch('src.neira_code_analyzer.ai_utils.check_api_key', return_value="test_key"), \
             patch('src.neira_code_analyzer.ai_utils._ai_client_singleton.get_client') as mock_get_client:

            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            # Симулируем медленный API вызов
            def slow_api_call(*args, **kwargs):
                import time
                time.sleep(0.1)  # 100ms задержка
                mock_response = MagicMock()
                mock_response.text = "response"
                return mock_response

            mock_client.models.generate_content.side_effect = slow_api_call

            # Act - запускаем несколько асинхронных вызовов параллельно
            tasks = [
                generate_ai_review_async("prompt1"),
                generate_ai_review_async("prompt2"),
                generate_ai_review_async("prompt3")
            ]

            results = await asyncio.gather(*tasks)

            # Assert
            end_time = asyncio.get_event_loop().time()
            execution_time = end_time - start_time

            # Если бы вызовы были синхронными, время выполнения было бы ~300ms
            # С асинхронностью должно быть значительно меньше
            assert len(results) == 3
            assert all(result == "response" for result in results)
            # Проверяем что время выполнения разумное (не более 200ms для 3 параллельных вызовов)
            assert execution_time < 0.2
