"""
ActionExecutor - выполнение структурированных действий

Выделенный класс для выполнения действий на основе JSON инструкций от ИИ.
Отвечает только за создание файлов, папок и других операций файловой системы.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ActionType(Enum):
    """Типы поддерживаемых действий"""
    CREATE_FILE = "create_file"
    CREATE_DIRECTORY = "create_directory"
    UPDATE_FILE = "update_file"
    DELETE_FILE = "delete_file"
    COPY_FILE = "copy_file"
    MOVE_FILE = "move_file"

@dataclass
class ActionResult:
    """Результат выполнения действия"""
    success: bool
    action_type: str
    target_path: str
    message: str
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}

@dataclass
class ExecutionSummary:
    """Сводка выполнения всех действий"""
    total_actions: int
    successful_actions: int
    failed_actions: int
    results: List[ActionResult]
    
    @property
    def success_rate(self) -> float:
        """Процент успешных действий"""
        if self.total_actions == 0:
            return 0.0
        return (self.successful_actions / self.total_actions) * 100

class ActionExecutor:
    """
    Выполняет структурированные действия на основе JSON инструкций
    
    Принцип единственной ответственности: только выполнение действий.
    Не содержит логики парсинга или планирования.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
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
    
    def execute_actions(self, project_path: Path, actions: List[Dict]) -> ExecutionSummary:
        """
        Выполняет список действий
        
        Args:
            project_path: Базовый путь проекта
            actions: Список действий в JSON формате
            
        Returns:
            ExecutionSummary: Сводка выполнения
        """
        results = []
        successful = 0
        
        self.logger.info(f"Выполняю {len(actions)} действий в {project_path}")
        
        for i, action in enumerate(actions, 1):
            self.logger.info(f"Действие {i}/{len(actions)}: {action.get('action', 'unknown')}")
            
            result = self._execute_single_action(project_path, action)
            results.append(result)
            
            if result.success:
                successful += 1
                self.logger.info(f"✅ {result.message}")
            else:
                self.logger.error(f"❌ {result.message}")
        
        summary = ExecutionSummary(
            total_actions=len(actions),
            successful_actions=successful,
            failed_actions=len(actions) - successful,
            results=results
        )
        
        self.logger.info(f"Выполнение завершено: {successful}/{len(actions)} успешно")
        return summary
    
    def _execute_single_action(self, project_path: Path, action: Dict) -> ActionResult:
        """
        Выполняет одно действие
        
        Args:
            project_path: Базовый путь проекта
            action: Действие в JSON формате
            
        Returns:
            ActionResult: Результат выполнения
        """
        action_type = action.get('action')
        
        if not action_type:
            return ActionResult(
                success=False,
                action_type='unknown',
                target_path='',
                message="Отсутствует тип действия"
            )
        
        try:
            # Диспетчеризация действий
            if action_type == ActionType.CREATE_FILE.value:
                return self._create_file(project_path, action)
            elif action_type == ActionType.CREATE_DIRECTORY.value:
                return self._create_directory(project_path, action)
            elif action_type == ActionType.UPDATE_FILE.value:
                return self._update_file(project_path, action)
            elif action_type == ActionType.DELETE_FILE.value:
                return self._delete_file(project_path, action)
            elif action_type == ActionType.COPY_FILE.value:
                return self._copy_file(project_path, action)
            elif action_type == ActionType.MOVE_FILE.value:
                return self._move_file(project_path, action)
            else:
                return ActionResult(
                    success=False,
                    action_type=action_type,
                    target_path=action.get('path', ''),
                    message=f"Неподдерживаемый тип действия: {action_type}"
                )
                
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=action_type,
                target_path=action.get('path', ''),
                message=f"Ошибка выполнения: {str(e)}"
            )
    
    def _create_file(self, project_path: Path, action: Dict) -> ActionResult:
        """Создает файл с содержимым"""
        file_path = action.get('path')
        content = action.get('content', '')
        
        if not file_path:
            return ActionResult(
                success=False,
                action_type=ActionType.CREATE_FILE.value,
                target_path='',
                message="Не указан путь к файлу"
            )
        
        full_path = project_path / file_path
        
        # Проверяем безопасность пути
        if not self._validate_file_path(full_path, project_path):
            return ActionResult(
                success=False,
                action_type=ActionType.CREATE_FILE.value,
                target_path=file_path,
                message=f"Отклонен небезопасный путь: {file_path}"
            )
        
        # Создаем родительские папки если нужно
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Записываем содержимое
        full_path.write_text(content, encoding='utf-8')
        
        lines_count = content.count('\n') + (1 if content else 0)
        chars_count = len(content)
        
        return ActionResult(
            success=True,
            action_type=ActionType.CREATE_FILE.value,
            target_path=file_path,
            message=f"Создан файл: {file_path}",
            details={
                'lines': lines_count,
                'characters': chars_count,
                'size_bytes': len(content.encode('utf-8'))
            }
        )
    
    def _create_directory(self, project_path: Path, action: Dict) -> ActionResult:
        """Создает папку"""
        dir_path = action.get('path')
        
        if not dir_path:
            return ActionResult(
                success=False,
                action_type=ActionType.CREATE_DIRECTORY.value,
                target_path='',
                message="Не указан путь к папке"
            )
        
        full_path = project_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        
        return ActionResult(
            success=True,
            action_type=ActionType.CREATE_DIRECTORY.value,
            target_path=dir_path,
            message=f"Создана папка: {dir_path}"
        )
    
    def _update_file(self, project_path: Path, action: Dict) -> ActionResult:
        """Обновляет существующий файл"""
        file_path = action.get('path')
        content = action.get('content', '')
        mode = action.get('mode', 'replace')  # 'replace', 'append', 'prepend'
        
        if not file_path:
            return ActionResult(
                success=False,
                action_type=ActionType.UPDATE_FILE.value,
                target_path='',
                message="Не указан путь к файлу"
            )
        
        full_path = project_path / file_path
        
        if mode == 'append':
            # Добавляем в конец
            existing_content = full_path.read_text(encoding='utf-8') if full_path.exists() else ''
            new_content = existing_content + '\n' + content
        elif mode == 'prepend':
            # Добавляем в начало
            existing_content = full_path.read_text(encoding='utf-8') if full_path.exists() else ''
            new_content = content + '\n' + existing_content
        else:
            # Заменяем содержимое
            new_content = content
        
        full_path.write_text(new_content, encoding='utf-8')
        
        return ActionResult(
            success=True,
            action_type=ActionType.UPDATE_FILE.value,
            target_path=file_path,
            message=f"Обновлен файл: {file_path} (режим: {mode})"
        )
    
    def _delete_file(self, project_path: Path, action: Dict) -> ActionResult:
        """Удаляет файл или папку"""
        target_path = action.get('path')
        
        if not target_path:
            return ActionResult(
                success=False,
                action_type=ActionType.DELETE_FILE.value,
                target_path='',
                message="Не указан путь для удаления"
            )
        
        full_path = project_path / target_path
        
        if not full_path.exists():
            return ActionResult(
                success=False,
                action_type=ActionType.DELETE_FILE.value,
                target_path=target_path,
                message=f"Файл не существует: {target_path}"
            )
        
        if full_path.is_file():
            full_path.unlink()
            message = f"Удален файл: {target_path}"
        elif full_path.is_dir():
            import shutil
            shutil.rmtree(full_path)
            message = f"Удалена папка: {target_path}"
        else:
            return ActionResult(
                success=False,
                action_type=ActionType.DELETE_FILE.value,
                target_path=target_path,
                message=f"Неизвестный тип объекта: {target_path}"
            )
        
        return ActionResult(
            success=True,
            action_type=ActionType.DELETE_FILE.value,
            target_path=target_path,
            message=message
        )
    
    def _copy_file(self, project_path: Path, action: Dict) -> ActionResult:
        """Копирует файл"""
        source_path = action.get('source')
        target_path = action.get('target')
        
        if not source_path or not target_path:
            return ActionResult(
                success=False,
                action_type=ActionType.COPY_FILE.value,
                target_path=target_path or '',
                message="Не указаны пути source и target"
            )
        
        full_source = project_path / source_path
        full_target = project_path / target_path
        
        if not full_source.exists():
            return ActionResult(
                success=False,
                action_type=ActionType.COPY_FILE.value,
                target_path=target_path,
                message=f"Источник не существует: {source_path}"
            )
        
        # Создаем родительские папки для цели
        full_target.parent.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy2(full_source, full_target)
        
        return ActionResult(
            success=True,
            action_type=ActionType.COPY_FILE.value,
            target_path=target_path,
            message=f"Скопирован файл: {source_path} → {target_path}"
        )
    
    def _move_file(self, project_path: Path, action: Dict) -> ActionResult:
        """Перемещает файл"""
        source_path = action.get('source')
        target_path = action.get('target')
        
        if not source_path or not target_path:
            return ActionResult(
                success=False,
                action_type=ActionType.MOVE_FILE.value,
                target_path=target_path or '',
                message="Не указаны пути source и target"
            )
        
        full_source = project_path / source_path
        full_target = project_path / target_path
        
        if not full_source.exists():
            return ActionResult(
                success=False,
                action_type=ActionType.MOVE_FILE.value,
                target_path=target_path,
                message=f"Источник не существует: {source_path}"
            )
        
        # Создаем родительские папки для цели
        full_target.parent.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.move(str(full_source), str(full_target))
        
        return ActionResult(
            success=True,
            action_type=ActionType.MOVE_FILE.value,
            target_path=target_path,
            message=f"Перемещен файл: {source_path} → {target_path}"
        ) 