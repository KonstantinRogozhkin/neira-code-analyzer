"""
Тесты для модуля валидации путей
Проверяют безопасность и корректность валидации против path traversal атак
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest

from neira_code_analyzer.path_validator import (
    PathValidationError,
    validate_file_path,
    validate_project_path,
    validate_safe_path,
)


class TestPathValidator:
    """Тесты для валидации путей"""

    def setup_method(self):
        """Настройка для каждого теста"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.txt"
        self.test_file.write_text("test content")

    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_validate_safe_path_success(self):
        """Тест успешной валидации безопасного пути"""
        result = validate_safe_path(str(self.test_file), self.temp_dir)
        assert result == self.test_file.resolve()

    def test_validate_safe_path_traversal_attack(self):
        """Тест предотвращения path traversal атаки"""
        malicious_path = "../../../etc/passwd"

        with pytest.raises(PathValidationError) as exc_info:
            validate_safe_path(malicious_path, self.temp_dir)

        # Должно обнаруживать подозрительный паттерн ../..
        assert "Suspicious path pattern detected" in str(exc_info.value)

    def test_validate_safe_path_suspicious_patterns(self):
        """Тест обнаружения подозрительных паттернов"""
        suspicious_paths = [
            "/etc/passwd",
            "/proc/version",
            "C:\\Windows\\System32",
            "..\\..\\sensitive"
        ]

        for path in suspicious_paths:
            with pytest.raises(PathValidationError) as exc_info:
                validate_safe_path(path, self.temp_dir)
            assert "Suspicious path pattern detected" in str(exc_info.value)

    def test_validate_project_path_success(self):
        """Тест успешной валидации пути проекта"""
        result = validate_project_path(self.temp_dir)
        assert result == Path(self.temp_dir).resolve()

    def test_validate_project_path_not_directory(self):
        """Тест ошибки для файла вместо директории"""
        with pytest.raises(PathValidationError) as exc_info:
            validate_project_path(str(self.test_file))

        assert "must be a directory" in str(exc_info.value)

    def test_validate_project_path_no_access(self):
        """Тест ошибки при отсутствии прав доступа"""
        with patch('os.access', return_value=False):
            with pytest.raises(PathValidationError) as exc_info:
                validate_project_path(self.temp_dir)

            assert "No read access" in str(exc_info.value)

    def test_validate_file_path_executable_blocked(self):
        """Тест блокировки исполняемых файлов"""
        exe_file = Path(self.temp_dir) / "malicious.exe"
        exe_file.write_text("fake exe")

        with pytest.raises(PathValidationError) as exc_info:
            validate_file_path(str(exe_file), self.temp_dir)

        assert "Executable file type not allowed" in str(exc_info.value)

    def test_validate_file_path_success(self):
        """Тест успешной валидации файла"""
        result = validate_file_path(str(self.test_file), self.temp_dir)
        assert result == self.test_file.resolve()

    def test_invalid_path_handling(self):
        """Тест обработки невалидных путей"""
        invalid_path = "/nonexistent/path/that/does/not/exist"

        # Абсолютный путь вне базовой директории должен вызывать ошибку
        with pytest.raises(PathValidationError) as exc_info:
            validate_safe_path(invalid_path, self.temp_dir)

        assert "outside allowed directory" in str(exc_info.value)

    def test_absolute_path_with_default_base_dir(self):
        """Тест абсолютного пути с base_dir='.' (по умолчанию)"""
        # Тестируем что временная директория работает с base_dir="."
        result = validate_safe_path(self.temp_dir)
        assert result == Path(self.temp_dir).resolve()
