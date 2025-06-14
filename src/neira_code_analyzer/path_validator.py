"""
Модуль для безопасной валидации путей
Предотвращает path traversal атаки и несанкционированный доступ к файлам
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class PathValidationError(Exception):
    """Ошибка валидации пути"""
    pass

def validate_safe_path(path_str: str | Path, base_dir: str = ".") -> Path:
    """
    Безопасная валидация пути для предотвращения path traversal атак

    Args:
        path_str: Путь для валидации
        base_dir: Базовый каталог (по умолчанию текущий)

    Returns:
        Path: Валидированный и разрешенный путь

    Raises:
        PathValidationError: При небезопасном пути
    """
    try:
        # Проверяем на подозрительные паттерны в исходной строке
        path_str_normalized = str(path_str).lower()
        suspicious_patterns = ['../..', '/etc/', '/proc/', '/sys/', '/dev/', '\\..\\', 'c:\\windows']

        for pattern in suspicious_patterns:
            if pattern in path_str_normalized:
                raise PathValidationError(f"Suspicious path pattern detected: {pattern}")

        # Преобразуем в Path и разрешаем все символические ссылки
        path = Path(path_str).resolve()
        base = Path(base_dir).resolve()

        # Для абсолютных путей проверяем только безопасность, не относительность к base_dir
        if path.is_absolute() and base_dir == ".":
            # Проверяем системные папки для абсолютных путей
            system_paths = ['/etc', '/proc', '/sys', '/dev', '/boot', '/root']
            if any(str(path).startswith(sys_path) for sys_path in system_paths):
                raise PathValidationError(f"Access to system directory denied: {path}")
        else:
            # Проверяем, что путь находится внутри базового каталога (для относительных путей)
            try:
                path.relative_to(base)
            except ValueError:
                raise PathValidationError(f"Path '{path_str}' is outside allowed directory '{base_dir}'")

        # Дополнительные проверки безопасности
        if not path.exists():
            logger.warning(f"Path does not exist: {path}")

        return path

    except (OSError, ValueError) as e:
        if isinstance(e, PathValidationError):
            raise
        raise PathValidationError(f"Invalid path '{path_str}': {str(e)}")

def validate_project_path(path_str: str | Path) -> Path:
    """
    Специальная валидация для путей проектов
    Проверяет что путь ведет к валидному проекту

    Args:
        path_str: Путь к проекту

    Returns:
        Path: Валидированный путь к проекту

    Raises:
        PathValidationError: При невалидном пути проекта
    """
    # Для проектов позволяем абсолютные пути (например, временные директории в тестах)
    path = Path(path_str)

    # Проверяем подозрительные паттерны
    path_str_normalized = str(path_str).lower()
    suspicious_patterns = ['../..', '/etc/', '/proc/', '/sys/', '/dev/', '\\..\\', 'c:\\windows']

    for pattern in suspicious_patterns:
        if pattern in path_str_normalized:
            raise PathValidationError(f"Suspicious path pattern detected: {pattern}")

    # Разрешаем путь
    validated_path = path.resolve()

    if not validated_path.is_dir():
        raise PathValidationError(f"Project path must be a directory: {path_str}")

    # Проверяем права доступа
    if not os.access(validated_path, os.R_OK):
        raise PathValidationError(f"No read access to project directory: {path_str}")

    return validated_path

def validate_file_path(file_path: str | Path, base_dir: str = ".") -> Path:
    """
    Валидация пути к файлу с дополнительными проверками

    Args:
        file_path: Путь к файлу
        base_dir: Базовый каталог

    Returns:
        Path: Валидированный путь к файлу

    Raises:
        PathValidationError: При невалидном пути к файлу
    """
    validated_path = validate_safe_path(file_path, base_dir)

    # Проверяем расширение файла на подозрительные типы
    suspicious_extensions = {'.exe', '.bat', '.cmd', '.sh', '.ps1', '.scr', '.com'}
    if validated_path.suffix.lower() in suspicious_extensions:
        raise PathValidationError(f"Executable file type not allowed: {validated_path.suffix}")

    return validated_path
