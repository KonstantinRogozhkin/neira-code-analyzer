"""
AnalysisReporter - генерация отчетов по результатам анализа

Выделенный класс для создания markdown отчетов на основе AnalysisResult.
Отвечает только за форматирование и представление данных.
"""

from typing import Dict, List, Optional, Any
import logging
from .filter_analyzer import AnalysisResult

logger = logging.getLogger(__name__)

class AnalysisReporter:
    """
    Генерирует markdown отчеты на основе результатов анализа
    
    Принцип единственной ответственности: только генерация отчетов.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def generate_report(self, analysis_result: AnalysisResult) -> str:
        """
        Генерирует полный markdown отчет
        
        Args:
            analysis_result: Результат анализа от FilterAnalyzer
            
        Returns:
            str: Markdown отчет
        """
        if not analysis_result.success:
            return f"❌ Ошибка анализа: {analysis_result.error_message}"
        
        report_parts = [
            self._generate_header(analysis_result),
            self._generate_summary(analysis_result),
            self._generate_file_stats_table(analysis_result.file_stats),
            self._generate_recommendations(analysis_result.recommendations),
            self._generate_footer()
        ]
        
        return "\n\n".join(filter(None, report_parts))
    
    def _generate_header(self, result: AnalysisResult) -> str:
        """Генерирует заголовок отчета"""
        return f"""# 📊 Анализ структуры проекта

**🎯 Тип проекта:** {result.project_type or 'Не определен'}
**📁 Всего файлов:** {result.total_files}
**💾 Общий размер:** {self._format_size(result.total_size)}
**🔢 Токенов:** {result.total_tokens:,}"""
    
    def _generate_summary(self, result: AnalysisResult) -> str:
        """Генерирует сводку по статусу"""
        if result.total_tokens > 800000:
            status = "🔴 Критический"
            message = "Проект слишком большой для анализа"
        elif result.total_tokens > 500000:
            status = "🟡 Предупреждение"
            message = "Проект большой, рекомендуется фильтрация"
        else:
            status = "🟢 Нормальный"
            message = "Размер проекта в пределах нормы"
        
        return f"""## 📈 Статус проекта

**Статус:** {status}  
**Описание:** {message}"""
    
    def _generate_file_stats_table(self, file_stats: Dict[str, Dict[str, Any]]) -> str:
        """Генерирует таблицу статистики файлов"""
        if not file_stats:
            return "## 📋 Статистика файлов\n\nНет данных для отображения."
        
        # Сортируем по количеству файлов
        sorted_stats = sorted(
            file_stats.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        table_rows = ["| Расширение | Файлов | Размер | Примеры |",
                     "|------------|---------|---------|---------|"]
        
        for extension, stats in sorted_stats:
            count = stats["count"]
            total_size = self._format_size(stats["total_size"])
            examples = ", ".join(stats["files"][:3])  # Первые 3 файла
            if len(stats["files"]) > 3:
                examples += "..."
            
            table_rows.append(f"| {extension} | {count} | {total_size} | {examples} |")
        
        return f"""## 📋 Статистика файлов

{chr(10).join(table_rows)}"""
    
    def _generate_recommendations(self, recommendations: List[str]) -> str:
        """Генерирует раздел рекомендаций"""
        if not recommendations:
            return "## 💡 Рекомендации\n\nВсе хорошо! Дополнительных рекомендаций нет."
        
        recommendations_list = "\n".join(f"- {rec}" for rec in recommendations)
        
        return f"""## 💡 Рекомендации

{recommendations_list}

### 🛠️ Практические советы:

- **Для Python проектов:** Исключите `__pycache__/**`, `*.pyc`, `build/**`
- **Для веб-проектов:** Исключите `node_modules/**`, `dist/**`, `*.bundle.js`
- **Общие исключения:** `.git/**`, `*.log`, `*.tmp`, `.env`

### 📝 Как применить фильтры:

```bash
# Пример использования с фильтрами
get_context --path /path/to/project \\
    --include "*.py,*.md" \\
    --exclude "__pycache__/**,*.log"
```"""
    
    def _generate_footer(self) -> str:
        """Генерирует подвал отчета"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""---

*Отчет сгенерирован: {timestamp}*  
*Анализатор: neira-code-analyzer FilterAnalyzer v2.0*"""
    
    def _format_size(self, size_bytes: int) -> str:
        """Форматирует размер в человекочитаемый вид"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def generate_quick_summary(self, analysis_result: AnalysisResult) -> str:
        """
        Генерирует краткую сводку для быстрого просмотра
        
        Args:
            analysis_result: Результат анализа
            
        Returns:
            str: Краткая сводка
        """
        if not analysis_result.success:
            return f"❌ {analysis_result.error_message}"
        
        status_emoji = "🟢" if analysis_result.total_tokens < 500000 else "🟡" if analysis_result.total_tokens < 800000 else "🔴"
        
        return f"""{status_emoji} {analysis_result.project_type or 'Проект'}: {analysis_result.total_files} файлов, {analysis_result.total_tokens:,} токенов

🎯 **Топ расширения:**
{self._get_top_extensions(analysis_result.file_stats, 3)}

💡 **Рекомендации:** {len(analysis_result.recommendations)} пунктов"""
    
    def _get_top_extensions(self, file_stats: Dict[str, Dict[str, Any]], limit: int = 3) -> str:
        """Возвращает топ расширений файлов"""
        if not file_stats:
            return "нет данных"
        
        sorted_stats = sorted(
            file_stats.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        top_items = []
        for extension, stats in sorted_stats[:limit]:
            top_items.append(f"{extension} ({stats['count']})")
        
        return ", ".join(top_items) 