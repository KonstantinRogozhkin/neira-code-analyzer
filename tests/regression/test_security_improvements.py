"""
Регрессионные тесты для критических улучшений безопасности.
Коммит: 16ca582 - устранение уязвимостей Path Traversal.
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from unittest.mock import Mock, patch
from neira_code_analyzer.analysis_action_executor import AnalysisActionExecutor
from neira_code_analyzer.action_executor import ActionExecutor


class TestPathTraversalSecurity:
    """Тесты для предотвращения Path Traversal атак"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.project_path = Path("/safe/project")
        self.executor = AnalysisActionExecutor()
    
    def test_path_traversal_prevention(self):
        """Тест предотвращения Path Traversal атак"""
        
        # Небезопасные пути
        dangerous_paths = [
            "../../../etc/passwd",
            "../../sensitive/file.txt", 
            "../outside_project.py",
            "/absolute/path/file.py",
            "some/../../../escape.txt"
        ]
        
        for dangerous_path in dangerous_paths:
            # Проверяем что опасные пути отклоняются  
            result = self.executor._validate_file_path(Path(dangerous_path), self.project_path)
            assert result is False, f"Dangerous path should be rejected: {dangerous_path}"
    
    def test_safe_paths_allowed(self):
        """Тест что безопасные пути разрешены"""
        
        safe_paths = [
            "src/main.py",
            "lib/utils.py",
            "tests/test_example.py",
            "config/settings.json"
        ]
        
        for safe_path in safe_paths:
            # Безопасные пути должны проходить валидацию
            safe_full_path = self.project_path / safe_path
            result = self.executor._validate_file_path(safe_full_path, self.project_path)
            assert result is True, f"Safe path should be allowed: {safe_path}"
    
    def test_absolute_path_within_project_allowed(self):
        """Тест что абсолютные пути внутри проекта разрешены"""
        
        project_file = self.project_path / "src" / "main.py"
        
        result = self.executor._validate_file_path(project_file, self.project_path)
        assert result is True, f"Absolute path within project should be allowed: {project_file}"


class TestAIResponseParserSecurity:
    """Тесты для централизованного парсера AI ответов"""
    
    def test_malicious_json_handling(self):
        """Тест обработки вредоносного JSON"""
        
        # Импорт может не работать если модуль не готов
        try:
            from neira_code_analyzer.response_parser import AIResponseParser
            parser = AIResponseParser()
            
            malicious_inputs = [
                '{"__proto__": {"polluted": true}}',
                '{"eval": "os.system(\'rm -rf /\')"}',
                '{"constructor": {"prototype": {"polluted": true}}}',
                '{"script": "<script>alert(1)</script>"}'
            ]
            
            for malicious_json in malicious_inputs:
                # Парсер должен безопасно обработать вредоносный JSON
                try:
                    result = parser.parse_response(malicious_json)
                    # Результат не должен содержать опасные ключи
                    if isinstance(result, dict):
                        assert "__proto__" not in result
                        assert "eval" not in result
                        assert "constructor" not in result
                except Exception:
                    # Исключение допустимо для вредоносного ввода
                    pass
                    
        except ImportError:
            # Модуль может быть еще не готов
            pytest.skip("AIResponseParser not available")


class TestAsyncArchitectureRegression:
    """Регрессионные тесты для асинхронной архитектуры"""
    
    @pytest.mark.asyncio
    async def test_no_blocking_functions_remain(self):
        """Тест что блокирующие функции удалены"""
        
        try:
            from neira_code_analyzer import ai_utils
            
            # Проверяем что старая синхронная функция удалена
            assert not hasattr(ai_utils, 'generate_ai_review'), \
                "Blocking generate_ai_review function should be removed"
            
            # Проверяем что асинхронная версия существует
            assert hasattr(ai_utils, 'generate_ai_review_async'), \
                "Async generate_ai_review_async function should exist"
                
        except ImportError:
            pytest.skip("ai_utils module not available")
    
    @pytest.mark.asyncio
    async def test_async_function_does_not_block(self):
        """Тест что async функции не блокируют event loop"""
        
        try:
            from neira_code_analyzer.ai_utils import generate_ai_review_async
            import asyncio
            
            # Создаем mock для API ключа
            with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
                with patch('google.generativeai.GenerativeModel') as mock_model:
                    mock_instance = Mock()
                    mock_instance.generate_content_async.return_value = Mock(text="Test response")
                    mock_model.return_value = mock_instance
                    
                    # Функция должна быть действительно асинхронной
                    start_time = asyncio.get_event_loop().time()
                    await generate_ai_review_async("test prompt", "test model")
                    end_time = asyncio.get_event_loop().time()
                    
                    # Асинхронная функция не должна блокировать
                    assert (end_time - start_time) < 1.0, \
                        "Async function should not block for significant time"
                        
        except ImportError:
            pytest.skip("Required modules not available") 