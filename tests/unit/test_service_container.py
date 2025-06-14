"""
Юнит-тесты для ServiceContainer.
Коммит: e752224 - добавление thread-safe service container для dependency injection.
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
import threading
import time
from unittest.mock import Mock, patch
from neira_code_analyzer.service_container import ServiceContainer


class TestServiceContainer:
    """Тесты для ServiceContainer"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        # Очищаем singleton для каждого теста
        ServiceContainer._instance = None
        ServiceContainer._lock = threading.Lock()
    
    def test_singleton_pattern(self):
        """Тест что ServiceContainer - singleton"""
        
        container1 = ServiceContainer.get_instance()
        container2 = ServiceContainer.get_instance()
        
        assert container1 is container2, "ServiceContainer должен быть singleton"
    
    def test_thread_safety(self):
        """Тест thread-safety singleton"""
        
        instances = []
        
        def create_instance():
            instances.append(ServiceContainer.get_instance())
        
        # Создаем несколько потоков
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_instance)
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Все инстансы должны быть одинаковыми
        first_instance = instances[0]
        for instance in instances[1:]:
            assert instance is first_instance, "Все инстансы должны быть одинаковыми"
    
    def test_register_and_get_service(self):
        """Тест регистрации и получения сервисов"""
        
        container = ServiceContainer.get_instance()
        
        # Регистрируем mock сервис
        mock_service = Mock()
        container.register('test_service', mock_service)
        
        # Получаем сервис
        retrieved_service = container.get('test_service')
        
        assert retrieved_service is mock_service, "Сервис должен возвращаться правильно"
    
    def test_get_nonexistent_service(self):
        """Тест получения несуществующего сервиса"""
        
        container = ServiceContainer.get_instance()
        
        # Получаем несуществующий сервис
        result = container.get('nonexistent_service')
        
        assert result is None, "Несуществующий сервис должен возвращать None"
    
    def test_clear_services(self):
        """Тест очистки всех сервисов"""
        
        container = ServiceContainer.get_instance()
        
        # Регистрируем несколько сервисов
        container.register('service1', Mock())
        container.register('service2', Mock())
        
        # Очищаем
        container.clear()
        
        # Проверяем что сервисы удалены
        assert container.get('service1') is None
        assert container.get('service2') is None
    
    def test_service_override(self):
        """Тест перезаписи сервиса"""
        
        container = ServiceContainer.get_instance()
        
        # Регистрируем первый сервис
        first_service = Mock()
        container.register('test_service', first_service)
        
        # Перезаписываем
        second_service = Mock()
        container.register('test_service', second_service)
        
        # Проверяем что возвращается новый сервис
        retrieved_service = container.get('test_service')
        assert retrieved_service is second_service, "Сервис должен быть перезаписан"
        assert retrieved_service is not first_service, "Старый сервис не должен возвращаться"


class TestServiceContainerIntegration:
    """Интеграционные тесты ServiceContainer"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        ServiceContainer._instance = None
        ServiceContainer._lock = threading.Lock()
    
    def test_dependency_injection_pattern(self):
        """Тест паттерна dependency injection"""
        
        container = ServiceContainer.get_instance()
        
        # Создаем mock зависимости
        mock_dependency = Mock()
        mock_dependency.process.return_value = "processed"
        
        # Регистрируем зависимость
        container.register('processor', mock_dependency)
        
        # Создаем класс который использует DI
        class ServiceUser:
            def __init__(self):
                self.processor = container.get('processor')
            
            def do_work(self):
                return self.processor.process() if self.processor else None
        
        # Тестируем
        user = ServiceUser()
        result = user.do_work()
        
        assert result == "processed", "DI должно работать корректно"
        mock_dependency.process.assert_called_once()
    
    def test_concurrent_access(self):
        """Тест конкурентного доступа к сервисам"""
        
        container = ServiceContainer.get_instance()
        container.register('shared_service', Mock())
        
        results = []
        errors = []
        
        def access_service():
            try:
                for _ in range(100):
                    service = container.get('shared_service')
                    results.append(service is not None)
                    time.sleep(0.001)  # Небольшая задержка
            except Exception as e:
                errors.append(e)
        
        # Запускаем несколько потоков
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=access_service)
            threads.append(thread)
            thread.start()
        
        # Ждем завершения
        for thread in threads:
            thread.join()
        
        # Проверяем результаты
        assert len(errors) == 0, f"Не должно быть ошибок при конкурентном доступе: {errors}"
        assert all(results), "Все обращения к сервису должны быть успешными"
    
    def test_memory_cleanup(self):
        """Тест очистки памяти"""
        
        container = ServiceContainer.get_instance()
        
        # Регистрируем много сервисов
        for i in range(100):
            container.register(f'service_{i}', Mock())
        
        # Проверяем что они все зарегистрированы
        for i in range(100):
            assert container.get(f'service_{i}') is not None
        
        # Очищаем
        container.clear()
        
        # Проверяем что память освобождена
        for i in range(100):
            assert container.get(f'service_{i}') is None 