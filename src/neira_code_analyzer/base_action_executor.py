"""
BaseActionExecutor - базовый класс для всех ActionExecutor

АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: Устраняет дублирование кода между ActionExecutor и AnalysisActionExecutor.
Содержит общую функциональность для валидации путей, создания резервных копий и базовых файловых операций.
"""

import logging
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BaseExecutionSummary(ABC):
    """Базовая сводка выполнения действий"""
    actions_executed: int
    actions_succeeded: int
    actions_failed: int
    files_modified: list[str]
    files_created: list[str]
    files_backed_up: list[str]
    errors: list[str]
    duration_seconds: float

    @property
    def success_rate(self) -> float:
        """Процент успешно выполненных действий"""
        if self.actions_executed == 0:
            return 0.0
        return (self.actions_succeeded / self.actions_executed) * 100


class BaseActionExecutor(ABC):
    """
    Базовый класс для всех ActionExecutor
    
    АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: Устраняет дублирование кода путем вынесения общих методов.
    Следует принципу DRY (Don't Repeat Yourself) и упрощает поддержку.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.backup_dir = None  # Будет установлена при инициализации сессии

    def _validate_file_path(self, file_path: Path, project_path: Path) -> bool:
        """
        Проверяет что путь к файлу находится внутри проекта (защита от Path Traversal)

        Args:
            file_path: Путь к файлу
            project_path: Корневой путь проекта

        Returns:
            bool: True если путь безопасен
        """
        try:
            # Разрешаем все символические ссылки
            resolved_file = file_path.resolve()
            resolved_project = project_path.resolve()

            # Проверяем что файл находится внутри проекта
            try:
                resolved_file.relative_to(resolved_project)
                return True
            except ValueError:
                self.logger.error(f"Небезопасный путь (за пределами проекта): {file_path}")
                return False

        except Exception as e:
            self.logger.error(f"Ошибка валидации пути {file_path}: {e}")
            return False

    def _backup_file_to_backup_dir(self, file_path: Path) -> bool:
        """
        Создает резервную копию файла в папке backup

        Args:
            file_path: Путь к файлу для резервного копирования

        Returns:
            bool: True если резервная копия создана успешно
        """
        if not self.backup_dir:
            self.logger.warning("Backup directory не установлена")
            return False

        if not file_path.exists():
            self.logger.warning(f"Файл для backup не существует: {file_path}")
            return False

        try:
            # ИСПРАВЛЕНИЕ: Создаем структуру папок относительно корня файловой системы
            # Используем только имя файла для простоты
            backup_file_path = self.backup_dir / file_path.name

            # Создаем папку если нужно
            backup_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Копируем файл
            shutil.copy2(file_path, backup_file_path)

            self.logger.info(f"Backup создан: {backup_file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка создания backup для {file_path}: {e}")
            return False

    def _create_file_safely(
        self,
        file_path: Path,
        content: str,
        project_path: Path,
        summary: BaseExecutionSummary
    ) -> bool:
        """
        Безопасно создает файл с проверкой пути

        Args:
            file_path: Путь к создаваемому файлу
            content: Содержимое файла
            project_path: Корневой путь проекта
            summary: Сводка для обновления

        Returns:
            bool: True если файл создан успешно
        """
        # Проверяем безопасность пути
        if not self._validate_file_path(file_path, project_path):
            self.logger.error(f"Отклонен небезопасный путь: {file_path}")
            return False

        if file_path.exists():
            self.logger.warning(f"Файл {file_path} уже существует, пропускаем создание")
            return False

        try:
            # Создаем директории если нужно
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Создаем файл
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            summary.files_created.append(str(file_path))
            self.logger.info(f"Файл создан: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка создания файла {file_path}: {e}")
            return False

    def _update_file_safely(
        self,
        file_path: Path,
        content: str,
        project_path: Path,
        summary: BaseExecutionSummary
    ) -> bool:
        """
        Безопасно обновляет файл с резервным копированием

        Args:
            file_path: Путь к обновляемому файлу
            content: Новое содержимое файла
            project_path: Корневой путь проекта
            summary: Сводка для обновления

        Returns:
            bool: True если файл обновлен успешно
        """
        # Проверяем безопасность пути
        if not self._validate_file_path(file_path, project_path):
            self.logger.error(f"Отклонен небезопасный путь: {file_path}")
            return False

        if not file_path.exists():
            self.logger.error(f"Файл {file_path} не существует")
            return False

        try:
            # Создаем backup
            if self._backup_file_to_backup_dir(file_path):
                summary.files_backed_up.append(str(file_path))

            # Обновляем файл
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            summary.files_modified.append(str(file_path))
            self.logger.info(f"Файл обновлен: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка обновления файла {file_path}: {e}")
            return False

    def rollback_changes(self, session_id: str, project_path: Path) -> bool:
        """
        Откатывает изменения из backup

        Args:
            session_id: ID сессии
            project_path: Путь к проекту

        Returns:
            bool: True если откат выполнен успешно
        """
        backup_dir = project_path / ".neira" / "backups" / session_id

        if not backup_dir.exists():
            self.logger.warning(f"Backup папка не найдена: {backup_dir}")
            return False

        try:
            restored_count = 0

            # Восстанавливаем все файлы из backup
            for backup_file in backup_dir.rglob('*'):
                if backup_file.is_file():
                    # Определяем оригинальный путь файла
                    relative_path = backup_file.relative_to(backup_dir)
                    original_file = project_path / relative_path

                    # Восстанавливаем файл
                    original_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_file, original_file)
                    restored_count += 1

            self.logger.info(f"Восстановлено {restored_count} файлов из backup")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка отката изменений: {e}")
            return False

    @abstractmethod
    def execute_actions(self, *args, **kwargs):
        """Абстрактный метод для выполнения действий - должен быть реализован в наследниках"""
        pass

    @abstractmethod
    def _execute_single_action(self, *args, **kwargs):
        """Абстрактный метод для выполнения одного действия - должен быть реализован в наследниках"""
        pass
