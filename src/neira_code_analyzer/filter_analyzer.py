"""
FilterAnalyzer - анализ структуры проекта и статистики файлов

Выделенный класс для анализа фильтров, ранее находившийся в ContextGenerator.
Отвечает только за сбор статистики и анализ, не за генерацию отчетов.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from code2prompt_rs import Code2Prompt

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Результат анализа фильтров"""
    success: bool
    total_files: int = 0
    total_size: int = 0
    total_tokens: int = 0
    file_stats: dict[str, dict[str, Any]] = None
    project_type: str | None = None
    recommendations: list[str] = None
    error_message: str | None = None

    def __post_init__(self):
        if self.file_stats is None:
            self.file_stats = {}
        if self.recommendations is None:
            self.recommendations = []

class FilterAnalyzer:
    """
    Анализирует структуру проекта и собирает статистику файлов

    Принцип единственной ответственности: только анализ, без генерации отчетов.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def analyze(
        self,
        path: str = ".",
        include_patterns: list[str] = None,
        exclude_patterns: list[str] = None,
        encoding: str = "cl100k"
    ) -> AnalysisResult:
        """
        Анализирует проект и собирает статистику

        Args:
            path: Путь к проекту
            include_patterns: Паттерны включения файлов
            exclude_patterns: Паттерны исключения файлов
            encoding: Тип кодировки для подсчета токенов

        Returns:
            AnalysisResult: Результат анализа со статистикой
        """
        try:
            self.logger.info(f"Начинаю анализ проекта: {path}")

            # Инициализируем Code2Prompt с правильными параметрами как в context_generator
            code2prompt = Code2Prompt(
                path=path,
                include_patterns=include_patterns or [],
                exclude_patterns=exclude_patterns or [],
                code_blocks=False,  # Только анализ, без кода
                line_numbers=False,
                absolute_paths=False
            )

            # Выполняем анализ используя session для получения статистики
            session = code2prompt.session()
            result = code2prompt.generate(encoding=encoding)

            # Извлекаем статистику из результата и сессии
            files_info = getattr(session, 'files', []) if hasattr(session, 'files') else []

            file_stats = self._process_file_stats(files_info)
            total_tokens = getattr(result, 'tokens', 0) if hasattr(result, 'tokens') else 0
            total_files = len(files_info)
            total_size = sum(getattr(f, 'size', 0) if hasattr(f, 'size') else 0 for f in files_info)

            # Определяем тип проекта
            project_type = self._detect_project_type(file_stats)

            # Генерируем рекомендации
            recommendations = self._generate_recommendations(file_stats, total_tokens)

            return AnalysisResult(
                success=True,
                total_files=total_files,
                total_size=total_size,
                total_tokens=total_tokens,
                file_stats=file_stats,
                project_type=project_type,
                recommendations=recommendations
            )

        except Exception as e:
            self.logger.error(f"Ошибка анализа: {e}")
            return AnalysisResult(
                success=False,
                error_message=f"Ошибка анализа: {str(e)}"
            )

    def _process_file_stats(self, files: list[Any]) -> dict[str, dict[str, Any]]:
        """Обрабатывает статистику файлов по расширениям"""
        stats = {}

        for file_info in files:
            # Обрабатываем разные форматы данных файлов
            if hasattr(file_info, 'path'):
                file_path = file_info.path
                size = getattr(file_info, 'size', 0)
            elif isinstance(file_info, dict):
                file_path = file_info.get("path", "")
                size = file_info.get("size", 0)
            else:
                # Если это просто строка пути
                file_path = str(file_info)
                size = 0

            path = Path(file_path)
            extension = path.suffix.lower() or "no_extension"

            if extension not in stats:
                stats[extension] = {
                    "count": 0,
                    "total_size": 0,
                    "files": []
                }

            stats[extension]["count"] += 1
            stats[extension]["total_size"] += size
            stats[extension]["files"].append(str(path))

        return stats

    def _detect_project_type(self, file_stats: dict[str, dict[str, Any]]) -> str | None:
        """
        Определяет тип проекта на основе найденных файлов

        Args:
            file_stats: Статистика файлов по расширениям

        Returns:
            str: Тип проекта или None если не определен
        """
        extensions = set(file_stats.keys())

        # Правила определения типа проекта (Data-Driven подход)
        project_detection_rules = [
            {"name": "Python", "required": {".py"}, "optional": {".pyx", ".pyi"}},
            {"name": "React/TypeScript", "required": {".tsx", ".jsx"}, "optional": {".ts", ".js"}},
            {"name": "TypeScript", "required": {".ts"}, "optional": {".tsx", ".js"}},
            {"name": "JavaScript", "required": {".js"}, "optional": {".jsx", ".json"}},
            {"name": "Rust", "required": {".rs"}, "optional": {".toml"}},
            {"name": "Go", "required": {".go"}, "optional": {".mod"}},
            {"name": "Java", "required": {".java"}, "optional": {".gradle", ".maven"}},
            {"name": "C++", "required": {".cpp", ".cc", ".cxx"}, "optional": {".h", ".hpp"}},
            {"name": "C", "required": {".c"}, "optional": {".h"}},
        ]

        for rule in project_detection_rules:
            if rule["required"].intersection(extensions):
                return rule["name"]

        return None

    def _generate_recommendations(self, file_stats: dict, total_tokens: int) -> list[str]:
        """
        Генерирует рекомендации по оптимизации фильтров

        Args:
            file_stats: Статистика файлов
            total_tokens: Общее количество токенов

        Returns:
            List[str]: Список рекомендаций
        """
        recommendations = []

        # Рекомендации по количеству токенов
        if total_tokens > 800000:
            recommendations.append("⚠️ Проект превышает 800K токенов - рекомендуется агрессивная фильтрация")
        elif total_tokens > 500000:
            recommendations.append("💡 Проект большой (>500K токенов) - можно применить дополнительные фильтры")

        # Рекомендации по типам файлов
        large_extensions = []
        for ext, stats in file_stats.items():
            if stats["count"] > 100:
                large_extensions.append(f"{ext} ({stats['count']} файлов)")

        if large_extensions:
            recommendations.append(f"📁 Много файлов: {', '.join(large_extensions)}")

        # Общие рекомендации по исключениям
        common_excludes = []
        extensions = set(file_stats.keys())

        if ".log" in extensions:
            common_excludes.append("*.log")
        if ".tmp" in extensions:
            common_excludes.append("*.tmp")
        if ".cache" in extensions:
            common_excludes.append("*.cache")

        if common_excludes:
            recommendations.append(f"🚫 Рекомендуется исключить: {', '.join(common_excludes)}")

        return recommendations
