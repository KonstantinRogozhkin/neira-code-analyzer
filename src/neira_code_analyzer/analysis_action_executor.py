"""
AnalysisActionExecutor - выполнение действий с кодом по анализу

АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: Теперь наследуется от BaseActionExecutor для устранения дублирования кода.
Выделенный класс для выполнения JSON-команд от ИИ по анализу и исправлению кода.
Поддерживает безопасное выполнение операций с файловой системой.
"""

import ast
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .base_action_executor import BaseActionExecutor, BaseExecutionSummary

logger = logging.getLogger(__name__)

@dataclass
class AnalysisExecutionSummary(BaseExecutionSummary):
    """
    Сводка выполнения действий анализа
    
    АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: Теперь наследуется от BaseExecutionSummary для устранения дублирования
    """
    pass  # Все функциональность уже в базовом классе


class AnalysisActionExecutor(BaseActionExecutor):
    """
    Выполняет JSON-команды от ИИ для анализа и исправления кода

    АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: Теперь наследуется от BaseActionExecutor для устранения дублирования.
    Принцип единственной ответственности: только выполнение действий.
    Поддерживает безопасные операции с файлами и откат изменений.
    """

    def __init__(self):
        super().__init__()
        # Специфичная для анализа инициализация, если потребуется

    def execute_actions(
        self,
        actions: list[dict[str, Any]],
        project_path: Path,
        session_id: str
    ) -> AnalysisExecutionSummary:
        """
        Выполняет список действий от ИИ

        Args:
            actions: Список JSON действий от ИИ
            project_path: Путь к проекту
            session_id: ID сессии для бэкапов

        Returns:
            AnalysisExecutionSummary: Сводка выполнения
        """
        start_time = datetime.now()

        # Создаем папку для бэкапов
        self.backup_dir = project_path / ".neira" / "backups" / session_id
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        summary = AnalysisExecutionSummary(
            actions_executed=0,
            actions_succeeded=0,
            actions_failed=0,
            files_modified=[],
            files_created=[],
            files_backed_up=[],
            errors=[],
            duration_seconds=0.0
        )

        for action in actions:
            try:
                summary.actions_executed += 1
                success = self._execute_single_action(action, project_path, summary)

                if success:
                    summary.actions_succeeded += 1
                else:
                    summary.actions_failed += 1

            except Exception as e:
                self.logger.error(f"Ошибка выполнения действия {action}: {e}")
                summary.errors.append(f"Действие {action.get('action', 'unknown')}: {str(e)}")
                summary.actions_failed += 1

        end_time = datetime.now()
        summary.duration_seconds = (end_time - start_time).total_seconds()

        self.logger.info(f"Выполнено {summary.actions_executed} действий, "
                        f"успешно: {summary.actions_succeeded}, "
                        f"ошибок: {summary.actions_failed}")

        return summary

    def _execute_single_action(
        self,
        action: dict[str, Any],
        project_path: Path,
        summary: AnalysisExecutionSummary
    ) -> bool:
        """
        Выполняет одно действие

        Args:
            action: JSON действие от ИИ
            project_path: Путь к проекту
            summary: Сводка для обновления

        Returns:
            bool: True если действие выполнено успешно
        """
        action_type = action.get("action")

        if not action_type:
            self.logger.error("Действие не содержит поля 'action'")
            return False

        # Диспетчер действий
        action_handlers = {
            "create_file": self._create_file,
            "update_file": self._update_file,
            "backup_file": self._backup_file,
            "refactor_function": self._refactor_function,
            "add_comment": self._add_comment,
            "fix_issue": self._fix_issue,
            "optimize_code": self._optimize_code,
            "create_test": self._create_test,
            "create_documentation": self._create_documentation
        }

        handler = action_handlers.get(action_type)
        if not handler:
            self.logger.error(f"Неизвестный тип действия: {action_type}")
            summary.errors.append(f"Неизвестный тип действия: {action_type}")
            return False

        try:
            return handler(action, project_path, summary)
        except Exception as e:
            self.logger.error(f"Ошибка выполнения действия {action_type}: {e}")
            summary.errors.append(f"{action_type}: {str(e)}")
            return False

    def _create_file(
        self,
        action: dict[str, Any],
        project_path: Path,
        summary: AnalysisExecutionSummary
    ) -> bool:
        """
        Создает новый файл
        
        АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: Использует _create_file_safely из базового класса
        """
        file_path = project_path / action.get("path", "")
        content = action.get("content", "")

        return self._create_file_safely(file_path, content, project_path, summary)

    def _update_file(
        self,
        action: dict[str, Any],
        project_path: Path,
        summary: AnalysisExecutionSummary
    ) -> bool:
        """
        Обновляет существующий файл
        
        АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: Использует _update_file_safely из базового класса
        """
        file_path = project_path / action.get("path", "")
        content = action.get("content", "")

        return self._update_file_safely(file_path, content, project_path, summary)

    def _backup_file(
        self,
        action: dict[str, Any],
        project_path: Path,
        summary: AnalysisExecutionSummary
    ) -> bool:
        """Создает резервную копию файла"""
        file_path = project_path / action.get("path", "")

        # Проверяем безопасность пути
        if not self._validate_file_path(file_path, project_path):
            self.logger.error(f"Отклонен небезопасный путь: {file_path}")
            return False

        if self._backup_file_to_backup_dir(file_path):
            summary.files_backed_up.append(str(file_path))
            return True

        return False

    def _refactor_function(
        self,
        action: dict[str, Any],
        project_path: Path,
        summary: AnalysisExecutionSummary
    ) -> bool:
        """
        Рефакторинг функции в файле с использованием AST для безопасного парсинга
        
        ИСПРАВЛЕНИЕ: Заменен небезопасный regex на AST-парсер для:
        - Надежной обработки декораторов и аннотаций типов
        - Защиты от ReDoS-атак
        - Корректной работы с нестандартным форматированием
        """
        file_path = project_path / action.get("path", "")
        function_name = action.get("function_name", "")
        new_content = action.get("new_function_content", "")

        # Проверяем безопасность пути
        if not self._validate_file_path(file_path, project_path):
            self.logger.error(f"Отклонен небезопасный путь: {file_path}")
            return False

        if not file_path.exists():
            self.logger.error(f"Файл {file_path} не существует")
            return False

        if not function_name or not new_content:
            self.logger.error("Отсутствует имя функции или новое содержимое")
            return False

        # Создаем бэкап
        if self._backup_file_to_backup_dir(file_path):
            summary.files_backed_up.append(str(file_path))

        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            # Безопасный AST-парсинг вместо regex
            if file_path.suffix == '.py':
                return self._refactor_python_function_with_ast(
                    content, file_path, function_name, new_content, summary
                )
            else:
                # Для не-Python файлов используем простую замену
                self.logger.info(f"Базовая замена для {file_path.suffix} файла")
                return self._refactor_non_python_function(
                    content, file_path, function_name, new_content, summary
                )

        except Exception as e:
            self.logger.error(f"Ошибка рефакторинга функции: {e}")
            return False

    def _refactor_python_function_with_ast(
        self,
        content: str,
        file_path: Path,
        function_name: str,
        new_content: str,
        summary: AnalysisExecutionSummary
    ) -> bool:
        """
        Безопасный рефакторинг Python функции с использованием AST
        """
        try:
            # Парсим код в AST
            tree = ast.parse(content)

            # Ищем функцию в AST
            function_node = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    function_node = node
                    break

            if function_node is None:
                self.logger.warning(f"Функция {function_name} не найдена в {file_path}")
                return False

            # Получаем границы функции в исходном коде
            lines = content.splitlines(keepends=True)

            # Находим начало функции (с учетом декораторов)
            start_line = function_node.lineno - 1
            if function_node.decorator_list:
                start_line = function_node.decorator_list[0].lineno - 1

            # Находим конец функции
            end_line = function_node.end_lineno if hasattr(function_node, 'end_lineno') else None

            if end_line is None:
                # Fallback для старых версий Python
                end_line = self._find_function_end_line(lines, start_line, function_name)

            # Заменяем функцию
            new_lines = lines[:start_line] + [new_content + '\n'] + lines[end_line:]
            updated_content = ''.join(new_lines)

            # Проверяем синтаксис нового кода
            try:
                ast.parse(updated_content)
            except SyntaxError as e:
                self.logger.error(f"Новый код содержит синтаксические ошибки: {e}")
                return False

            # Сохраняем изменения
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            summary.files_modified.append(str(file_path))
            self.logger.info(f"AST-рефакторинг функции {function_name} в {file_path} выполнен успешно")
            return True

        except SyntaxError as e:
            self.logger.error(f"Синтаксическая ошибка в исходном файле {file_path}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Ошибка AST-рефакторинга: {e}")
            return False

    def _find_function_end_line(self, lines: list[str], start_line: int, function_name: str) -> int:
        """
        Находит последнюю строку функции для старых версий Python без end_lineno
        """
        indent_level = None

        for i in range(start_line, len(lines)):
            line = lines[i]

            # Определяем уровень отступа функции
            if indent_level is None and line.strip().startswith('def '):
                indent_level = len(line) - len(line.lstrip())
                continue

            # Если нашли строку с меньшим отступом (или без отступа), это конец функции
            if line.strip() and indent_level is not None:
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indent_level and not line.strip().startswith('#'):
                    return i

        return len(lines)

    def _refactor_non_python_function(
        self,
        content: str,
        file_path: Path,
        function_name: str,
        new_content: str,
        summary: AnalysisExecutionSummary
    ) -> bool:
        """
        Простая замена для не-Python файлов
        TODO: Добавить поддержку других языков с соответствующими парсерами
        """
        # Базовая замена по паттерну имени функции
        if function_name in content:
            # Это очень простая реализация, можно улучшить
            self.logger.warning(f"Простая замена для {file_path.suffix} файлов может быть неточной")
            return False

        return False

    def _add_comment(
        self,
        action: dict[str, Any],
        project_path: Path,
        summary: AnalysisExecutionSummary
    ) -> bool:
        """Добавляет комментарий в файл"""
        file_path = project_path / action.get("path", "")
        line_number = action.get("line_number", 1)
        comment = action.get("comment", "")

        if not file_path.exists():
            self.logger.error(f"Файл {file_path} не существует")
            return False

        # Создаем бэкап
        if self._backup_file_to_backup_dir(file_path):
            summary.files_backed_up.append(str(file_path))

        with open(file_path, encoding='utf-8') as f:
            lines = f.readlines()

        # Вставляем комментарий
        if 0 <= line_number - 1 < len(lines):
            lines.insert(line_number - 1, f"# {comment}\n")

            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            summary.files_modified.append(str(file_path))
            self.logger.info(f"Добавлен комментарий в {file_path}:{line_number}")
            return True

        return False

    def _fix_issue(
        self,
        action: dict[str, Any],
        project_path: Path,
        summary: AnalysisExecutionSummary
    ) -> bool:
        """Исправляет конкретную проблему в коде"""
        file_path = project_path / action.get("path", "")
        issue_description = action.get("issue", "")
        fix_type = action.get("fix_type", "")
        old_code = action.get("old_code", "")
        new_code = action.get("new_code", "")

        # Проверяем безопасность пути
        if not self._validate_file_path(file_path, project_path):
            self.logger.error(f"Отклонен небезопасный путь: {file_path}")
            return False

        if not file_path.exists():
            self.logger.error(f"Файл {file_path} не существует")
            return False

        self.logger.info(f"Исправление проблемы в {file_path}: {issue_description}")

        try:
            # Создаем бэкап
            if self._backup_file_to_backup_dir(file_path):
                summary.files_backed_up.append(str(file_path))

            # Различные стратегии исправления
            if fix_type == "replace" and old_code and new_code:
                # Точная замена кода
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()

                if old_code in content:
                    updated_content = content.replace(old_code, new_code)

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)

                    summary.files_modified.append(str(file_path))
                    self.logger.info(f"Исправление '{fix_type}' применено в {file_path}")
                    return True
                else:
                    self.logger.warning(f"Старый код не найден в {file_path}")
                    return False

            elif fix_type == "add_import":
                # Добавление импорта
                import_line = action.get("import_line", "")
                if import_line:
                    with open(file_path, encoding='utf-8') as f:
                        lines = f.readlines()

                    # Ищем место для добавления импорта (после существующих импортов)
                    insert_line = 0
                    for i, line in enumerate(lines):
                        if line.strip().startswith(('import ', 'from ')):
                            insert_line = i + 1

                    lines.insert(insert_line, f"{import_line}\n")

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)

                    summary.files_modified.append(str(file_path))
                    self.logger.info(f"Добавлен импорт в {file_path}: {import_line}")
                    return True

            else:
                # Общий случай - просто логируем что исправление требует ручного вмешательства
                self.logger.warning(f"Исправление типа '{fix_type}' требует ручного вмешательства")
                self.logger.info(f"Описание: {issue_description}")
                return False

        except Exception as e:
            self.logger.error(f"Ошибка исправления проблемы: {e}")
            return False

    def _optimize_code(
        self,
        action: dict[str, Any],
        project_path: Path,
        summary: AnalysisExecutionSummary
    ) -> bool:
        """Оптимизирует код"""
        file_path = project_path / action.get("path", "")
        optimization_type = action.get("optimization_type", "")
        old_code = action.get("old_code", "")
        optimized_code = action.get("optimized_code", "")

        # Проверяем безопасность пути
        if not self._validate_file_path(file_path, project_path):
            self.logger.error(f"Отклонен небезопасный путь: {file_path}")
            return False

        if not file_path.exists():
            self.logger.error(f"Файл {file_path} не существует")
            return False

        self.logger.info(f"Оптимизация '{optimization_type}' в {file_path}")

        try:
            # Создаем бэкап
            if self._backup_file_to_backup_dir(file_path):
                summary.files_backed_up.append(str(file_path))

            # Различные типы оптимизации
            if optimization_type == "replace" and old_code and optimized_code:
                # Замена неоптимального кода на оптимизированный
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()

                if old_code in content:
                    updated_content = content.replace(old_code, optimized_code)

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)

                    summary.files_modified.append(str(file_path))
                    self.logger.info(f"Оптимизация применена в {file_path}")
                    return True
                else:
                    self.logger.warning(f"Неоптимизированный код не найден в {file_path}")
                    return False

            elif optimization_type == "remove_unused_imports":
                # Простая оптимизация - удаление очевидно неиспользуемых импортов
                with open(file_path, encoding='utf-8') as f:
                    lines = f.readlines()

                # Простая эвристика - ищем импорты, которые не используются в файле
                content = ''.join(lines)
                optimized_lines = []

                for line in lines:
                    if line.strip().startswith(('import ', 'from ')):
                        # Простая проверка - если модуль упоминается в коде
                        import_parts = line.split()
                        if len(import_parts) >= 2:
                            module_name = import_parts[1].split('.')[0]
                            # Если модуль используется в коде, оставляем импорт
                            if module_name in content.replace(line, ''):
                                optimized_lines.append(line)
                            else:
                                self.logger.debug(f"Удален неиспользуемый импорт: {line.strip()}")
                        else:
                            optimized_lines.append(line)
                    else:
                        optimized_lines.append(line)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(optimized_lines)

                summary.files_modified.append(str(file_path))
                self.logger.info(f"Удалены неиспользуемые импорты в {file_path}")
                return True

            else:
                self.logger.warning(f"Тип оптимизации '{optimization_type}' требует ручного вмешательства")
                return False

        except Exception as e:
            self.logger.error(f"Ошибка оптимизации кода: {e}")
            return False

    def _create_test(
        self,
        action: dict[str, Any],
        project_path: Path,
        summary: AnalysisExecutionSummary
    ) -> bool:
        """Создает тестовый файл"""
        test_path = project_path / action.get("path", "")
        test_content = action.get("content", "")

        # Создаем папку tests если нужно
        test_path.parent.mkdir(parents=True, exist_ok=True)

        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(test_content)

        summary.files_created.append(str(test_path))
        self.logger.info(f"Создан тест: {test_path}")
        return True

    def _create_documentation(
        self,
        action: dict[str, Any],
        project_path: Path,
        summary: AnalysisExecutionSummary
    ) -> bool:
        """Создает документацию"""
        doc_path = project_path / action.get("path", "")
        doc_content = action.get("content", "")

        # Создаем папку docs если нужно
        doc_path.parent.mkdir(parents=True, exist_ok=True)

        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(doc_content)

        summary.files_created.append(str(doc_path))
        self.logger.info(f"Создана документация: {doc_path}")
        return True
