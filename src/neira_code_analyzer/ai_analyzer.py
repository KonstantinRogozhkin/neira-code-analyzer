"""
NeiraAnalyzer - Унифицированный анализатор кода с ИИ

РЕФАКТОРИНГ: Обновлен для использования продвинутой архитектуры по образцу DocsAgent.
Теперь поддерживает интерактивные сессии, JSON контракт с ИИ и управление состоянием.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

# Импорты новой архитектуры
from .analysis_agent import AnalysisAgent

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.5-pro-preview-06-05"
DEFAULT_TEMPLATE_NAME = "code-review"

@dataclass
class AnalysisJob:
    """Класс для хранения параметров анализа кода (УНИФИЦИРОВАННЫЙ)"""
    path: str
    template_name: str = DEFAULT_TEMPLATE_NAME
    include_patterns: list = None
    exclude_patterns: list = None
    max_tokens: int = 1000000
    ai_model: str = DEFAULT_MODEL
    preset_name: str = None
    merge_with_preset: bool = False
    save_as_preset: str = None
    user_query: str = None  # Пользовательский запрос/комментарий для фокуса анализа

    def __post_init__(self):
        """Инициализация значений по умолчанию"""
        if self.include_patterns is None:
            self.include_patterns = []
        if self.exclude_patterns is None:
            self.exclude_patterns = []

class NeiraAnalyzer:
    """
    Унифицированный анализатор кода с продвинутой архитектурой

    АРХИТЕКТУРНЫЕ УЛУЧШЕНИЯ (ИСПРАВЛЕНО):
    - Использует AnalysisAgent как единственный источник истины
    - Поддерживает JSON контракт с ИИ через AnalysisAgent
    - Управление состоянием через AnalysisSessionManager
    - Безопасное выполнение действий через AnalysisActionExecutor
    - Устранена неконсистентность архитектуры ИИ
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # ИСПРАВЛЕНИЕ КРИТИЧЕСКОЙ ПРОБЛЕМЫ №1: Единая архитектура ИИ
        # Используем только AnalysisAgent, убираем дублирование логики
        try:
            self.analysis_agent = AnalysisAgent()
            self.logger.info("✅ NeiraAnalyzer: Продвинутая архитектура ИИ инициализирована")
        except Exception as e:
            self.logger.error(f"❌ NeiraAnalyzer: Критическая ошибка инициализации AnalysisAgent: {e}")
            self.analysis_agent = None

    async def perform_code_review(
        self,
        path: str = ".",
        template_name: str = DEFAULT_TEMPLATE_NAME,
        include_patterns: list[str] = None,
        exclude_patterns: list[str] = None,
        max_tokens: int = 1000000,
        ai_model: str = DEFAULT_MODEL,
        preset_name: str = None,
        merge_with_preset: bool = False,
        save_as_preset: str = None,
        user_query: str = None,
        session_id: str = ""
    ) -> str:
        """
        Выполняет анализ кода с использованием продвинутой архитектуры

        ИСПРАВЛЕНИЕ: Полностью делегирует выполнение AnalysisAgent.
        Устраняет неконсистентность между простой и продвинутой моделями ИИ.

        Args:
            path: Путь к проекту
            template_name: Шаблон анализа
            include_patterns: Паттерны включения файлов
            exclude_patterns: Паттерны исключения файлов
            max_tokens: Максимальное количество токенов
            ai_model: Модель ИИ
            preset_name: Имя пресета фильтров
            merge_with_preset: Объединить с пресетом
            save_as_preset: Сохранить как пресет
            user_query: Пользовательский запрос для фокуса анализа
            session_id: ID существующей сессии для продолжения диалога

        Returns:
            str: Результат анализа
        """
        self.logger.info(f"🚀 Запуск унифицированного анализа кода: {path}")

        # Валидация критических зависимостей
        if not self.analysis_agent:
            return self._generate_critical_error_report(
                "AnalysisAgent не инициализирован. Система не может выполнить анализ."
            )

        # Валидация параметров
        validation_error = self._validate_parameters(
            path, template_name, include_patterns, exclude_patterns,
            max_tokens, user_query
        )
        if validation_error:
            return validation_error

        try:
            # ИСПРАВЛЕНИЕ: Только продвинутая архитектура через AnalysisAgent
            analysis_result = await self.analysis_agent.analyze_code(
                path=path,
                template_name=template_name,
                ai_model=ai_model,
                user_query=user_query,
                session_id=session_id,
                include_patterns=include_patterns or [],
                exclude_patterns=exclude_patterns or [],
                max_tokens=max_tokens,
                preset_name=preset_name,
                merge_with_preset=merge_with_preset,
                save_as_preset=save_as_preset
            )

            self.logger.info("✅ Унифицированный анализ завершен успешно")
            return analysis_result

        except Exception as e:
            error_msg = f"❌ Критическая ошибка унифицированного анализа: {str(e)}"
            self.logger.error(error_msg)
            return self._generate_critical_error_report(str(e))

    def _validate_parameters(
        self,
        path: str,
        template_name: str,
        include_patterns: list[str],
        exclude_patterns: list[str],
        max_tokens: int,
        user_query: str
    ) -> str:
        """Валидация входных параметров с детальным отчетом об ошибках"""

        if not path or not isinstance(path, str):
            return self._generate_validation_error("Параметр 'path' обязателен и должен быть строкой.")

        if not template_name or not isinstance(template_name, str):
            return self._generate_validation_error(
                f"Параметр 'template_name' должен быть строкой. Получено: {type(template_name)}"
            )

        if include_patterns is not None and not isinstance(include_patterns, list):
            return self._generate_validation_error(
                f"'include_patterns' должен быть списком. Получено: {type(include_patterns)}"
            )

        if exclude_patterns is not None and not isinstance(exclude_patterns, list):
            return self._generate_validation_error(
                f"'exclude_patterns' должен быть списком. Получено: {type(exclude_patterns)}"
            )

        if user_query is not None and not isinstance(user_query, str):
            return self._generate_validation_error(
                f"'user_query' должен быть строкой или None. Получено: {type(user_query)}"
            )

        if not isinstance(max_tokens, int) or max_tokens <= 0:
            return self._generate_validation_error(
                f"'max_tokens' должен быть положительным числом. Получено: {max_tokens}"
            )

        project_path = Path(path)
        if not project_path.exists():
            return self._generate_validation_error(f"Путь '{path}' не существует.")

        return ""  # Валидация пройдена

    def _generate_validation_error(self, message: str) -> str:
        """Генерирует стандартизированное сообщение об ошибке валидации"""
        return f"""# ❌ Ошибка валидации параметров

**Проблема:** {message}

**Действие:** Проверьте правильность переданных параметров и повторите запрос.

---
*NeiraAnalyzer v2.0 - Продвинутая архитектура ИИ*
"""

    def _generate_critical_error_report(self, error_message: str) -> str:
        """Генерирует отчет о критической ошибке системы"""
        return f"""# 🚨 Критическая ошибка системы

**Описание:** {error_message}

**Возможные причины:**
- Проблемы с инициализацией компонентов системы
- Недоступность ИИ-сервисов
- Нарушение целостности архитектуры

**Рекомендуемые действия:**
1. Перезапустите MCP сервер
2. Проверьте конфигурацию переменных окружения
3. Убедитесь в доступности всех зависимостей

---
*NeiraAnalyzer v2.0 - Система безопасной обработки ошибок*
"""
