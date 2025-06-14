"""
Унифицированная обработка ошибок
Устраняет дублирование кода обработки ошибок между модулями
"""

import logging
import traceback
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class BaseServiceError(Exception):
    """Базовая ошибка сервиса"""
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class ValidationError(BaseServiceError):
    """Ошибка валидации данных"""
    pass

class SecurityError(BaseServiceError):
    """Ошибка безопасности"""
    pass

class ServiceUnavailableError(BaseServiceError):
    """Сервис недоступен"""
    pass

def handle_errors(
    default_message: str = "Произошла ошибка",
    log_traceback: bool = True,
    return_error_response: bool = True
):
    """
    Декоратор для унифицированной обработки ошибок

    Args:
        default_message: Сообщение по умолчанию для пользователя
        log_traceback: Записывать ли traceback в лог
        return_error_response: Возвращать ли форматированный ответ об ошибке
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except BaseServiceError as e:
                # Обрабатываем кастомные ошибки сервиса
                error_msg = f"❌ {e.message}"
                if e.details:
                    error_msg += f"\n\n**Детали:** {e.details}"

                logger.error(f"Service error in {func.__name__}: {e.message}")
                if log_traceback:
                    logger.debug(f"Traceback: {traceback.format_exc()}")

                return error_msg if return_error_response else None

            except Exception as e:
                # Обрабатываем неожиданные ошибки
                error_msg = f"❌ {default_message}: {str(e)}"

                logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                if log_traceback:
                    logger.error(f"Traceback: {traceback.format_exc()}")

                return error_msg if return_error_response else None

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseServiceError as e:
                # Обрабатываем кастомные ошибки сервиса
                error_msg = f"❌ {e.message}"
                if e.details:
                    error_msg += f"\n\n**Детали:** {e.details}"

                logger.error(f"Service error in {func.__name__}: {e.message}")
                if log_traceback:
                    logger.debug(f"Traceback: {traceback.format_exc()}")

                return error_msg if return_error_response else None

            except Exception as e:
                # Обрабатываем неожиданные ошибки
                error_msg = f"❌ {default_message}: {str(e)}"

                logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                if log_traceback:
                    logger.error(f"Traceback: {traceback.format_exc()}")

                return error_msg if return_error_response else None

        # Возвращаем правильную обертку в зависимости от типа функции
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

class BaseService:
    """
    Базовый класс для сервисов с унифицированной обработкой ошибок
    """

    def __init__(self, service_name: str = None):
        self.service_name = service_name or self.__class__.__name__
        self.logger = logging.getLogger(f"{__name__}.{self.service_name}")

    def _validate_path(self, path: str) -> Path:
        """Валидация пути с использованием path_validator"""
        try:
            from .path_validator import validate_project_path
            return validate_project_path(path)
        except Exception as e:
            raise ValidationError(f"Invalid path: {path}", {"original_error": str(e)})

    def _log_operation(self, operation: str, details: dict[str, Any] = None):
        """Логирование операции"""
        details_str = f" | {details}" if details else ""
        self.logger.info(f"{self.service_name}: {operation}{details_str}")

    def _handle_critical_error(self, error: Exception, context: str = ""):
        """Обработка критических ошибок"""
        context_str = f" in {context}" if context else ""
        self.logger.critical(f"Critical error{context_str}: {str(error)}")
        raise ServiceUnavailableError(
            f"Service {self.service_name} is temporarily unavailable",
            {"context": context, "original_error": str(error)}
        )

def create_error_response(error_type: str, message: str, details: dict[str, Any] = None) -> str:
    """
    Создание стандартизированного ответа об ошибке

    Args:
        error_type: Тип ошибки (SECURITY, VALIDATION, SERVICE, etc.)
        message: Сообщение об ошибке
        details: Дополнительные детали

    Returns:
        str: Форматированный ответ об ошибке
    """
    response = f"# ❌ {error_type} ОШИБКА\n\n"
    response += f"**Описание:** {message}\n\n"

    if details:
        response += "**Детали:**\n"
        for key, value in details.items():
            response += f"- **{key}:** {value}\n"
        response += "\n"

    response += "**Рекомендуемые действия:**\n"
    if error_type == "SECURITY":
        response += "- Проверьте правильность переданных путей\n"
        response += "- Убедитесь, что у вас есть права доступа к файлам\n"
    elif error_type == "VALIDATION":
        response += "- Проверьте правильность переданных параметров\n"
        response += "- Используйте корректные форматы данных\n"
    elif error_type == "SERVICE":
        response += "- Перезапустите сервис\n"
        response += "- Проверьте подключение к внешним сервисам\n"
    else:
        response += "- Обратитесь к документации\n"
        response += "- Проверьте логи для дополнительной информации\n"

    response += "\n---\n*neira-code-analyzer - Система обработки ошибок*"

    return response
