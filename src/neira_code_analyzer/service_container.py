"""
Service Container для dependency injection
Заменяет небезопасный глобальный кэш на thread-safe решение
"""

import logging
import threading
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ServiceContainer:
    """
    Thread-safe контейнер сервисов для dependency injection
    Заменяет глобальный кэш из main.py для соответствия MCP принципам
    """

    def __init__(self):
        self._services: dict[str, Any] = {}
        self._lock = threading.RLock()
        self._singletons: dict[str, Any] = {}

    def get_service(self, service_class: type[T], singleton: bool = True) -> T:
        """
        Получить экземпляр сервиса с поддержкой singleton паттерна

        Args:
            service_class: Класс сервиса для создания
            singleton: Использовать singleton (по умолчанию True)

        Returns:
            T: Экземпляр сервиса
        """
        service_name = service_class.__name__

        with self._lock:
            if singleton:
                if service_name not in self._singletons:
                    logger.debug(f"Creating singleton instance for {service_name}")
                    self._singletons[service_name] = service_class()
                return self._singletons[service_name]
            else:
                # Создаем новый экземпляр каждый раз
                logger.debug(f"Creating new instance for {service_name}")
                return service_class()

    def register_instance(self, service_class: type[T], instance: T) -> None:
        """
        Зарегистрировать готовый экземпляр сервиса

        Args:
            service_class: Класс сервиса
            instance: Готовый экземпляр
        """
        service_name = service_class.__name__

        with self._lock:
            self._singletons[service_name] = instance
            logger.debug(f"Registered instance for {service_name}")

    def clear_cache(self) -> None:
        """Очистить кэш сервисов (для тестирования)"""
        with self._lock:
            self._services.clear()
            self._singletons.clear()
            logger.debug("Service cache cleared")

    def get_stats(self) -> dict[str, int]:
        """Получить статистику использования сервисов"""
        with self._lock:
            return {
                'services_count': len(self._services),
                'singletons_count': len(self._singletons)
            }

# Thread-safe глобальный контейнер для использования в MCP handlers
_global_container = ServiceContainer()

def get_service_container() -> ServiceContainer:
    """Получить глобальный контейнер сервисов"""
    return _global_container

def get_cached_service(service_class: type[T], singleton: bool = True) -> T:
    """
    Удобная функция для получения сервиса из глобального контейнера

    Args:
        service_class: Класс сервиса
        singleton: Использовать singleton

    Returns:
        T: Экземпляр сервиса
    """
    return _global_container.get_service(service_class, singleton)
