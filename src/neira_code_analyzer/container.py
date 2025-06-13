"""
Dependency Injection Container
Централизованная система управления зависимостями для устранения циклических импортов

Этот модуль реализует паттерн Service Locator / DI Container для разрешения
циклических зависимостей между ai_analyzer, context_generator и другими модулями.
"""

from typing import Dict, Any, Optional, TypeVar, Type, Callable
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DIContainer:
    """
    Контейнер зависимостей для устранения циклических импортов
    
    Использует ленивую инициализацию и паттерн Service Locator
    для разрешения зависимостей между модулями.
    """
    
    def __init__(self):
        """Инициализация пустого контейнера"""
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._singletons: Dict[str, Any] = {}
        
    def register_factory(self, service_name: str, factory: Callable[[], Any]) -> None:
        """
        Регистрирует фабрику для создания сервиса
        
        Args:
            service_name: Название сервиса
            factory: Функция создания экземпляра сервиса
        """
        self._factories[service_name] = factory
        logger.debug(f"Registered factory for service: {service_name}")
        
    def register_singleton(self, service_name: str, instance: Any) -> None:
        """
        Регистрирует готовый экземпляр как синглтон
        
        Args:
            service_name: Название сервиса
            instance: Готовый экземпляр
        """
        self._singletons[service_name] = instance
        logger.debug(f"Registered singleton for service: {service_name}")
        
    def get(self, service_name: str) -> Any:
        """
        Получает экземпляр сервиса
        
        Args:
            service_name: Название сервиса
            
        Returns:
            Any: Экземпляр сервиса
            
        Raises:
            ValueError: Если сервис не зарегистрирован
        """
        # Сначала проверяем синглтоны
        if service_name in self._singletons:
            return self._singletons[service_name]
            
        # Потом фабрики
        if service_name in self._factories:
            # Создаем экземпляр и сохраняем как синглтон для последующих вызовов
            instance = self._factories[service_name]()
            self._singletons[service_name] = instance
            logger.debug(f"Created and cached instance for service: {service_name}")
            return instance
            
        raise ValueError(f"Service '{service_name}' not registered")
        
    def has(self, service_name: str) -> bool:
        """
        Проверяет, зарегистрирован ли сервис
        
        Args:
            service_name: Название сервиса
            
        Returns:
            bool: True если сервис зарегистрирован
        """
        return service_name in self._singletons or service_name in self._factories


# Глобальный контейнер зависимостей
container = DIContainer()


def setup_container() -> None:
    """
    Настройка зависимостей в контейнере
    
    Функция должна вызываться при запуске приложения для регистрации
    всех сервисов с их зависимостями.
    """
    logger.info("Setting up dependency injection container")
    
    # Регистрируем фабрики с ленивой инициализацией
    # Это позволяет избежать циклических импортов
    
    def create_template_manager():
        from .template_manager import TemplateManager
        return TemplateManager()
        
    def create_project_manager():
        from .project_manager import ProjectManager  
        return ProjectManager()
        
    def create_context_generator():
        from .context_generator import ContextGenerator
        return ContextGenerator()
        
    def create_ai_analyzer():
        from .ai_analyzer import NeiraAnalyzer
        return NeiraAnalyzer()
        
    def create_filter_manager():
        from .filters import FilterPresetManager
        return FilterPresetManager()
        
    def create_filter_setup_service():
        from .filter_setup_service import FilterSetupService
        return FilterSetupService()
        
    def create_docs_generator():
        from .docs_generator import DocsGenerator
        return DocsGenerator()
        
    # Регистрируем фабрики
    container.register_factory("template_manager", create_template_manager)
    container.register_factory("project_manager", create_project_manager)
    container.register_factory("context_generator", create_context_generator)
    container.register_factory("ai_analyzer", create_ai_analyzer)
    container.register_factory("filter_manager", create_filter_manager)
    container.register_factory("filter_setup_service", create_filter_setup_service)
    container.register_factory("docs_generator", create_docs_generator)
    
    logger.info("Dependency injection container setup complete")


def get_service(service_name: str) -> Any:
    """
    Удобная функция для получения сервиса из контейнера
    
    Args:
        service_name: Название сервиса
        
    Returns:
        Any: Экземпляр сервиса
    """
    return container.get(service_name)


# Удобные функции для получения конкретных сервисов
def get_template_manager():
    """Получить экземпляр TemplateManager"""
    return get_service("template_manager")


def get_project_manager():
    """Получить экземпляр ProjectManager"""
    return get_service("project_manager")


def get_context_generator():
    """Получить экземпляр ContextGenerator"""
    return get_service("context_generator")


def get_ai_analyzer():
    """Получить экземпляр NeiraAnalyzer"""
    return get_service("ai_analyzer")


def get_filter_manager():
    """Получить экземпляр FilterPresetManager"""
    return get_service("filter_manager")


def get_filter_setup_service():
    """Получить экземпляр FilterSetupService"""
    return get_service("filter_setup_service")


def get_docs_generator():
    """Получить экземпляр DocsGenerator"""
    return get_service("docs_generator") 