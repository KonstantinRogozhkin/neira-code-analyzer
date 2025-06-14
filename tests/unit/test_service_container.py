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
from neira_code_analyzer.service_container import ServiceContainer, get_service_container


class TestServiceContainer:
    """Тесты для ServiceContainer"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        # Очищаем кэш для каждого теста
        container = get_service_container()
        container.clear_cache()
    
    def test_singleton_pattern(self):
        """Тест что global container - singleton"""
        
        container1 = get_service_container()
        container2 = get_service_container()
        
        assert container1 is container2, "Global container должен быть singleton"
    
    def test_thread_safety(self):
        """Тест thread-safety для получения сервисов"""
        
        # Создаем тестовый класс для сервиса
        class TestService:
            def __init__(self):
                self.value = "test"
        
        results = []
        
        def get_service():
            container = get_service_container()
            service = container.get_service(TestService, singleton=True)
            results.append(service)
        
        # Создаем несколько потоков
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=get_service)
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Все инстансы должны быть одинаковыми (singleton)
        assert len(results) == 10, "Должно быть 10 результатов"
        first_instance = results[0]
        for instance in results[1:]:
            assert instance is first_instance, "Все singleton инстансы должны быть одинаковыми"
    
    def test_register_and_get_service(self):
        """Тест регистрации и получения сервисов"""
        
        container = get_service_container()
        
        # Создаем тестовый класс
        class TestService:
            def __init__(self):
                self.value = "registered"
        
        # Регистрируем готовый экземпляр
        test_instance = TestService()
        container.register_instance(TestService, test_instance)
        
        # Получаем сервис
        retrieved_service = container.get_service(TestService)
        
        assert retrieved_service is test_instance, "Зарегистрированный сервис должен возвращаться правильно"
    
    def test_get_nonexistent_service(self):
        """Тест создания нового сервиса автоматически"""
        
        container = get_service_container()
        
        # Создаем новый класс сервиса
        class NewService:
            def __init__(self):
                self.created = True
        
        # Получаем сервис - должен создаться автоматически
        result = container.get_service(NewService)
        
        assert result is not None, "Новый сервис должен создаться автоматически"
        assert hasattr(result, 'created'), "Сервис должен быть правильно инициализирован"
    
    def test_clear_services(self):
        """Тест очистки всех сервисов"""
        
        container = get_service_container()
        
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