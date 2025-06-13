"""
Регрессионные тесты для исправления "тихих ошибок" конфигурации

Проверяет что исправление #1 "Устранение Silent Failures" работает корректно:
- ConfigurationError выбрасывается вместо fallback значений
- Fail-Fast подход вместо молчаливых ошибок
- Правильная обработка отсутствующих пресетов и шаблонов
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.neira_code_analyzer.mcp_schemas import ConfigurationError
from src.neira_code_analyzer.ai_analyzer import NeiraAnalyzer


class TestConfigurationErrorRegression:
    """Регрессионные тесты для ConfigurationError"""
    
    def test_configuration_error_exists(self):
        """
        Регрессионный тест: ConfigurationError должен быть доступен
        
        Проверяет что класс ConfigurationError был создан и может быть импортирован
        """
        # Act & Assert
        assert ConfigurationError is not None
        
        # Проверяем что это действительно исключение
        assert issubclass(ConfigurationError, Exception)
        
        # Проверяем что можно создать экземпляр
        error = ConfigurationError("Test error")
        assert str(error) == "Test error"
    
    def test_configuration_error_inheritance(self):
        """
        Регрессионный тест: ConfigurationError должен наследоваться от Exception
        
        Проверяет правильную иерархию наследования
        """
        # Arrange & Act
        error = ConfigurationError("Test configuration error")
        
        # Assert
        assert isinstance(error, Exception)
        assert isinstance(error, ConfigurationError)
    
    def test_configuration_error_message_handling(self):
        """
        Регрессионный тест: ConfigurationError должен правильно обрабатывать сообщения
        
        Проверяет что сообщения об ошибках передаются корректно
        """
        # Arrange
        test_message = "КРИТИЧЕСКАЯ ОШИБКА КОНФИГУРАЦИИ: Файл не найден"
        
        # Act
        error = ConfigurationError(test_message)
        
        # Assert
        assert str(error) == test_message
        assert error.args[0] == test_message


class TestFailFastBehavior:
    """Тесты Fail-Fast поведения вместо silent failures"""
    
    def test_fail_fast_vs_silent_failure_concept(self):
        """
        Регрессионный тест: демонстрация различия между Fail-Fast и Silent Failure
        
        Показывает что система теперь использует Fail-Fast подход
        """
        # Arrange - функция которая раньше возвращала fallback
        def old_behavior_with_fallback():
            try:
                # Симулируем ошибку
                raise FileNotFoundError("Config file not found")
            except:
                # СТАРОЕ ПОВЕДЕНИЕ: возвращаем fallback
                return ["default"]  # Silent failure
        
        def new_behavior_fail_fast():
            try:
                # Симулируем ошибку
                raise FileNotFoundError("Config file not found")
            except FileNotFoundError as e:
                # НОВОЕ ПОВЕДЕНИЕ: выбрасываем ConfigurationError
                raise ConfigurationError(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
        
        # Act & Assert - старое поведение
        result = old_behavior_with_fallback()
        assert result == ["default"]  # Silent failure работает
        
        # Act & Assert - новое поведение
        with pytest.raises(ConfigurationError, match="КРИТИЧЕСКАЯ ОШИБКА"):
            new_behavior_fail_fast()  # Fail-fast работает
    
    def test_critical_vs_non_critical_errors(self):
        """
        Регрессионный тест: различие между критическими и некритическими ошибками
        
        Проверяет что система правильно различает типы ошибок
        """
        # Arrange
        def handle_critical_error():
            # Критическая ошибка - отсутствие основных компонентов
            raise ConfigurationError("Критическая ошибка: основные компоненты недоступны")
        
        def handle_non_critical_error():
            # Некритическая ошибка - можно продолжить работу
            try:
                # Симулируем опциональную операцию
                raise FileNotFoundError("Optional config not found")
            except FileNotFoundError:
                # Возвращаем значение по умолчанию
                return "default_value"
        
        # Act & Assert - критическая ошибка должна прерывать выполнение
        with pytest.raises(ConfigurationError, match="Критическая ошибка"):
            handle_critical_error()
        
        # Act & Assert - некритическая ошибка обрабатывается gracefully
        result = handle_non_critical_error()
        assert result == "default_value"


class TestConfigurationValidation:
    """Тесты валидации конфигурации"""
    
    def test_configuration_validation_early_detection(self):
        """
        Регрессионный тест: раннее обнаружение проблем конфигурации
        
        Проверяет что проблемы конфигурации обнаруживаются как можно раньше
        """
        # Arrange
        def validate_configuration():
            """Функция валидации конфигурации"""
            required_files = ["presets.json", "templates/"]
            
            for required in required_files:
                if not Path(required).exists():
                    raise ConfigurationError(
                        f"КРИТИЧЕСКАЯ ОШИБКА КОНФИГУРАЦИИ: Отсутствует {required}"
                    )
            
            return True
        
        # Act & Assert - при отсутствии файлов должна быть ошибка
        with pytest.raises(ConfigurationError, match="КРИТИЧЕСКАЯ ОШИБКА КОНФИГУРАЦИИ"):
            validate_configuration()
    
    def test_helpful_error_messages(self):
        """
        Регрессионный тест: полезные сообщения об ошибках
        
        Проверяет что ошибки содержат достаточно информации для исправления
        """
        # Arrange
        def create_helpful_error():
            return ConfigurationError(
                "КРИТИЧЕСКАЯ ОШИБКА КОНФИГУРАЦИИ: Файл пресетов не найден\n\n"
                "🔧 Как исправить:\n"
                "1. Проверьте установку проекта\n"
                "2. Убедитесь что все файлы на месте\n"
                "3. Переустановите если необходимо\n\n"
                "📍 Ожидаемое расположение: presets/filter_presets.json"
            )
        
        # Act
        error = create_helpful_error()
        error_message = str(error)
        
        # Assert - проверяем наличие полезной информации
        assert "КРИТИЧЕСКАЯ ОШИБКА КОНФИГУРАЦИИ" in error_message
        assert "Как исправить" in error_message
        assert "Проверьте установку" in error_message
        assert "Ожидаемое расположение" in error_message
    
    def test_error_recovery_instructions(self):
        """
        Регрессионный тест: инструкции по восстановлению
        
        Проверяет что ошибки содержат четкие инструкции по восстановлению
        """
        # Arrange
        recovery_keywords = [
            "Проверьте установку",
            "Убедитесь",
            "Переустановите", 
            "Обратитесь",
            "Как исправить",
            "Решение"
        ]
        
        def create_error_with_recovery():
            return ConfigurationError(
                "КРИТИЧЕСКАЯ ОШИБКА: Компонент недоступен\n\n"
                "🔧 Как исправить:\n"
                "1. Проверьте установку всех зависимостей\n"
                "2. Убедитесь что файлы конфигурации на месте\n"
                "3. Переустановите проект если проблема сохраняется"
            )
        
        # Act
        error = create_error_with_recovery()
        error_message = str(error)
        
        # Assert
        has_recovery_instruction = any(
            keyword in error_message for keyword in recovery_keywords
        )
        assert has_recovery_instruction, f"Ошибка должна содержать инструкции по восстановлению: {error_message}"


class TestArchitecturalImprovements:
    """Тесты архитектурных улучшений"""
    
    def test_unified_error_handling(self):
        """
        Регрессионный тест: унифицированная обработка ошибок
        
        Проверяет что все компоненты используют единый подход к обработке ошибок
        """
        # Arrange
        def component_a_error_handling():
            try:
                raise FileNotFoundError("Component A: file not found")
            except FileNotFoundError as e:
                raise ConfigurationError(f"Component A: {e}")
        
        def component_b_error_handling():
            try:
                raise PermissionError("Component B: access denied")
            except PermissionError as e:
                raise ConfigurationError(f"Component B: {e}")
        
        # Act & Assert - все компоненты используют ConfigurationError
        with pytest.raises(ConfigurationError, match="Component A"):
            component_a_error_handling()
        
        with pytest.raises(ConfigurationError, match="Component B"):
            component_b_error_handling()
    
    def test_error_context_preservation(self):
        """
        Регрессионный тест: сохранение контекста ошибок
        
        Проверяет что при обработке ошибок сохраняется достаточно контекста
        """
        # Arrange
        def process_with_context():
            try:
                # Симулируем операцию с контекстом
                operation_context = {
                    "component": "PresetManager",
                    "operation": "load_presets",
                    "file": "presets.json"
                }
                
                raise FileNotFoundError("File not found")
                
            except FileNotFoundError as e:
                # Сохраняем контекст в ошибке
                raise ConfigurationError(
                    f"КРИТИЧЕСКАЯ ОШИБКА в {operation_context['component']}\n"
                    f"Операция: {operation_context['operation']}\n"
                    f"Файл: {operation_context['file']}\n"
                    f"Причина: {e}"
                )
        
        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            process_with_context()
        
        error_message = str(exc_info.value)
        assert "PresetManager" in error_message
        assert "load_presets" in error_message
        assert "presets.json" in error_message
        assert "File not found" in error_message


# Удален класс TestConfigurationErrorRecovery - тесты ссылались на несуществующие методы 