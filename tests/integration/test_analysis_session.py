"""
Исправленные интеграционные тесты для analysis_session_manager.py

Тестирует:
- Полный цикл интерактивной сессии анализа
- Сохранение и восстановление состояния сессии  
- Правильную работу с текущим API
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from neira_code_analyzer.analysis_session_manager import (
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
        assert session.status == "analyzing"
        assert len(session.session_id) >= 8
        assert session.ai_model == "gemini-2.5-pro-preview-06-05"
        assert session.params == {"include_patterns": ["*.py"]}

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
        updated_session = self.session_manager.add_analysis_interaction(
            original_session,
            "Test user input",
            "Test AI response"
        )

        # Act - сохраняем
        save_result = self.session_manager.save_session(self.test_project_path, updated_session)
        assert save_result is True

        # Act - загружаем
        loaded_session = self.session_manager.load_session(self.test_project_path)

        # Assert
        assert loaded_session is not None
        assert loaded_session.session_id == original_session.session_id
        assert loaded_session.template_name == "security-audit"
        assert loaded_session.user_query == "Check for security issues"
        assert len(loaded_session.analysis_history) == 1
        assert loaded_session.analysis_history[0]["user_request"] == "Test user input"

    def test_interactive_session_flow(self):
        """Тест интерактивного потока сессии"""
        # Arrange
        session = self.session_manager.create_new_session(
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
            ]
        }

        # Act
        result = self.session_manager.add_analysis_interaction(
            session,
            "Please analyze the main.py file",
            json.dumps(mock_ai_response)
        )

        # Assert
        assert result is not None
        assert len(result.analysis_history) == 1
        assert result.analysis_history[0]["user_request"] == "Please analyze the main.py file"
        assert result.status == "interactive"

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
        session = self.session_manager.add_analysis_interaction(
            session,
            "First question",
            "First answer"
        )

        session = self.session_manager.add_analysis_interaction(
            session,
            "Follow-up question",
            "Follow-up answer"
        )

        # Act & Assert
        assert len(session.analysis_history) == 2
        assert session.analysis_history[0]["user_request"] == "First question"
        assert session.analysis_history[1]["user_request"] == "Follow-up question"
        assert session.step == 3  # Started at 1, incremented twice

    def test_session_status_transitions(self):
        """Тест переходов статуса сессии"""
        # Arrange
        session = self.session_manager.create_new_session(
            self.test_project_path,
            params={"include_patterns": ["*.py"]},
            ai_model="gemini-2.5-pro-preview-06-05",
            template_name="code-review"
        )

        # Assert initial status
        assert session.status == "analyzing"

        # Act - добавляем взаимодействие
        session = self.session_manager.add_analysis_interaction(
            session,
            "Test request",
            "Test response"
        )

        # Assert status changed to interactive
        assert session.status == "interactive"

        # Act - завершаем сессию
        final_analysis = {"summary": "Analysis completed"}
        session = self.session_manager.complete_session(session, final_analysis)

        # Assert status changed to completed
        assert session.status == "completed"
        assert len(session.completed_analyses) == 1

    def test_multiple_sessions_isolation(self):
        """Тест изоляции множественных сессий"""
        import time

        # Arrange - создаем две папки проектов
        project1_path = self.test_project_path / "project1"
        project2_path = self.test_project_path / "project2"
        project1_path.mkdir()
        project2_path.mkdir()

        # Act - создаем сессии для разных проектов
        session1 = self.session_manager.create_new_session(
            project1_path,
            params={"include_patterns": ["*.py"]},
            ai_model="gemini-2.5-pro-preview-06-05",
            template_name="code-review"
        )

        # Небольшая задержка чтобы session_id были разные
        time.sleep(0.01)

        session2 = self.session_manager.create_new_session(
            project2_path,
            params={"include_patterns": ["*.py", "*.js"]},
            ai_model="gemini-2.5-pro-preview-06-05",
            template_name="security-audit"
        )

        # Assert сессии изолированы
        assert session1.project_path != session2.project_path
        assert session1.template_name == "code-review"
        assert session2.template_name == "security-audit"

    def test_session_cleanup_and_archival(self):
        """Тест очистки и архивирования сессии"""
        # Arrange
        session = self.session_manager.create_new_session(
            self.test_project_path,
            params={"include_patterns": ["*.py"]},
            ai_model="gemini-2.5-pro-preview-06-05",
            template_name="code-review"
        )

        # Сохраняем сессию
        self.session_manager.save_session(self.test_project_path, session)

        # Проверяем что сессия существует
        loaded_session = self.session_manager.load_session(self.test_project_path)
        assert loaded_session is not None

        # Act - очищаем сессию (используем delete_session вместо cleanup_session)
        cleanup_result = self.session_manager.delete_session(self.test_project_path)

        # Assert
        assert cleanup_result is True
        # После очистки сессия не должна загружаться
        cleaned_session = self.session_manager.load_session(self.test_project_path)
        assert cleaned_session is None


class TestAnalysisSessionErrorHandling:
    """Тесты обработки ошибок анализа сессий"""

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

    def test_corrupted_session_file_recovery(self):
        """Тест восстановления при повреждении файла сессии"""
        # Arrange - создаем поврежденный файл сессии
        session_dir = self.test_project_path / ".neira" / "sessions"
        session_dir.mkdir(parents=True, exist_ok=True)

        corrupted_file = session_dir / "analysis_session.json"
        corrupted_file.write_text("corrupted json data")

        # Act - пытаемся загрузить сессию
        loaded_session = self.session_manager.load_session(self.test_project_path)

        # Assert - сессия не загружается, но не падает
        assert loaded_session is None

        # Act - создаем новую сессию
        new_session = self.session_manager.create_new_session(
            self.test_project_path,
            params={"include_patterns": ["*.py"]},
            ai_model="gemini-2.5-pro-preview-06-05",
            template_name="code-review"
        )

        # Assert - новая сессия создается нормально
        assert new_session is not None
        assert new_session.status == "analyzing"
