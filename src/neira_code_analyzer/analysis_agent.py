"""
AnalysisAgent - умный оркестратор анализа и исправления кода с ИИ

Отвечает за:
- Координацию интерактивного процесса анализа кода
- JSON контракт с ИИ для структурированных ответов
- Интеграцию с AnalysisSessionManager и AnalysisActionExecutor
- Поддержку многошагового и интерактивного анализа
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .analysis_action_executor import AnalysisActionExecutor
from .analysis_session_manager import AnalysisSessionManager, AnalysisSessionState
from .response_parser import AIResponseParser

logger = logging.getLogger(__name__)

@dataclass
class AnalysisAIResponse:
    """Структурированный ответ от ИИ для анализа кода"""
    status: str  # 'analyzing', 'suggesting_fixes', 'ready_to_execute', 'completed', 'error'
    analysis_summary: str
    findings: list[dict[str, Any]]  # Список найденных проблем/рекомендаций
    suggested_actions: list[dict[str, Any]]  # JSON действия для исправления
    next_focus: str | None = None  # Следующий фокус анализа
    questions_for_user: list[str] = None  # Вопросы к пользователю

    @classmethod
    def from_json(cls, json_data: str) -> 'AnalysisAIResponse':
        """Создает объект из JSON строки используя централизованный парсер"""
        parsed_data = AIResponseParser.from_json(json_data)

        if not parsed_data:
            logger.error("Не удалось распарсить ответ ИИ")
            return cls(
                status='error',
                analysis_summary="Ошибка парсинга ответа ИИ",
                findings=[],
                suggested_actions=[],
                questions_for_user=[]
            )

        # Проверяем обязательные поля для анализа
        required_fields = ['status', 'analysis_summary', 'findings']
        if not AIResponseParser.validate_response_structure(parsed_data, required_fields):
            logger.error(f"Отсутствуют обязательные поля: {required_fields}")
            return cls(
                status='error',
                analysis_summary="Некорректная структура ответа ИИ",
                findings=[],
                suggested_actions=[],
                questions_for_user=[]
            )

        # Добавляем значения по умолчанию для необязательных полей
        parsed_data.setdefault('suggested_actions', [])
        parsed_data.setdefault('questions_for_user', [])

        try:
            return cls(**parsed_data)
        except Exception as e:
            logger.error(f"Ошибка создания объекта AnalysisAIResponse: {e}")
            return cls(
                status='error',
                analysis_summary=f"Ошибка создания объекта: {str(e)}",
                findings=[],
                suggested_actions=[],
                questions_for_user=[]
            )

class AnalysisAgent:
    """
    Главный оркестратор интерактивного анализа кода с ИИ
    Координирует AnalysisSessionManager, AnalysisActionExecutor и ИИ вызовы
    """

    def __init__(self):
        self.session_manager = AnalysisSessionManager()
        self.action_executor = AnalysisActionExecutor()
        self.logger = logger

        # Загружаем переменные окружения для ИИ
        try:
            from .ai_utils import load_env_file
            env_loaded = load_env_file()
            if env_loaded:
                logger.debug("🔧 AnalysisAgent: .env файл загружен")
        except Exception as e:
            logger.warning(f"⚠️ AnalysisAgent: Ошибка загрузки .env: {e}")

        # Инициализируем ИИ модуль для реальных вызовов
        self._ai_module_available = False
        self._generate_ai_review_func = None
        try:
            from .ai_utils import generate_ai_review_async
            self._generate_ai_review_func = generate_ai_review_async
            self._ai_module_available = True
            logger.info("✅ AnalysisAgent: ИИ модуль инициализирован")
        except ImportError as e:
            logger.warning(f"⚠️ AnalysisAgent: ИИ модуль недоступен - {e}")
            self._generate_ai_review_func = None

        # Инициализируем context_generator для анализа проекта
        self.context_generator = None
        try:
            from .context_generator import ContextGenerator
            self.context_generator = ContextGenerator()
            logger.info("✅ AnalysisAgent: Генератор контекста инициализирован")
        except Exception as e:
            logger.error(f"❌ AnalysisAgent: Ошибка инициализации генератора контекста: {e}")

    async def analyze_code(
        self,
        path: str = ".",
        template_name: str = "code-review",
        ai_model: str = "gemini-2.5-pro-preview-06-05",
        user_query: str | None = None,
        session_id: str = "",
        **params
    ) -> str:
        """
        Основная точка входа для анализа кода

        Args:
            path: Путь к проекту
            template_name: Шаблон анализа
            ai_model: Модель ИИ для использования
            user_query: Пользовательский запрос для фокуса
            session_id: ID существующей сессии (если пустой - создается новая)
            **params: Дополнительные параметры

        Returns:
            str: Отчет о выполнении анализа
        """
        project_path = Path(path).resolve()

        self.logger.info(f"🤖 Запуск интерактивного анализа кода для: {project_path}")

        # Определяем нужно ли создавать новую сессию или продолжать существующую
        if session_id and session_id.strip():
            # Если передан session_id - пытаемся загрузить эту конкретную сессию
            session_state = self.session_manager.load_session(project_path)
            if session_state and session_state.session_id == session_id.strip():
                self.logger.info(f"📋 Продолжаем сессию: {session_id}")
                return await self._continue_analysis_session(
                    project_path, session_state, user_query, ai_model
                )
            else:
                self.logger.warning(f"⚠️ Сессия {session_id} не найдена, создаем новую")
                return await self._start_new_analysis_session(
                    project_path, template_name, ai_model, user_query, params
                )
        else:
            # Если session_id пустой - создаем новую сессию
            self.logger.info("🆕 Создаем новую сессию (session_id не указан)")
            return await self._start_new_analysis_session(
                project_path, template_name, ai_model, user_query, params
            )

    async def _start_new_analysis_session(
        self,
        project_path: Path,
        template_name: str,
        ai_model: str,
        user_query: str | None,
        params: dict
    ) -> str:
        """Начинает новую сессию анализа кода"""

        self.logger.info("Создание новой сессии анализа кода")

        # Создаем новую сессию
        session_state = self.session_manager.create_new_session(
            project_path, params, ai_model, template_name, user_query
        )

        # Сохраняем начальное состояние
        self.session_manager.save_session(project_path, session_state)

        # Выполняем первичный анализ
        try:
            ai_response = await self._get_initial_code_analysis(
                project_path, template_name, params, ai_model, user_query
            )

            # Обновляем сессию с полученным анализом
            session_state.status = 'interactive'
            self.session_manager.add_analysis_interaction(
                session_state,
                user_query or f"Начальный анализ с шаблоном {template_name}",
                ai_response.analysis_summary,
                ai_response.next_focus
            )
            self.session_manager.save_session(project_path, session_state)

            # Генерируем отчет о начале
            report = self._generate_start_analysis_report(project_path, session_state, ai_response, True)

        except Exception as e:
            # Обновляем статус на ошибку
            session_state.status = 'error'
            self.session_manager.save_session(project_path, session_state)

            self.logger.error(f"Ошибка начального анализа: {e}")
            report = self._generate_error_analysis_report(project_path, session_state, str(e))

        return report

    async def _continue_analysis_session(
        self,
        project_path: Path,
        session_state: AnalysisSessionState,
        user_query: str | None,
        ai_model: str
    ) -> str:
        """Продолжает существующую сессию анализа"""

        self.logger.info(f"Продолжение сессии анализа: {session_state.session_id}")

        if not user_query:
            # Если нет нового запроса, показываем информацию о сессии
            return self._generate_session_info_report(project_path, session_state)

        try:
            # Получаем продолжение анализа от ИИ
            ai_response = await self._get_follow_up_analysis(
                project_path, session_state, user_query, ai_model
            )

            # Обновляем сессию
            self.session_manager.add_analysis_interaction(
                session_state,
                user_query,
                ai_response.analysis_summary,
                ai_response.next_focus
            )
            self.session_manager.save_session(project_path, session_state)

            # Генерируем отчет о продолжении
            report = self._generate_continue_analysis_report(
                project_path, session_state, ai_response, user_query
            )

        except Exception as e:
            self.logger.error(f"Ошибка продолжения анализа: {e}")
            report = self._generate_error_analysis_report(project_path, session_state, str(e))

        return report

    async def _get_initial_code_analysis(
        self,
        project_path: Path,
        template_name: str,
        params: dict,
        ai_model: str,
        user_query: str | None
    ) -> AnalysisAIResponse:
        """Получает первичный анализ кода от ИИ"""

        # Генерируем контекст проекта
        project_context = await self._generate_project_context(project_path, params)

        # Создаем промпт для анализа
        analysis_prompt = self._create_analysis_prompt(
            project_path, project_context, template_name, user_query
        )

        if self._ai_module_available and self._generate_ai_review_func:
            # Реальный асинхронный вызов ИИ
            try:
                ai_response_text = await self._generate_ai_review_func(analysis_prompt, ai_model)
                return AnalysisAIResponse.from_json(ai_response_text)
            except Exception as e:
                logger.error(f"Ошибка вызова ИИ для анализа: {e}")
                return self._get_demo_analysis_response()
        else:
            # Демо режим
            return self._get_demo_analysis_response()

    async def _get_follow_up_analysis(
        self,
        project_path: Path,
        session_state: AnalysisSessionState,
        user_query: str,
        ai_model: str
    ) -> AnalysisAIResponse:
        """Получает продолжение анализа от ИИ"""

        # Создаем промпт для продолжения с контекстом сессии
        follow_up_prompt = self._create_follow_up_prompt(
            project_path, session_state, user_query
        )

        if self._ai_module_available and self._generate_ai_review_func:
            try:
                ai_response_text = await self._generate_ai_review_func(follow_up_prompt, ai_model)
                return AnalysisAIResponse.from_json(ai_response_text)
            except Exception as e:
                logger.error(f"Ошибка вызова ИИ для продолжения анализа: {e}")
                return self._get_demo_follow_up_response(user_query)
        else:
            return self._get_demo_follow_up_response(user_query)

    async def _generate_project_context(self, project_path: Path, params: dict) -> str:
        """Генерирует контекст проекта для анализа"""

        if not self.context_generator:
            return f"Проект: {project_path}\nВнимание: Генератор контекста недоступен"

        try:
            # Используем ContextGenerator для получения кода
            context_args = {
                "path": str(project_path),
                "template_name": params.get("template_name", "code-review"),
                "include_patterns": params.get("include_patterns", []),
                "exclude_patterns": params.get("exclude_patterns", []),
                "line_numbers": True,
                "code_blocks": True,
                "encoding": "cl100k"
            }

            context_results = await self.context_generator.get_context(context_args)
            project_context = context_results[0].text if context_results else "Контекст недоступен"

            return project_context

        except Exception as e:
            self.logger.error(f"Ошибка генерации контекста проекта: {e}")
            return f"Проект: {project_path}\nОшибка генерации контекста: {str(e)}"

    def _create_analysis_prompt(
        self,
        project_path: Path,
        project_context: str,
        template_name: str,
        user_query: str | None
    ) -> str:
        """Создает промпт для первичного анализа кода"""

        base_prompt = f"""# Анализ кода проекта с JSON контрактом

Проведи детальный анализ предоставленного кода и верни результат в виде JSON объекта.

## Контекст анализа:
- **Проект:** {project_path}
- **Шаблон анализа:** {template_name}
- **Пользовательский запрос:** {user_query or "Общий анализ кода"}

## Код для анализа:
{project_context}

## Требуемый формат ответа (JSON):
```json
{{
  "status": "analyzing|suggesting_fixes|ready_to_execute|completed",
  "analysis_summary": "Краткая сводка анализа",
  "findings": [
    {{
      "type": "issue|improvement|security|performance",
      "severity": "high|medium|low",
      "title": "Краткое описание",
      "description": "Подробное описание",
      "file": "путь/к/файлу",
      "line": 123,
      "suggestion": "Рекомендация по исправлению"
    }}
  ],
  "suggested_actions": [
    {{
      "action": "create_file|update_file|refactor_function|add_comment|fix_issue",
      "description": "Описание действия",
      "path": "путь/к/файлу",
      "content": "новое содержимое (если применимо)"
    }}
  ],
  "next_focus": "Что анализировать дальше",
  "questions_for_user": ["Вопрос 1", "Вопрос 2"]
}}
```

Верни ТОЛЬКО JSON, без дополнительного текста."""

        return base_prompt

    def _create_follow_up_prompt(
        self,
        project_path: Path,
        session_state: AnalysisSessionState,
        user_query: str
    ) -> str:
        """Создает промпт для продолжения анализа"""

        # Собираем историю взаимодействий
        history = ""
        for interaction in session_state.analysis_history[-3:]:  # Последние 3 взаимодействия
            history += f"\n- Шаг {interaction['step']}: {interaction['user_request']}"

        follow_up_prompt = f"""# Продолжение анализа кода (Сессия: {session_state.session_id})

## Контекст сессии:
- **Проект:** {project_path}
- **Текущий фокус:** {session_state.current_focus}
- **Шаблон:** {session_state.template_name}

## История анализа:{history}

## Новый запрос пользователя:
{user_query}

Проанализируй новый запрос в контексте предыдущих взаимодействий и верни результат в том же JSON формате:

```json
{{
  "status": "analyzing|suggesting_fixes|ready_to_execute|completed",
  "analysis_summary": "Анализ нового запроса",
  "findings": [...],
  "suggested_actions": [...],
  "next_focus": "Новый фокус",
  "questions_for_user": [...]
}}
```

Верни ТОЛЬКО JSON, без дополнительного текста."""

        return follow_up_prompt

    def _get_demo_analysis_response(self) -> AnalysisAIResponse:
        """Демо ответ для тестирования"""
        return AnalysisAIResponse(
            status='suggesting_fixes',
            analysis_summary="Демо анализ: обнаружено несколько областей для улучшения",
            findings=[
                {
                    "type": "improvement",
                    "severity": "medium",
                    "title": "Длинные функции",
                    "description": "Найдены функции длиннее 50 строк",
                    "file": "src/example.py",
                    "line": 25,
                    "suggestion": "Разбить на меньшие функции"
                }
            ],
            suggested_actions=[
                {
                    "action": "add_comment",
                    "description": "Добавить комментарий к сложной функции",
                    "path": "src/example.py",
                    "line_number": 25,
                    "comment": "TODO: Рефакторинг - разбить функцию"
                }
            ],
            next_focus="Анализ производительности",
            questions_for_user=["Хотите ли вы сосредоточиться на производительности?"]
        )

    def _get_demo_follow_up_response(self, user_query: str) -> AnalysisAIResponse:
        """Демо ответ для продолжения"""
        return AnalysisAIResponse(
            status='completed',
            analysis_summary=f"Демо анализ запроса: {user_query}",
            findings=[],
            suggested_actions=[],
            next_focus="Анализ завершен",
            questions_for_user=[]
        )

    def _generate_start_analysis_report(
        self,
        project_path: Path,
        session_state: AnalysisSessionState,
        ai_response: AnalysisAIResponse,
        is_force_new: bool = False
    ) -> str:
        """Генерирует отчет о начале анализа с информацией о создании сессии"""

        report = f"""# 🤖 Автоматический анализ кода

**🆕 Новая сессия создана**
**🆔 Сессия:** `{session_state.session_id}`
**💬 Ваш запрос:** {session_state.user_query or "Общий анализ кода"}
**🎯 Шаблон:** {session_state.template_name}
**🧠 Модель ИИ:** {session_state.ai_model}
**📍 Проект:** {project_path.name}

---

## 📊 Результаты анализа

**📈 Статус:** {ai_response.status}

### 🔍 Ключевые находки

{ai_response.analysis_summary}

### 📋 Детальные результаты
"""

        # Добавляем детальные находки
        if ai_response.findings:
            for i, finding in enumerate(ai_response.findings, 1):
                severity = finding.get('severity', 'info')
                category = finding.get('category', 'general')
                description = finding.get('description', 'Не указано')

                severity_emoji = {
                    'critical': '🚨',
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢',
                    'info': 'ℹ️'
                }.get(severity, 'ℹ️')

                report += f"""
#### {severity_emoji} Находка {i}: {category.title()}
- **Серьезность:** {severity}
- **Описание:** {description}
"""

                if 'file_path' in finding:
                    report += f"- **Файл:** `{finding['file_path']}`\n"
                if 'line_range' in finding:
                    report += f"- **Строки:** {finding['line_range']}\n"

        # Добавляем предлагаемые действия
        if ai_response.suggested_actions:
            report += f"\n\n### 🛠️ Предлагаемые действия ({len(ai_response.suggested_actions)})\n\n"
            for i, action in enumerate(ai_response.suggested_actions, 1):
                action_type = action.get('type', 'unknown')
                description = action.get('description', 'Не указано')
                report += f"{i}. **{action_type.title()}:** {description}\n"

        # Добавляем вопросы к пользователю если есть
        if ai_response.questions_for_user:
            report += "\n\n### ❓ Вопросы для уточнения\n\n"
            for i, question in enumerate(ai_response.questions_for_user, 1):
                report += f"{i}. {question}\n"

        # Добавляем информацию о следующих шагах
        if ai_response.next_focus:
            report += f"\n\n### 🎯 Следующий фокус анализа\n\n{ai_response.next_focus}\n"

        report += f"""

---

## 🚀 Как продолжить

Для продолжения диалога используйте `get_analyze` с `session_id`:

```json
{{
  "path": "{project_path}",
  "session_id": "{session_state.session_id}",
  "user_query": "Ваш следующий вопрос или запрос"
}}
```

Для создания новой сессии НЕ указывайте `session_id`:

```json
{{
  "path": "{project_path}",
  "user_query": "Новый анализ"
}}
```

*Анализ выполнен с помощью продвинутой архитектуры ИИ через AnalysisAgent*
"""
        return report

    def _generate_continue_analysis_report(
        self,
        project_path: Path,
        session_state: AnalysisSessionState,
        ai_response: AnalysisAIResponse,
        user_query: str
    ) -> str:
        """Генерирует отчет о продолжении анализа"""

        report = f"""# 🔄 Продолжение анализа (Шаг {session_state.step})

**🆔 Сессия:** `{session_state.session_id}`
**💬 Ваш запрос:** {user_query}

## 📊 Ответ ИИ

{ai_response.analysis_summary}

"""

        if ai_response.findings:
            report += f"### 🔍 Новые находки: {len(ai_response.findings)}\n\n"
            for i, finding in enumerate(ai_response.findings, 1):
                severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(finding.get("severity", "low"), "⚪")
                report += f"{i}. {severity_emoji} **{finding.get('title')}**\n"
                report += f"   - 💡 {finding.get('suggestion', 'Нет рекомендаций')}\n\n"

        if ai_response.suggested_actions:
            report += "### 🛠️ Рекомендуемые действия:\n\n"
            for i, action in enumerate(ai_response.suggested_actions, 1):
                report += f"{i}. **{action.get('action')}** - {action.get('description')}\n"

        if ai_response.next_focus:
            report += f"\n### 🎯 Следующий фокус: {ai_response.next_focus}\n"

        if ai_response.questions_for_user:
            report += "\n### ❓ Вопросы для уточнения:\n\n"
            for question in ai_response.questions_for_user:
                report += f"- {question}\n"

        report += f"\n**🔄 Всего взаимодействий в сессии:** {len(session_state.analysis_history)}"

        return report

    def _generate_session_info_report(
        self,
        project_path: Path,
        session_state: AnalysisSessionState
    ) -> str:
        """Генерирует отчет о состоянии сессии"""

        report = f"""# 📋 Информация о сессии анализа

**🆔 Сессия:** `{session_state.session_id}`
**📁 Проект:** `{project_path}`
**🎯 Шаблон:** `{session_state.template_name}`
**📊 Статус:** `{session_state.status}`
**🎯 Текущий фокус:** {session_state.current_focus or "Не установлен"}

## 📚 История взаимодействий: {len(session_state.analysis_history)}

"""

        for interaction in session_state.analysis_history[-5:]:  # Последние 5
            report += f"**Шаг {interaction['step']}** ({interaction['timestamp'][:16]})\n"
            report += f"- 💬 Запрос: {interaction['user_request']}\n"
            report += f"- 🎯 Фокус: {interaction['focus']}\n\n"

        report += """
## 🚀 Продолжить анализ

Задайте новый вопрос или запрос для продолжения анализа:
- "Проанализируй файл X подробнее"
- "Покажи проблемы с производительностью"
- "Сосредоточься на безопасности"
"""

        return report

    def _generate_error_analysis_report(
        self,
        project_path: Path,
        session_state: AnalysisSessionState,
        error_message: str
    ) -> str:
        """Генерирует отчет об ошибке"""

        return f"""# ❌ Ошибка анализа кода

**🆔 Сессия:** `{session_state.session_id}`
**📁 Проект:** `{project_path}`

## Описание ошибки

{error_message}

Попробуйте перезапустить анализ или обратитесь к администратору.
"""
