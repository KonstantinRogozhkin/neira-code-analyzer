"""
Юнит-тесты для унифицированной системы обработки ошибок.
Коммит: e752224 - добавление error_handling модуля.
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from unittest.mock import Mock, patch
from neira_code_analyzer.error_handling import (
    BaseService,
    BaseServiceError,
    ValidationError,
    SecurityError,
    ServiceUnavailableError,
    handle_errors,
    create_error_response
)


class TestBaseServiceError:
    """Тесты для базовых ошибок сервиса"""
    
    def test_base_service_error_creation(self):
        """Тест создания базовой ошибки"""
        error = BaseServiceError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}
    
    def test_base_service_error_with_details(self):
        """Тест создания ошибки с деталями"""
        details = {"field": "value", "code": 123}
        error = BaseServiceError("Test error", details)
        
        assert error.message == "Test error"
        assert error.details == details
    
    def test_validation_error_inheritance(self):
        """Тест что ValidationError наследуется от BaseServiceError"""
        error = ValidationError("Validation failed")
        
        assert isinstance(error, BaseServiceError)
        assert error.message == "Validation failed"
    
    def test_security_error_inheritance(self):
        """Тест что SecurityError наследуется от BaseServiceError"""
        error = SecurityError("Security violation")
        
        assert isinstance(error, BaseServiceError)
        assert error.message == "Security violation"
    
    def test_service_unavailable_error_inheritance(self):
        """Тест что ServiceUnavailableError наследуется от BaseServiceError"""
        error = ServiceUnavailableError("Service down")
        
        assert isinstance(error, BaseServiceError)
        assert error.message == "Service down"


class TestHandleErrorsDecorator:
    """Тесты для декоратора handle_errors"""
    
    def test_decorator_catches_base_service_error(self):
        """Тест что декоратор ловит BaseServiceError"""
        
        @handle_errors()
        def failing_function():
            raise ValidationError("Validation failed")
        
        result = failing_function()
        
        assert isinstance(result, str)
        assert "❌" in result
        assert "Validation failed" in result
    
    def test_decorator_catches_general_exception(self):
        """Тест что декоратор ловит общие исключения"""
        
        @handle_errors(default_message="Custom error message")
        def failing_function():
            raise ValueError("Something went wrong")
        
        result = failing_function()
        
        assert isinstance(result, str)
        assert "❌" in result
        assert "Custom error message" in result
    
    def test_decorator_success_case(self):
        """Тест что декоратор не мешает успешному выполнению"""
        
        @handle_errors()
        def successful_function(x, y):
            return x + y
        
        result = successful_function(2, 3)
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_decorator_with_async_function(self):
        """Тест декоратора с асинхронными функциями"""
        
        @handle_errors()
        async def async_failing_function():
            raise SecurityError("Async security error")
        
        result = await async_failing_function()
        
        assert isinstance(result, str)
        assert "❌" in result
        assert "Async security error" in result
    
    @pytest.mark.asyncio
    async def test_decorator_with_async_success(self):
        """Тест декоратора с успешной асинхронной функцией"""
        
        @handle_errors()
        async def async_successful_function():
            return "success"
        
        result = await async_successful_function()
        assert result == "success"


class TestBaseService:
    """Тесты для базового класса сервиса"""
    
    def test_base_service_initialization(self):
        """Тест инициализации базового сервиса"""
        service = BaseService("TestService")
        
        assert service.service_name == "TestService"
        assert service.logger.name.endswith("TestService")
    
    def test_base_service_default_name(self):
        """Тест автоматического имени сервиса"""
        service = BaseService()
        
        assert service.service_name == "BaseService"
    
    def test_log_operation(self):
        """Тест логирования операций"""
        service = BaseService("TestService")
        
        with patch.object(service.logger, 'info') as mock_log:
            service._log_operation("Test operation", {"key": "value"})
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0][0]
            assert "TestService" in call_args
            assert "Test operation" in call_args
    
    def test_handle_critical_error(self):
        """Тест обработки критических ошибок"""
        service = BaseService("TestService")
        
        with pytest.raises(ServiceUnavailableError) as exc_info:
            service._handle_critical_error(ValueError("Critical issue"), "test context")
        
        error = exc_info.value
        assert "temporarily unavailable" in error.message
        assert error.details["context"] == "test context"
        assert "Critical issue" in error.details["original_error"]


class TestCreateErrorResponse:
    """Тесты для создания ответов об ошибках"""
    
    def test_basic_error_response(self):
        """Тест базового ответа об ошибке"""
        response = create_error_response("TEST", "Test error message")
        
        assert "❌ TEST ОШИБКА" in response
        assert "Test error message" in response
        assert "Рекомендуемые действия" in response
    
    def test_error_response_with_details(self):
        """Тест ответа об ошибке с деталями"""
        details = {"file": "test.py", "line": 42}
        response = create_error_response("VALIDATION", "Validation error", details)
        
        assert "VALIDATION ОШИБКА" in response
        assert "Validation error" in response
        assert "file:** test.py" in response
        assert "line:** 42" in response
    
    def test_security_error_recommendations(self):
        """Тест рекомендаций для ошибок безопасности"""
        response = create_error_response("SECURITY", "Path traversal detected")
        
        assert "SECURITY ОШИБКА" in response
        assert "права доступа" in response
        assert "правильность переданных путей" in response
    
    def test_validation_error_recommendations(self):
        """Тест рекомендаций для ошибок валидации"""
        response = create_error_response("VALIDATION", "Invalid input")
        
        assert "VALIDATION ОШИБКА" in response
        assert "правильность переданных параметров" in response
        assert "корректные форматы данных" in response
    
    def test_service_error_recommendations(self):
        """Тест рекомендаций для сервисных ошибок"""
        response = create_error_response("SERVICE", "Database connection failed")
        
        assert "SERVICE ОШИБКА" in response
        assert "Перезапустите сервис" in response
        assert "подключение к внешним сервисам" in response
    
    def test_generic_error_recommendations(self):
        """Тест рекомендаций для общих ошибок"""
        response = create_error_response("UNKNOWN", "Unknown error")
        
        assert "UNKNOWN ОШИБКА" in response
        assert "документации" in response
        assert "логи" in response


class TestErrorHandlingIntegration:
    """Интеграционные тесты системы обработки ошибок"""
    
    def test_service_with_error_handling(self):
        """Тест сервиса с обработкой ошибок"""
        
        class TestService(BaseService):
            def __init__(self):
                super().__init__("TestService")
            
            @handle_errors("Service operation failed")
            def process_data(self, data):
                if not data:
                    raise ValidationError("Data is required")
                if data.get("invalid"):
                    raise SecurityError("Invalid data detected")
                return {"result": "success", "data": data}
        
        service = TestService()
        
        # Тестируем успешный случай
        result = service.process_data({"valid": True})
        assert result["result"] == "success"
        
        # Тестируем ValidationError
        result = service.process_data(None)
        assert isinstance(result, str)
        assert "❌" in result
        assert "Data is required" in result
        
        # Тестируем SecurityError
        result = service.process_data({"invalid": True})
        assert isinstance(result, str)
        assert "❌" in result
        assert "Invalid data detected" in result
    
    def test_nested_error_handling(self):
        """Тест вложенной обработки ошибок"""
        
        @handle_errors("Inner operation failed")
        def inner_operation():
            raise ValidationError("Inner validation failed")
        
        @handle_errors("Outer operation failed")
        def outer_operation():
            result = inner_operation()
            if isinstance(result, str) and "❌" in result:
                raise ServiceUnavailableError("Inner service failed")
            return result
        
        result = outer_operation()
        
        assert isinstance(result, str)
        assert "❌" in result
        assert "Inner service failed" in result 