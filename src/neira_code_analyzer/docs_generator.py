"""
Рефакторированный генератор документации

Заменил "God Object" на композицию специализированных классов:
- DocsAgent: умный оркестратор с JSON контрактом
- DocsSessionManager: управление состоянием сессии
- ActionExecutor: выполнение структурированных действий

Устранены проблемы:
❌ Хрупкий парсинг текста → ✅ JSON контракт с ИИ
❌ Смешение ответственностей → ✅ Принцип единственной ответственности
❌ Тестовый код в продакшне → ✅ Демо-логика вынесена в отдельный слой
"""

import logging

from .docs_agent import DocsAgent

logger = logging.getLogger(__name__)

class DocsGenerator:
    """
    Рефакторированный генератор документации

    Теперь это тонкая обертка над DocsAgent, которая сохраняет
    обратную совместимость API но использует новую архитектуру.

    Преимущества новой архитектуры:
    - Четкое разделение ответственностей (SRP)
    - JSON контракт с ИИ вместо хрупкого парсинга
    - Типизированные структуры данных
    - Простота тестирования и расширения
    """

    def __init__(self):
        """Инициализация с использованием нового DocsAgent"""
        self.docs_agent = DocsAgent()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def generate_docs(self,
                          path: str = ".",
                          docs_structure: str = "standard",
                          scan_depth: int = 3,
                          max_file_size: int = 400,
                          archive_processed: bool = True,
                          update_changelog: bool = True,
                          git_scan_days: int = 14,
                          compress_guides: bool = True,
                          target_guide_length: int = 150,
                          ai_model: str = "gemini-2.5-pro-preview-06-05",
                          **kwargs) -> str:
        """
        Генерация документации с использованием новой архитектуры

        Args:
            path: Путь к проекту для анализа
            docs_structure: Структура документации (пока не используется)
            scan_depth: Глубина сканирования (пока не используется)
            max_file_size: Максимальный размер файла (пока не используется)
            archive_processed: Архивировать обработанные файлы (пока не используется)
            update_changelog: Обновлять changelog (пока не используется)
            git_scan_days: Дни для сканирования git (пока не используется)
            compress_guides: Сжимать руководства (пока не используется)
            target_guide_length: Целевая длина руководства (пока не используется)
            ai_model: Модель ИИ для использования
            **kwargs: Дополнительные параметры

        Returns:
            str: Отчет о генерации документации

        Note:
            Многие параметры пока не используются в новой архитектуре.
            Они сохранены для обратной совместимости и будут реализованы
            в будущих версиях по мере необходимости.
        """

        self.logger.info("🚀 Запуск рефакторированной генерации документации")
        self.logger.info(f"📁 Проект: {path}")
        self.logger.info(f"🤖 ИИ модель: {ai_model}")

        # Собираем все параметры для передачи в DocsAgent
        params = {
            'docs_structure': docs_structure,
            'scan_depth': scan_depth,
            'max_file_size': max_file_size,
            'archive_processed': archive_processed,
            'update_changelog': update_changelog,
            'git_scan_days': git_scan_days,
            'compress_guides': compress_guides,
            'target_guide_length': target_guide_length,
            **kwargs
        }

        try:
            # Делегируем всю работу DocsAgent
            result = await self.docs_agent.generate_docs(
                path=path,
                ai_model=ai_model,
                **params
            )

            self.logger.info("✅ Генерация документации завершена успешно")
            return result

        except Exception as e:
            error_msg = f"Ошибка генерации документации: {str(e)}"
            self.logger.error(error_msg)

            # Возвращаем понятный отчет об ошибке
            return f"""❌ ОШИБКА ГЕНЕРАЦИИ ДОКУМЕНТАЦИИ

🚨 Ошибка: {error_msg}

📁 Проект: {path}
🤖 ИИ модель: {ai_model}

🔧 Рекомендации:
1. Проверьте корректность пути к проекту
2. Убедитесь в доступности ИИ модели
3. Проверьте права доступа к файлам
4. Очистите временные файлы сессии (.docs_session/)

💡 Если проблема повторяется, обратитесь к логам для детального анализа.
"""

# Для обратной совместимости экспортируем главный класс
__all__ = ['DocsGenerator']
