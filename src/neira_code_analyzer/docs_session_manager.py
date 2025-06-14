"""
DocsSessionManager - управление состоянием сессии документации

Выделенный класс для управления состоянием пошаговой генерации документации.
Отвечает только за сохранение, загрузку и очистку состояния сессии.
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SessionState:
    """Структурированное состояние сессии"""
    session_id: str
    project_path: str
    step: int
    status: str  # 'analyzing', 'executing', 'completed', 'error'
    params: dict
    completed_steps: list[dict]
    ai_model: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict:
        """Конвертирует в словарь для JSON сериализации"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'SessionState':
        """Создает объект из словаря"""
        return cls(**data)

class DocsSessionManager:
    """
    Управляет состоянием сессии генерации документации

    Принцип единственной ответственности: только управление состоянием.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_new_session(
        self,
        project_path: Path,
        params: dict,
        ai_model: str
    ) -> SessionState:
        """
        Создает новую сессию документации

        Args:
            project_path: Путь к проекту
            params: Параметры генерации
            ai_model: Модель ИИ для использования

        Returns:
            SessionState: Новое состояние сессии
        """
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        timestamp = datetime.now().isoformat()

        session_state = SessionState(
            session_id=session_id,
            project_path=str(project_path),
            step=1,
            status='analyzing',
            params=params,
            completed_steps=[],
            ai_model=ai_model,
            created_at=timestamp,
            updated_at=timestamp
        )

        # Создаем рабочую папку для сессии
        self._ensure_session_directory(project_path)

        self.logger.info(f"Создана новая сессия: {session_id}")
        return session_state

    def load_session(self, project_path: Path) -> SessionState | None:
        """
        Загружает существующее состояние сессии

        Args:
            project_path: Путь к проекту

        Returns:
            SessionState или None если сессия не найдена
        """
        session_file = self._get_session_file_path(project_path)

        if not session_file.exists():
            self.logger.info("Файл сессии не найден")
            return None

        try:
            with open(session_file, encoding='utf-8') as f:
                data = json.load(f)

            session_state = SessionState.from_dict(data)
            self.logger.info(f"Загружена сессия: {session_state.session_id}")
            return session_state

        except Exception as e:
            self.logger.error(f"Ошибка загрузки сессии: {e}")
            return None

    def save_session(self, project_path: Path, session_state: SessionState) -> bool:
        """
        Сохраняет состояние сессии

        Args:
            project_path: Путь к проекту
            session_state: Состояние для сохранения

        Returns:
            bool: True если сохранение успешно
        """
        try:
            # Обновляем время изменения
            session_state.updated_at = datetime.now().isoformat()

            # Убеждаемся что папка существует
            self._ensure_session_directory(project_path)

            session_file = self._get_session_file_path(project_path)

            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_state.to_dict(), f, indent=2, ensure_ascii=False)

            self.logger.info(f"Сессия сохранена: {session_state.session_id}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка сохранения сессии: {e}")
            return False

    def update_session_step(
        self,
        session_state: SessionState,
        new_status: str = None,
        completed_step: dict = None
    ) -> SessionState:
        """
        Обновляет шаг сессии

        Args:
            session_state: Текущее состояние
            new_status: Новый статус (опционально)
            completed_step: Выполненный шаг (опционально)

        Returns:
            SessionState: Обновленное состояние
        """
        session_state.step += 1

        if new_status:
            session_state.status = new_status

        if completed_step:
            session_state.completed_steps.append(completed_step)

        session_state.updated_at = datetime.now().isoformat()

        self.logger.info(f"Обновлен шаг сессии: {session_state.step}")
        return session_state

    def cleanup_session(self, project_path: Path) -> bool:
        """
        Очищает файлы сессии после завершения

        Args:
            project_path: Путь к проекту

        Returns:
            bool: True если очистка успешна
        """
        session_dir = self._get_session_directory(project_path)

        if not session_dir.exists():
            return True

        try:
            import shutil
            shutil.rmtree(session_dir)
            self.logger.info("Сессия очищена")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка очистки сессии: {e}")
            return False

    def get_session_info(self, project_path: Path) -> dict | None:
        """
        Получает краткую информацию о сессии

        Args:
            project_path: Путь к проекту

        Returns:
            Dict с информацией о сессии или None
        """
        session_state = self.load_session(project_path)

        if not session_state:
            return None

        return {
            'session_id': session_state.session_id,
            'step': session_state.step,
            'status': session_state.status,
            'completed_steps': len(session_state.completed_steps),
            'created_at': session_state.created_at,
            'updated_at': session_state.updated_at
        }

    def _get_session_directory(self, project_path: Path) -> Path:
        """Возвращает путь к папке сессии"""
        return project_path / ".docs_session"

    def _get_session_file_path(self, project_path: Path) -> Path:
        """Возвращает путь к файлу состояния сессии"""
        return self._get_session_directory(project_path) / "state.json"

    def _ensure_session_directory(self, project_path: Path):
        """Убеждается что папка сессии существует"""
        session_dir = self._get_session_directory(project_path)
        session_dir.mkdir(exist_ok=True)
