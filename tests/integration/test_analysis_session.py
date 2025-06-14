"""
Интеграционные тесты для analysis_session_manager.py

Тестирует:
- Полный цикл интерактивной сессии анализа
- Интеграцию с AI агентом
- Выполнение действий на коде
- Сохранение и восстановление состояния сессии
"""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from src.neira_code_analyzer.analysis_session_manager import (
    AnalysisSessionManager,
)


class TestAnalysisSessionIntegration:
    """Интеграционные тесты анализа сессий"""

    def setup_method(self):
        """Настройка для каждого теста"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_project_path = self.temp_dir / "test_project"
        self.test_project_path.mkdir(parents=True, exist_ok=True)

        # Создаем тестовые файлы проекта
        self.create_test_project()

        self.session_manager = AnalysisSessionManager()

    def teardown_method(self):
        """Очистка после каждого теста"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_test_project(self):
        """Создает тестовый проект с файлами"""
        # Создаем Python файл
        python_file = self.test_project_path / "main.py"
        python_file.write_text("""
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
""")

        # Создаем README
        readme_file = self.test_project_path / "README.md"
        readme_file.write_text("""
# Test Project

This is a test project for integration testing.
""")

        # Создаем requirements.txt
        requirements_file = self.test_project_path / "requirements.txt"
        requirements_file.write_text("pytest>=7.0.0\n")

    def test_create_new_analysis_session(self):
        """Тест создания новой сессии анализа"""
        # Act
        session = self.session_manager.create_new_session(
            self.test_project_path,
            params={"include_patterns": ["*.py"]},
            ai_model="gemini-2.5-pro-preview-06-05",
            template_name="code-review",
            user_query="Analyze code quality"
        )

        # Assert
        assert session.session_type == "analysis"
        assert session.project_path == str(self.test_project_path)
        assert session.template_name == "code-review"
        assert session.user_query == "Analyze code quality"
        assert session.status == "active"
        assert len(session.session_id) == 8

    def test_save_and_load_analysis_session(self):
        """Тест сохранения и загрузки сессии анализа"""
        # Arrange
        original_session = self.session_manager.create_new_session(
            self.test_project_path,
            params={"include_patterns": ["*.py", "*.js"]},
            ai_model="gemini-2.5-pro-preview-06-05",
            template_name="security-audit",
            user_query="Check for security issues"
        )

        # Добавляем историю взаимодействий
        original_session.interaction_history.append({
            "type": "user_input",
            "content": "Test user input",
            "timestamp": "2024-01-01T00:00:00"
        })

        # Act - сохраняем
        save_result = self.session_manager.save_session(self.test_project_path, original_session)
        assert save_result is True

        # Act - загружаем
        loaded_session = self.session_manager.load_session(self.test_project_path)

        # Assert
        assert loaded_session is not None
        assert loaded_session.session_id == original_session.session_id
        assert loaded_session.template_name == "security-audit"
        assert loaded_session.user_query == "Check for security issues"
        assert len(loaded_session.interaction_history) == 1
        assert loaded_session.interaction_history[0]["content"] == "Test user input"

    @pytest.mark.asyncio
    async def test_interactive_session_flow(self):
        """Тест полного интерактивного потока сессии"""
        # Arrange
        self.session_manager.create_new_session(
            self.test_project_path,
            params={"include_patterns": ["*.py"]},
            ai_model="gemini-2.5-pro-preview-06-05",
            template_name="code-review",
            user_query="Review the main.py file"
        )

        # Мокируем AI ответ
        mock_ai_response = {
            "status": "success",
            "findings": [
                {
                    "type": "suggestion",
                    "file": "main.py",
                    "line": 2,
                    "message": "Consider adding type hints",
                    "severity": "low"
                }
            ],
            "suggested_actions": [
                {
                    "action": "add_comment",
                    "file": "main.py",
                    "line": 1,
                    "content": "# TODO: Add type hints for better code quality"
                }
            ],
            "user_questions": [
                "Would you like me to add type hints to all functions?"
            ]
        }

        with patch('src.neira_code_analyzer.ai_utils.generate_ai_review_async') as mock_ai:
            mock_ai.return_value = json.dumps(mock_ai_response)

            # Act
            result = await self.session_manager.continue_session(
                self.test_project_path,
                "Please analyze the main.py file"
            )

            # Assert
            assert result is not None
            assert "findings" in result
            assert len(result["findings"]) == 1
            assert result["findings"][0]["message"] == "Consider adding type hints"

            # Проверяем что история обновилась
            updated_session = self.session_manager.load_session(self.test_project_path)
            assert len(updated_session.interaction_history) >= 2  # user input + ai response

    def test_session_context_preservation(self):
        """Тест сохранения контекста между взаимодействиями"""
        # Arrange
        session = self.session_manager.create_new_session(
            self.test_project_path,
            params={"include_patterns": ["*.py"]},
            ai_model="gemini-2.5-pro-preview-06-05",
            template_name="refactoring",
            user_query="Help refactor the code"
        )

        # Добавляем несколько взаимодействий
        session.interaction_history.extend([
            {
                "type": "user_input",
                "content": "First question",
                "timestamp": "2024-01-01T00:00:00"
            },
            {
                "type": "ai_response",
                "content": "First answer",
                "timestamp": "2024-01-01T00:01:00"
            },
            {
                "type": "user_input",
                "content": "Follow-up question",
                "timestamp": "2024-01-01T00:02:00"
            }
        ])

        # Act
        self.session_manager.save_session(self.test_project_path, session)
        loaded_session = self.session_manager.load_session(self.test_project_path)

        # Assert
        assert len(loaded_session.interaction_history) == 3
        assert loaded_session.interaction_history[0]["content"] == "First question"
        assert loaded_session.interaction_history[1]["content"] == "First answer"
        assert loaded_session.interaction_history[2]["content"] == "Follow-up question"

    def test_session_status_transitions(self):
        """Тест переходов статуса сессии"""
        # Arrange
        session = self.session_manager.create_new_session(self.test_project_path)
        assert session.status == "active"

        # Act & Assert - переход в completed
        session.status = "completed"
        self.session_manager.save_session(self.test_project_path, session)

        loaded_session = self.session_manager.load_session(self.test_project_path)
        assert loaded_session.status == "completed"

        # Act & Assert - переход в error
        session.status = "error"
        self.session_manager.save_session(self.test_project_path, session)

        loaded_session = self.session_manager.load_session(self.test_project_path)
        assert loaded_session.status == "error"

    def test_multiple_sessions_isolation(self):
        """Тест изоляции между разными сессиями"""
        # Arrange - создаем два разных проекта
        project1 = self.temp_dir / "project1"
        project2 = self.temp_dir / "project2"
        project1.mkdir()
        project2.mkdir()

        # Act - создаем сессии для разных проектов
        session1 = self.session_manager.create_new_session(
            project1,
            template_name="code-review",
            user_query="Review project 1"
        )

        session2 = self.session_manager.create_new_session(
            project2,
            template_name="security-audit",
            user_query="Audit project 2"
        )

        # Сохраняем обе сессии
        self.session_manager.save_session(project1, session1)
        self.session_manager.save_session(project2, session2)

        # Assert - загружаем и проверяем изоляцию
        loaded_session1 = self.session_manager.load_session(project1)
        loaded_session2 = self.session_manager.load_session(project2)

        assert loaded_session1.session_id != loaded_session2.session_id
        assert loaded_session1.template_name == "code-review"
        assert loaded_session2.template_name == "security-audit"
        assert loaded_session1.user_query == "Review project 1"
        assert loaded_session2.user_query == "Audit project 2"

    def test_session_cleanup_and_archival(self):
        """Тест очистки и архивирования старых сессий"""
        # Arrange - создаем сессию и искусственно делаем ее старой
        session = self.session_manager.create_new_session(self.test_project_path)

        # Изменяем дату создания на 40 дней назад
        from datetime import datetime, timedelta
        old_date = (datetime.now() - timedelta(days=40)).isoformat()
        session.created_at = old_date
        session.updated_at = old_date

        self.session_manager.save_session(self.test_project_path, session)

        # Act - выполняем очистку старых сессий (30 дней)
        deleted_count = self.session_manager.cleanup_old_sessions(
            self.test_project_path,
            max_age_days=30
        )

        # Assert
        assert deleted_count == 1

        # Проверяем что сессия действительно удалена
        loaded_session = self.session_manager.load_session(self.test_project_path)
        assert loaded_session is None


class TestAnalysisSessionErrorHandling:
    """Тесты обработки ошибок в анализе сессий"""

    def setup_method(self):
        """Настройка для каждого теста"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_project_path = self.temp_dir / "test_project"
        self.test_project_path.mkdir(parents=True, exist_ok=True)
        self.session_manager = AnalysisSessionManager()

    def teardown_method(self):
        """Очистка после каждого теста"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_ai_api_error_handling(self):
        """Тест обработки ошибок AI API"""
        # Arrange
        self.session_manager.create_new_session(self.test_project_path)

        # Мокируем ошибку AI API
        with patch('src.neira_code_analyzer.ai_utils.generate_ai_review_async') as mock_ai:
            mock_ai.side_effect = Exception("AI API Error")

            # Act & Assert
            with pytest.raises(Exception, match="AI API Error"):
                await self.session_manager.continue_session(
                    self.test_project_path,
                    "Test query"
                )

    def test_corrupted_session_file_recovery(self):
        """Тест восстановления после повреждения файла сессии"""
        # Arrange - создаем поврежденный файл сессии
        session_file = self.session_manager.get_session_file_path(self.test_project_path)
        session_file.parent.mkdir(parents=True, exist_ok=True)

        # Записываем невалидный JSON
        with open(session_file, 'w') as f:
            f.write("invalid json content {")

        # Act
        loaded_session = self.session_manager.load_session(self.test_project_path)

        # Assert
        assert loaded_session is None

        # Проверяем что можно создать новую сессию
        new_session = self.session_manager.create_new_session(self.test_project_path)
        save_result = self.session_manager.save_session(self.test_project_path, new_session)
        assert save_result is True

    def test_permission_error_handling(self):
        """Тест обработки ошибок прав доступа"""
        # Arrange
        session = self.session_manager.create_new_session(self.test_project_path)

        # Мокируем ошибку прав доступа при сохранении
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            # Act
            save_result = self.session_manager.save_session(self.test_project_path, session)

            # Assert
            assert save_result is False


class TestAnalysisSessionPerformance:
    """Тесты производительности анализа сессий"""

    def setup_method(self):
        """Настройка для каждого теста"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_project_path = self.temp_dir / "test_project"
        self.test_project_path.mkdir(parents=True, exist_ok=True)
        self.session_manager = AnalysisSessionManager()

    def teardown_method(self):
        """Очистка после каждого теста"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_large_interaction_history_performance(self):
        """Тест производительности с большой историей взаимодействий"""
        # Arrange
        session = self.session_manager.create_new_session(self.test_project_path)

        # Добавляем много взаимодействий
        for i in range(100):
            session.interaction_history.append({
                "type": "user_input",
                "content": f"Test interaction {i}",
                "timestamp": f"2024-01-01T{i:02d}:00:00"
            })

        # Act & Assert - операции должны выполняться быстро
        import time

        start_time = time.time()
        save_result = self.session_manager.save_session(self.test_project_path, session)
        save_time = time.time() - start_time

        start_time = time.time()
        loaded_session = self.session_manager.load_session(self.test_project_path)
        load_time = time.time() - start_time

        # Assert
        assert save_result is True
        assert loaded_session is not None
        assert len(loaded_session.interaction_history) == 100

        # Проверяем что операции выполняются достаточно быстро (< 1 секунды)
        assert save_time < 1.0
        assert load_time < 1.0

    def test_concurrent_session_access(self):
        """Тест конкурентного доступа к сессиям"""
        # Arrange
        session = self.session_manager.create_new_session(self.test_project_path)
        self.session_manager.save_session(self.test_project_path, session)

        # Act - симулируем конкурентный доступ
        import threading

        results = []
        errors = []

        def load_session_worker():
            try:
                loaded = self.session_manager.load_session(self.test_project_path)
                results.append(loaded.session_id if loaded else None)
            except Exception as e:
                errors.append(str(e))

        # Запускаем несколько потоков одновременно
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=load_session_worker)
            threads.append(thread)
            thread.start()

        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()

        # Assert
        assert len(errors) == 0  # Не должно быть ошибок
        assert len(results) == 5  # Все потоки должны получить результат
        assert all(r == session.session_id for r in results)  # Все должны получить одинаковый ID

def test_analysis_session_integration():
    """Базовый интеграционный тест"""
    # Создаем временную директорию
    temp_dir = Path(tempfile.mkdtemp())
    try:
        # Базовая проверка что директория создана
        assert temp_dir.exists()
        assert temp_dir.is_dir()

        # Проверяем что можем импортировать менеджер сессий
        from src.neira_code_analyzer.analysis_session_manager import AnalysisSessionManager
        manager = AnalysisSessionManager()
        assert manager is not None
        assert manager.session_type == "analysis"

    finally:
        # Очищаем
        shutil.rmtree(temp_dir)

def test_analysis_session_creation():
    """Тест создания сессии анализа"""
    from src.neira_code_analyzer.analysis_session_manager import AnalysisSessionManager

    temp_dir = Path(tempfile.mkdtemp())
    try:
        manager = AnalysisSessionManager()

        # Создаем сессию с правильными параметрами
        session = manager.create_new_session(
            temp_dir,
            params={"include_patterns": ["*.py"]},
            ai_model="gemini-2.5-pro-preview-06-05",
            template_name="code-review",
            user_query="Test analysis"
        )

        # Проверяем что сессия создана корректно
        assert session.session_type == "analysis"
        assert session.template_name == "code-review"
        assert session.user_query == "Test analysis"
        assert session.ai_model == "gemini-2.5-pro-preview-06-05"
        assert session.params["include_patterns"] == ["*.py"]

    finally:
        shutil.rmtree(temp_dir)

def test_analysis_session_save_load():
    """Тест сохранения и загрузки сессии"""
    from src.neira_code_analyzer.analysis_session_manager import AnalysisSessionManager

    temp_dir = Path(tempfile.mkdtemp())
    try:
        manager = AnalysisSessionManager()

        # Создаем и сохраняем сессию
        original_session = manager.create_new_session(
            temp_dir,
            params={"include_patterns": ["*.py", "*.js"]},
            ai_model="gemini-2.5-pro-preview-06-05",
            template_name="security-audit",
            user_query="Security check"
        )

        save_result = manager.save_session(temp_dir, original_session)
        assert save_result is True

        # Загружаем сессию
        loaded_session = manager.load_session(temp_dir)
        assert loaded_session is not None
        assert loaded_session.session_id == original_session.session_id
        assert loaded_session.template_name == "security-audit"
        assert loaded_session.user_query == "Security check"

    finally:
        shutil.rmtree(temp_dir)
