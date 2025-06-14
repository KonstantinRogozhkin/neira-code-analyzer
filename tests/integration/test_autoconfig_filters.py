"""
Интеграционный тест автонастройки фильтров в get_analyze

Проверяет, что get_analyze автоматически вызывает set_filters
для новых проектов без конфигурации .neira
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from neira_code_analyzer.main import get_analyze_tool


class TestAutoConfigFilters:
    """Тесты автонастройки фильтров"""

    def setup_method(self):
        """Настройка для каждого теста"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_project_path = self.temp_dir / "test_project"
        self.test_project_path.mkdir(parents=True, exist_ok=True)

        # Создаем тестовые файлы проекта
        self.create_test_project()

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

    @pytest.mark.asyncio
    async def test_get_analyze_autoconfig_filters(self):
        """Тест автонастройки фильтров в get_analyze для нового проекта"""

        # Убеждаемся что .neira файлов нет
        neira_file = self.test_project_path / ".neira"
        assert not neira_file.exists()

        # Мокируем NeiraAnalyzer чтобы не делать реальный AI запрос
        with patch('neira_code_analyzer.main.get_cached_service') as mock_get_service:
            # Мокируем FilterSetupService
            mock_filter_service = MagicMock()
            mock_filter_result = MagicMock()
            mock_filter_result.success = True
            mock_filter_result.optimization_stats = "Сокращение на 50%"
            mock_filter_service.setup_project_filters = AsyncMock(return_value=mock_filter_result)

            # Мокируем NeiraAnalyzer
            mock_ai_analyzer = MagicMock()
            mock_ai_analyzer.perform_code_review = AsyncMock(return_value="Мокированный результат анализа")

            def mock_service_factory(service_class):
                if service_class.__name__ == "FilterSetupService":
                    return mock_filter_service
                elif service_class.__name__ == "NeiraAnalyzer":
                    return mock_ai_analyzer
                else:
                    return MagicMock()

            mock_get_service.side_effect = mock_service_factory

            # Act - вызываем get_analyze для проекта без конфигурации
            arguments = {
                "path": str(self.test_project_path),
                "template_name": "code-review",
                "user_query": "Test analysis"
            }

            result = await get_analyze_tool(arguments)

            # Assert - проверяем что set_filters был вызван автоматически
            mock_filter_service.setup_project_filters.assert_called_once()
            # Проверяем аргументы вызова отдельно для избежания проблем с путями
            call_args = mock_filter_service.setup_project_filters.call_args
            assert call_args.kwargs["preset_name"] == "aggressive"
            assert call_args.kwargs["include_patterns"] == []
            assert call_args.kwargs["exclude_patterns"] == []
            assert call_args.kwargs["merge_with_preset"] == False
            assert call_args.kwargs["encoding"] == "cl100k"
            # Путь содержит наш тестовый проект
            assert "test_project" in call_args.kwargs["path"]

            # Проверяем что анализ был выполнен
            mock_ai_analyzer.perform_code_review.assert_called_once()

            # Проверяем результат
            assert len(result) == 1
            assert result[0].text == "Мокированный результат анализа"

    @pytest.mark.asyncio
    async def test_get_analyze_with_existing_config(self):
        """Тест что автонастройка НЕ выполняется если конфигурация уже есть"""

        # Создаем .neira файл
        neira_file = self.test_project_path / ".neira"
        neira_config = {
            "include_patterns": ["*.py"],
            "exclude_patterns": ["tests/**"],
            "encoding": "cl100k"
        }
        neira_file.write_text(json.dumps(neira_config, indent=2))

        # Мокируем сервисы
        with patch('neira_code_analyzer.main.get_cached_service') as mock_get_service:
            mock_filter_service = MagicMock()
            mock_ai_analyzer = MagicMock()
            mock_ai_analyzer.perform_code_review = AsyncMock(return_value="Анализ с существующей конфигурацией")

            def mock_service_factory(service_class):
                if service_class.__name__ == "FilterSetupService":
                    return mock_filter_service
                elif service_class.__name__ == "NeiraAnalyzer":
                    return mock_ai_analyzer
                else:
                    return MagicMock()

            mock_get_service.side_effect = mock_service_factory

            # Act - вызываем get_analyze для проекта с конфигурацией
            arguments = {
                "path": str(self.test_project_path),
                "template_name": "code-review",
                "user_query": "Test analysis"
            }

            result = await get_analyze_tool(arguments)

            # Assert - проверяем что set_filters НЕ был вызван
            mock_filter_service.setup_project_filters.assert_not_called()

            # Но анализ был выполнен
            mock_ai_analyzer.perform_code_review.assert_called_once()

            assert len(result) == 1
            assert result[0].text == "Анализ с существующей конфигурацией"

    @pytest.mark.asyncio
    async def test_get_analyze_autoconfig_failure_graceful(self):
        """Тест что анализ продолжается даже если автонастройка фильтров не удалась"""

        # Убеждаемся что .neira файлов нет
        neira_file = self.test_project_path / ".neira"
        assert not neira_file.exists()

        # Мокируем сервисы с ошибкой в FilterSetupService
        with patch('neira_code_analyzer.main.get_cached_service') as mock_get_service:
            mock_filter_service = MagicMock()
            mock_filter_result = MagicMock()
            mock_filter_result.success = False
            mock_filter_result.error_message = "Ошибка настройки фильтров"
            mock_filter_service.setup_project_filters = AsyncMock(return_value=mock_filter_result)

            mock_ai_analyzer = MagicMock()
            mock_ai_analyzer.perform_code_review = AsyncMock(return_value="Анализ несмотря на ошибку фильтров")

            def mock_service_factory(service_class):
                if service_class.__name__ == "FilterSetupService":
                    return mock_filter_service
                elif service_class.__name__ == "NeiraAnalyzer":
                    return mock_ai_analyzer
                else:
                    return MagicMock()

            mock_get_service.side_effect = mock_service_factory

            # Act - вызываем get_analyze
            arguments = {
                "path": str(self.test_project_path),
                "template_name": "code-review"
            }

            result = await get_analyze_tool(arguments)

            # Assert - автонастройка была попытана
            mock_filter_service.setup_project_filters.assert_called_once()

            # Но анализ всё равно продолжился
            mock_ai_analyzer.perform_code_review.assert_called_once()

            assert len(result) == 1
            assert result[0].text == "Анализ несмотря на ошибку фильтров"
