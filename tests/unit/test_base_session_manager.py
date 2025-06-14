"""
Юнит-тесты для base_session_manager.py - базовый менеджер сессий

Тестирует:
- BaseSessionState - базовое состояние сессии
- BaseSessionManager - базовый менеджер с общей логикой
- Унификация управления сессиями
- Устранение дублирования кода
"""

import json
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch

from src.neira_code_analyzer.base_session_manager import BaseSessionManager, BaseSessionState


# Тестовые классы для проверки абстрактных методов
@dataclass
class TestSessionState(BaseSessionState):
    """Тестовое состояние сессии для проверки базового класса"""
    test_data: str = "default_test_data"

    def __post_init__(self):
        super().__post_init__()
        if not self.session_type:
            self.session_type = "test"


class TestSessionManager(BaseSessionManager):
    """Тестовый менеджер сессий для проверки базового класса"""

    def __init__(self):
        super().__init__("test")

    def create_new_session(self, project_path: Path, **kwargs) -> TestSessionState:
        """Реализация абстрактного метода для тестов"""
        return TestSessionState(
            session_id="test_session",
            project_path=str(project_path),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            status="active",
            session_type="test",
            test_data=kwargs.get("test_data", "test_value")
        )

    def _deserialize_session(self, data: dict[str, Any]) -> TestSessionState:
        """Реализация абстрактного метода для тестов"""
        return TestSessionState(**data)


class TestBaseSessionState:
    """Тесты базового состояния сессии"""

    def test_base_session_state_initialization(self):
        """Тест инициализации базового состояния"""
        # Arrange & Act
        state = TestSessionState(
            session_id="test_id",
            project_path="/test/path",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            status="active",
            session_type="test"
        )

        # Assert
        assert state.session_id == "test_id"
        assert state.project_path == "/test/path"
        assert state.status == "active"
        assert state.session_type == "test"
        assert state.test_data == "default_test_data"

    def test_base_session_state_auto_generation(self):
        """Тест автоматической генерации полей"""
        # Arrange & Act
        state = TestSessionState(
            session_id="",  # Пустой ID должен быть сгенерирован
            project_path="/test/path",
            created_at="",  # Пустая дата должна быть сгенерирована
            updated_at="",
            status="active",
            session_type=""  # Пустой тип должен быть установлен в __post_init__
        )

        # Assert
        assert len(state.session_id) == 8  # UUID[:8]
        assert state.created_at != ""
        assert state.updated_at != ""
        assert state.session_type == "test"

    def test_base_session_state_timestamps(self):
        """Тест корректности временных меток"""
        # Arrange
        before_creation = datetime.now()

        # Act
        state = TestSessionState(
            session_id="test",
            project_path="/test",
            created_at="",
            updated_at="",
            status="active",
            session_type="test"
        )

        after_creation = datetime.now()

        # Assert
        created_time = datetime.fromisoformat(state.created_at)
        updated_time = datetime.fromisoformat(state.updated_at)

        assert before_creation <= created_time <= after_creation
        assert before_creation <= updated_time <= after_creation
        assert state.created_at == state.updated_at  # Должны быть одинаковыми при создании


class TestBaseSessionManager:
    """Тесты базового менеджера сессий"""

    def setup_method(self):
        """Настройка для каждого теста"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = TestSessionManager()
        self.test_project_path = self.temp_dir / "test_project"
        self.test_project_path.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Очистка после каждого теста"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_session_manager_initialization(self):
        """Тест инициализации менеджера сессий"""
        # Arrange & Act
        manager = TestSessionManager()

        # Assert
        assert manager.session_type == "test"
        assert hasattr(manager, 'logger')

    def test_get_session_file_path(self):
        """Тест получения пути к файлу сессии"""
        # Arrange & Act
        session_file = self.manager.get_session_file_path(self.test_project_path)

        # Assert
        expected_path = self.test_project_path / ".neira" / "test_session.json"
        assert session_file == expected_path

    def test_create_and_save_session(self):
        """Тест создания и сохранения сессии"""
        # Arrange
        session = self.manager.create_new_session(
            self.test_project_path,
            test_data="custom_test_data"
        )

        # Act
        save_result = self.manager.save_session(self.test_project_path, session)

        # Assert
        assert save_result is True

        session_file = self.manager.get_session_file_path(self.test_project_path)
        assert session_file.exists()

        # Проверяем содержимое файла
        with open(session_file, encoding='utf-8') as f:
            saved_data = json.load(f)

        assert saved_data['session_id'] == session.session_id
        assert saved_data['session_type'] == "test"
        assert saved_data['test_data'] == "custom_test_data"

    def test_load_existing_session(self):
        """Тест загрузки существующей сессии"""
        # Arrange - создаем и сохраняем сессию
        original_session = self.manager.create_new_session(
            self.test_project_path,
            test_data="load_test_data"
        )
        self.manager.save_session(self.test_project_path, original_session)

        # Act
        loaded_session = self.manager.load_session(self.test_project_path)

        # Assert
        assert loaded_session is not None
        assert loaded_session.session_id == original_session.session_id
        assert loaded_session.test_data == "load_test_data"
        assert loaded_session.session_type == "test"

    def test_load_nonexistent_session(self):
        """Тест загрузки несуществующей сессии"""
        # Arrange - не создаем сессию

        # Act
        loaded_session = self.manager.load_session(self.test_project_path)

        # Assert
        assert loaded_session is None

    def test_load_session_wrong_type(self):
        """Тест загрузки сессии неправильного типа"""
        # Arrange - создаем файл сессии с неправильным типом
        session_file = self.manager.get_session_file_path(self.test_project_path)
        session_file.parent.mkdir(parents=True, exist_ok=True)

        wrong_session_data = {
            "session_id": "wrong_session",
            "session_type": "wrong_type",  # Неправильный тип
            "project_path": str(self.test_project_path),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active"
        }

        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(wrong_session_data, f)

        # Act
        loaded_session = self.manager.load_session(self.test_project_path)

        # Assert
        assert loaded_session is None

    def test_delete_session(self):
        """Тест удаления сессии"""
        # Arrange - создаем сессию
        session = self.manager.create_new_session(self.test_project_path)
        self.manager.save_session(self.test_project_path, session)

        session_file = self.manager.get_session_file_path(self.test_project_path)
        assert session_file.exists()

        # Act
        delete_result = self.manager.delete_session(self.test_project_path)

        # Assert
        assert delete_result is True
        assert not session_file.exists()

    def test_delete_nonexistent_session(self):
        """Тест удаления несуществующей сессии"""
        # Arrange - не создаем сессию

        # Act
        delete_result = self.manager.delete_session(self.test_project_path)

        # Assert
        assert delete_result is True  # Должно возвращать True даже если файла нет

    def test_get_session_info_existing(self):
        """Тест получения информации о существующей сессии"""
        # Arrange
        session = self.manager.create_new_session(self.test_project_path)
        self.manager.save_session(self.test_project_path, session)

        # Act
        info = self.manager.get_session_info(self.test_project_path)

        # Assert
        assert info['exists'] is True
        assert info['session_type'] == "test"
        assert info['session_id'] == session.session_id
        assert info['status'] == session.status
        assert 'created_at' in info
        assert 'updated_at' in info

    def test_get_session_info_nonexistent(self):
        """Тест получения информации о несуществующей сессии"""
        # Arrange - не создаем сессию

        # Act
        info = self.manager.get_session_info(self.test_project_path)

        # Assert
        assert info['exists'] is False
        assert info['session_type'] == "test"

    def test_list_all_sessions_empty(self):
        """Тест получения списка сессий в пустом проекте"""
        # Arrange - не создаем сессии

        # Act
        sessions = self.manager.list_all_sessions(self.test_project_path)

        # Assert
        assert sessions == []

    def test_list_all_sessions_multiple(self):
        """Тест получения списка нескольких сессий"""
        # Arrange - создаем несколько типов сессий
        neira_dir = self.test_project_path / ".neira"
        neira_dir.mkdir(parents=True, exist_ok=True)

        # Создаем файлы разных типов сессий
        test_session_data = {
            "session_id": "test_session_1",
            "session_type": "test",
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        analysis_session_data = {
            "session_id": "analysis_session_1",
            "session_type": "analysis",
            "status": "completed",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        with open(neira_dir / "test_session.json", 'w') as f:
            json.dump(test_session_data, f)

        with open(neira_dir / "analysis_session.json", 'w') as f:
            json.dump(analysis_session_data, f)

        # Act
        sessions = self.manager.list_all_sessions(self.test_project_path)

        # Assert
        assert len(sessions) == 2

        session_types = [s['session_type'] for s in sessions]
        assert "test" in session_types
        assert "analysis" in session_types

    def test_cleanup_old_sessions(self):
        """Тест очистки старых сессий"""
        # Arrange - создаем старую и новую сессии
        neira_dir = self.test_project_path / ".neira"
        neira_dir.mkdir(parents=True, exist_ok=True)

        # Старая сессия (35 дней назад)
        old_date = (datetime.now() - timedelta(days=35)).isoformat()
        old_session_data = {
            "session_id": "old_session",
            "session_type": "test",
            "status": "completed",
            "created_at": old_date,
            "updated_at": old_date
        }

        # Новая сессия (5 дней назад)
        new_date = (datetime.now() - timedelta(days=5)).isoformat()
        new_session_data = {
            "session_id": "new_session",
            "session_type": "test",
            "status": "active",
            "created_at": new_date,
            "updated_at": new_date
        }

        old_file = neira_dir / "old_test_session.json"
        new_file = neira_dir / "new_test_session.json"

        with open(old_file, 'w') as f:
            json.dump(old_session_data, f)

        with open(new_file, 'w') as f:
            json.dump(new_session_data, f)

        # Act
        deleted_count = self.manager.cleanup_old_sessions(self.test_project_path, max_age_days=30)

        # Assert
        assert deleted_count == 1
        assert not old_file.exists()  # Старая сессия удалена
        assert new_file.exists()      # Новая сессия сохранена

    def test_session_update_timestamp(self):
        """Тест обновления временной метки при сохранении"""
        # Arrange
        session = self.manager.create_new_session(self.test_project_path)
        original_updated_at = session.updated_at

        # Небольшая задержка для различия временных меток
        import time
        time.sleep(0.01)

        # Act
        self.manager.save_session(self.test_project_path, session)

        # Assert
        assert session.updated_at != original_updated_at

        # Проверяем что новая метка действительно новее
        original_time = datetime.fromisoformat(original_updated_at)
        updated_time = datetime.fromisoformat(session.updated_at)
        assert updated_time > original_time


class TestBaseSessionManagerErrorHandling:
    """Тесты обработки ошибок в базовом менеджере"""

    def setup_method(self):
        """Настройка для каждого теста"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = TestSessionManager()
        self.test_project_path = self.temp_dir / "test_project"
        self.test_project_path.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Очистка после каждого теста"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_load_session_corrupted_json(self):
        """Тест загрузки сессии с поврежденным JSON"""
        # Arrange
        session_file = self.manager.get_session_file_path(self.test_project_path)
        session_file.parent.mkdir(parents=True, exist_ok=True)

        # Записываем невалидный JSON
        with open(session_file, 'w') as f:
            f.write("invalid json content {")

        # Act
        loaded_session = self.manager.load_session(self.test_project_path)

        # Assert
        assert loaded_session is None

    def test_save_session_permission_error(self):
        """Тест сохранения сессии при ошибке прав доступа"""
        # Arrange
        session = self.manager.create_new_session(self.test_project_path)

        # Мокируем ошибку записи файла
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            # Act
            save_result = self.manager.save_session(self.test_project_path, session)

            # Assert
            assert save_result is False

    def test_delete_session_permission_error(self):
        """Тест удаления сессии при ошибке прав доступа"""
        # Arrange
        session = self.manager.create_new_session(self.test_project_path)
        self.manager.save_session(self.test_project_path, session)

        self.manager.get_session_file_path(self.test_project_path)

        # Мокируем ошибку удаления файла
        with patch.object(Path, 'unlink', side_effect=PermissionError("Permission denied")):
            # Act
            delete_result = self.manager.delete_session(self.test_project_path)

            # Assert
            assert delete_result is False


def test_base_session_manager_exists():
    """Базовый тест что модуль импортируется"""
    assert BaseSessionState is not None
    assert BaseSessionManager is not None
