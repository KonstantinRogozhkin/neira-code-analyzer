"""
Unit тесты для FileSizeFilter

Quick Feature Add - Тестирование нового фильтра по размеру файла
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from neira_code_analyzer.filters import MAX_FILE_SIZE_KB, FileSizeFilter, create_file_size_filter


class TestFileSizeFilter:
    """Тесты для FileSizeFilter класса"""

    def test_init_default_size(self):
        """Тест инициализации с размером по умолчанию"""
        filter_obj = FileSizeFilter()
        assert filter_obj.max_size_kb == MAX_FILE_SIZE_KB
        assert filter_obj.max_size_bytes == MAX_FILE_SIZE_KB * 1024

    def test_init_custom_size(self):
        """Тест инициализации с кастомным размером"""
        custom_size = 100
        filter_obj = FileSizeFilter(max_size_kb=custom_size)
        assert filter_obj.max_size_kb == custom_size
        assert filter_obj.max_size_bytes == custom_size * 1024

    def test_should_exclude_file_not_exists(self):
        """Тест для несуществующего файла"""
        filter_obj = FileSizeFilter(max_size_kb=100)
        non_existent_file = Path("/non/existent/file.txt")

        should_exclude, reason = filter_obj.should_exclude_file(non_existent_file)
        assert not should_exclude
        assert reason == ""

    def test_should_exclude_file_small_file(self):
        """Тест для маленького файла"""
        filter_obj = FileSizeFilter(max_size_kb=100)

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"small content")
            tmp_path = Path(tmp.name)

        try:
            should_exclude, reason = filter_obj.should_exclude_file(tmp_path)
            assert not should_exclude
            assert reason == ""
        finally:
            tmp_path.unlink()

    def test_should_exclude_file_large_file(self):
        """Тест для большого файла"""
        filter_obj = FileSizeFilter(max_size_kb=1)  # 1KB лимит

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # Создаем файл больше 1KB
            tmp.write(b"x" * 2048)  # 2KB
            tmp_path = Path(tmp.name)

        try:
            should_exclude, reason = filter_obj.should_exclude_file(tmp_path)
            assert should_exclude
            assert "слишком большой" in reason
            assert "2.00MB" in reason or "0.00MB" in reason  # Размер может округляться
        finally:
            tmp_path.unlink()

    def test_should_exclude_file_stat_error(self):
        """Тест обработки ошибки при получении размера файла"""
        filter_obj = FileSizeFilter(max_size_kb=100)

        # Мокаем Path объект для симуляции ошибки
        with patch("pathlib.Path") as mock_path_class:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.is_file.return_value = True
            mock_path.stat.side_effect = OSError("Access denied")
            mock_path_class.return_value = mock_path

            Path("/test/file.txt")
            should_exclude, reason = filter_obj.should_exclude_file(mock_path)
            assert not should_exclude
            assert reason == ""

    def test_filter_file_list_mixed_sizes(self):
        """Тест фильтрации списка файлов с разными размерами"""
        filter_obj = FileSizeFilter(max_size_kb=1)  # 1KB лимит

        # Создаем временные файлы
        small_files = []
        large_files = []

        try:
            # Маленький файл
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(b"small")
                small_files.append(Path(tmp.name))

            # Большой файл
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(b"x" * 2048)  # 2KB
                large_files.append(Path(tmp.name))

            all_files = small_files + large_files
            remaining, excluded = filter_obj.filter_file_list(all_files)

            assert len(remaining) == 1
            assert len(excluded) == 1
            assert remaining[0] in small_files
            assert any(str(large_files[0]) in exc for exc in excluded)

        finally:
            # Cleanup
            for file_path in small_files + large_files:
                try:
                    file_path.unlink()
                except FileNotFoundError:
                    pass

    def test_get_stats_empty_list(self):
        """Тест статистики для пустого списка"""
        filter_obj = FileSizeFilter()
        stats = filter_obj.get_stats([])

        expected_stats = {
            "total_files": 0,
            "large_files_count": 0,
            "total_size_mb": 0.0,
            "large_files_size_mb": 0.0,
            "max_file_size_mb": 0.0,
            "largest_file": None,
        }

        assert stats == expected_stats

    def test_get_stats_with_files(self):
        """Тест статистики с реальными файлами"""
        filter_obj = FileSizeFilter(max_size_kb=1)  # 1KB лимит

        files_to_cleanup = []

        try:
            # Создаем тестовые файлы
            with tempfile.NamedTemporaryFile(delete=False) as small:
                small.write(b"small")
                small_path = Path(small.name)
                files_to_cleanup.append(small_path)

            with tempfile.NamedTemporaryFile(delete=False) as large:
                large.write(b"x" * 2048)  # 2KB
                large_path = Path(large.name)
                files_to_cleanup.append(large_path)

            stats = filter_obj.get_stats([small_path, large_path])

            assert stats["total_files"] == 2
            assert stats["large_files_count"] == 1
            assert stats["total_size_mb"] > 0
            assert stats["large_files_size_mb"] > 0
            assert stats["max_file_size_mb"] > 0
            assert stats["largest_file"] == str(large_path)

        finally:
            for file_path in files_to_cleanup:
                try:
                    file_path.unlink()
                except FileNotFoundError:
                    pass

    def test_create_file_size_filter_factory(self):
        """Тест factory функции"""
        # Тест с размером по умолчанию
        filter_default = create_file_size_filter()
        assert filter_default.max_size_kb == MAX_FILE_SIZE_KB

        # Тест с кастомным размером
        custom_size = 200
        filter_custom = create_file_size_filter(max_size_kb=custom_size)
        assert filter_custom.max_size_kb == custom_size


if __name__ == "__main__":
    pytest.main([__file__])
