"""
DocsAgent - умный оркестратор генерации документации с ИИ

Отвечает за:
- Координацию процесса генерации документации
- JSON контракт с ИИ
- Интеграцию с DocsSessionManager и ActionExecutor
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .action_executor import ActionExecutor, ExecutionSummary
from .docs_session_manager import DocsSessionManager, SessionState
from .response_parser import AIResponseParser

logger = logging.getLogger(__name__)

@dataclass
class AIResponse:
    """Структурированный ответ от ИИ"""
    status: str  # 'in_progress', 'completed', 'error'
    next_steps: list[dict[str, Any]]  # JSON действия
    summary: str
    analysis: str | None = None

    @classmethod
    def from_json(cls, json_data: str) -> 'AIResponse':
        """Создает объект из JSON строки используя централизованный парсер"""
        parsed_data = AIResponseParser.from_json(json_data)

        if not parsed_data:
            logger.error("Не удалось распарсить ответ ИИ")
            return cls(
                status='error',
                next_steps=[],
                summary="Ошибка парсинга ответа ИИ",
                analysis="Нет данных для обработки"
            )

        # ИСПРАВЛЕНО: Проверяем что parsed_data является словарем
        if not isinstance(parsed_data, dict):
            logger.error(f"Ожидался словарь, получен {type(parsed_data)}: {parsed_data}")
            return cls(
                status='error',
                next_steps=[],
                summary="Некорректный тип данных ответа ИИ",
                analysis=f"Получен {type(parsed_data)} вместо словаря"
            )

        # Проверяем обязательные поля для документации
        required_fields = ['status', 'summary', 'next_steps']
        if not AIResponseParser.validate_response_structure(parsed_data, required_fields):
            logger.error(f"Отсутствуют обязательные поля: {required_fields}")
            return cls(
                status='error',
                next_steps=[],
                summary="Некорректная структура ответа ИИ",
                analysis="Отсутствуют обязательные поля"
            )

        try:
            return cls(**parsed_data)
        except Exception as e:
            logger.error(f"Ошибка создания объекта AIResponse: {e}")
            return cls(
                status='error',
                next_steps=[],
                summary=f"Ошибка создания объекта: {str(e)}",
                analysis=str(parsed_data) if parsed_data else "Нет данных"
            )

class DocsAgent:
    """
    Главный оркестратор генерации документации с ИИ
    Координирует DocsSessionManager, ActionExecutor и ИИ вызовы
    """

    def __init__(self):
        self.session_manager = DocsSessionManager()
        self.action_executor = ActionExecutor()
        self.logger = logger

        # Загружаем переменные окружения для ИИ
        try:
            from .ai_utils import load_env_file
            env_loaded = load_env_file()
            if env_loaded:
                logger.debug("🔧 DocsAgent: .env файл загружен")
        except Exception as e:
            logger.warning(f"⚠️ DocsAgent: Ошибка загрузки .env: {e}")

        # Инициализируем ИИ модуль для реальных вызовов
        self._ai_module_available = False
        self._generate_ai_review_func = None
        try:
            from .ai_utils import generate_ai_review_async
            self._generate_ai_review_func = generate_ai_review_async
            self._ai_module_available = True
            logger.info("✅ DocsAgent: ИИ модуль инициализирован")
        except ImportError as e:
            logger.warning(f"⚠️ DocsAgent: ИИ модуль недоступен - {e}")
            self._generate_ai_review_func = None

        # Инициализируем context_generator для анализа проекта
        self.context_generator = None
        try:
            from .context_generator import ContextGenerator
            self.context_generator = ContextGenerator()
            logger.info("✅ DocsAgent: Генератор контекста инициализирован")
        except Exception as e:
            logger.error(f"❌ DocsAgent: Ошибка инициализации генератора контекста: {e}")

    async def generate_docs(
        self,
        path: str = ".",
        ai_model: str = "gemini-2.5-pro-preview-06-05",
        **params
    ) -> str:
        """
        Основная точка входа для генерации документации

        Args:
            path: Путь к проекту
            ai_model: Модель ИИ для использования
            **params: Дополнительные параметры

        Returns:
            str: Отчет о выполнении
        """
        project_path = Path(path).resolve()

        self.logger.info(f"🤖 Запуск генерации документации для: {project_path}")

        # Загружаем или создаем сессию
        session_state = self.session_manager.load_session(project_path)

        if session_state is None:
            return await self._start_new_session(project_path, ai_model, params)
        else:
            return await self._continue_session(project_path, session_state, ai_model, params)

    async def _start_new_session(
        self,
        project_path: Path,
        ai_model: str,
        params: dict
    ) -> str:
        """Начинает новую сессию документации"""

        self.logger.info("Создание новой сессии документации")

        # Создаем новую сессию
        session_state = self.session_manager.create_new_session(
            project_path, params, ai_model
        )

        # Сохраняем начальное состояние
        self.session_manager.save_session(project_path, session_state)

        # Анализируем проект и получаем первые инструкции
        try:
            ai_response = await self._get_initial_analysis(project_path, params, ai_model)

            # Обновляем сессию с полученными инструкциями
            session_state.status = 'executing'
            self.session_manager.save_session(project_path, session_state)

            # Генерируем отчет о начале
            report = self._generate_start_report(project_path, session_state, ai_response)

        except Exception as e:
            # Обновляем статус на ошибку
            session_state.status = 'error'
            self.session_manager.save_session(project_path, session_state)

            self.logger.error(f"Ошибка начального анализа: {e}")
            report = self._generate_error_report(project_path, session_state, str(e))

        return report

    async def _continue_session(
        self,
        project_path: Path,
        session_state: SessionState,
        ai_model: str,
        params: dict
    ) -> str:
        """Продолжает существующую сессию"""

        self.logger.info(f"Продолжение сессии: {session_state.session_id}")

        try:
            if session_state.status == 'analyzing':
                # Получаем первые инструкции
                ai_response = await self._get_initial_analysis(project_path, params, ai_model)
            else:
                # Получаем следующие инструкции
                ai_response = await self._get_next_instructions(project_path, session_state, ai_model)

            # Выполняем полученные действия
            if ai_response.next_steps:
                execution_summary = self.action_executor.execute_actions(
                    project_path,
                    ai_response.next_steps
                )
            else:
                execution_summary = None

            # Обновляем сессию
            completed_step = {
                'step': session_state.step,
                'ai_response': ai_response.summary,
                'actions_executed': len(ai_response.next_steps) if ai_response.next_steps else 0,
                'success_rate': execution_summary.success_rate if execution_summary else 100.0
            }

            if ai_response.status == 'completed':
                session_state.status = 'completed'

            session_state = self.session_manager.update_session_step(
                session_state,
                session_state.status,
                completed_step
            )

            self.session_manager.save_session(project_path, session_state)

            # Генерируем отчет
            report = self._generate_continue_report(
                project_path,
                session_state,
                ai_response,
                execution_summary
            )

            # Очищаем сессию если завершена
            if session_state.status == 'completed':
                self.session_manager.cleanup_session(project_path)

        except Exception as e:
            # Обновляем статус на ошибку
            session_state.status = 'error'
            self.session_manager.save_session(project_path, session_state)

            self.logger.error(f"Ошибка продолжения сессии: {e}")
            report = self._generate_error_report(project_path, session_state, str(e))

        return report

    async def _get_initial_analysis(
        self,
        project_path: Path,
        params: dict,
        ai_model: str
    ) -> AIResponse:
        """
        Получает начальный анализ проекта от ИИ

        РЕАЛЬНАЯ ИНТЕГРАЦИЯ: Использует context_generator + ai_utils
        """

        self.logger.info("🧠 Запрос начального анализа от ИИ")

        if not self._ai_module_available:
            # Fallback демо-режим если ИИ недоступен
            return await self._get_demo_initial_analysis(project_path)

        try:
            # 1. Анализируем проект с помощью context_generator
            project_context = await self._generate_project_context(project_path, params)

            # 2. Создаем промпт для ИИ анализа
            ai_prompt = self._create_analysis_prompt(project_path, project_context, params)

            # 3. Получаем ответ от ИИ
            self.logger.info(f"🤖 Отправляем запрос к {ai_model}")
            self.logger.debug(f"Промпт для ИИ (первые 300 символов): {ai_prompt[:300]}...")

            ai_response_text = await self._generate_ai_review_func(ai_prompt, ai_model)

            # Логируем ответ для диагностики
            self.logger.info(f"📥 Получен ответ от ИИ длиной: {len(ai_response_text) if ai_response_text else 0} символов")
            if ai_response_text:
                self.logger.debug(f"Ответ ИИ (первые 200 символов): {ai_response_text[:200]}")
            else:
                self.logger.error("❌ ИИ вернул пустой ответ!")

            # 4. Парсим JSON ответ
            ai_response = AIResponse.from_json(ai_response_text)

            self.logger.info(f"✅ Получен ответ от ИИ: {ai_response.status}")
            return ai_response

        except Exception as e:
            self.logger.error(f"❌ Ошибка анализа ИИ: {e}")
            # Возвращаем fallback ответ
            return AIResponse(
                status='error',
                next_steps=[],
                summary=f"Ошибка ИИ анализа: {str(e)}",
                analysis="Переключаемся на демо режим из-за ошибки ИИ"
            )

    async def _get_next_instructions(
        self,
        project_path: Path,
        session_state: SessionState,
        ai_model: str
    ) -> AIResponse:
        """
        Получает следующие инструкции от ИИ на основе текущего прогресса

        РЕАЛЬНАЯ ИНТЕГРАЦИЯ: Анализирует прогресс и запрашивает следующие шаги
        """

        self.logger.info("🔄 Запрос следующих инструкций от ИИ")

        if not self._ai_module_available:
            # Fallback демо-режим
            return await self._get_demo_next_instructions(session_state)

        try:
            # 1. Создаем промпт для проверки прогресса
            progress_prompt = self._create_progress_prompt(project_path, session_state)

            # 2. Получаем ответ от ИИ
            self.logger.info(f"🤖 Проверяем прогресс с {ai_model}")
            self.logger.debug(f"Промпт прогресса (первые 200 символов): {progress_prompt[:200]}...")

            ai_response_text = await self._generate_ai_review_func(progress_prompt, ai_model)

            # Логируем ответ для диагностики
            self.logger.info(f"📥 Получен ответ прогресса длиной: {len(ai_response_text) if ai_response_text else 0} символов")
            if ai_response_text:
                self.logger.debug(f"Ответ ИИ прогресса (первые 200 символов): {ai_response_text[:200]}")
            else:
                self.logger.error("❌ ИИ вернул пустой ответ для прогресса!")

            # 3. Парсим JSON ответ
            ai_response = AIResponse.from_json(ai_response_text)

            self.logger.info(f"✅ Получен прогресс от ИИ: {ai_response.status}")
            return ai_response

        except Exception as e:
            self.logger.error(f"❌ Ошибка запроса прогресса: {e}")
            return AIResponse(
                status='error',
                next_steps=[],
                summary=f"Ошибка проверки прогресса: {str(e)}"
            )

    async def _generate_project_context(self, project_path: Path, params: dict) -> str:
        """
        Генерирует контекст проекта для анализа ИИ

        Использует context_generator для сбора информации о проекте
        """

        if not self.context_generator:
            return f"Проект в {project_path} (детальный анализ недоступен)"

        try:
            # Используем documentation шаблон для анализа структуры проекта
            context_args = {
                "path": str(project_path),
                "template_name": "documentation",
                "include_patterns": ["*.py", "*.md", "*.txt", "*.yml", "*.yaml", "*.toml", "*.cfg"],
                "exclude_patterns": [
                    "__pycache__/**", "*.pyc", ".git/**",
                    "node_modules/**", ".venv/**", "venv/**",
                    "*.log", "*.tmp", ".docs_session/**"
                ],
                "line_numbers": False,  # Для анализа структуры номера строк не нужны
                "code_blocks": True,
                "follow_symlinks": False
            }

            context_results = await self.context_generator.get_context(context_args)
            context_text = context_results[0].text if context_results else ""

            # Ограничиваем размер контекста для ИИ (макс 50k символов)
            if len(context_text) > 50000:
                context_text = context_text[:50000] + "\n\n... (контекст обрезан для анализа)"

            return context_text

        except Exception as e:
            self.logger.error(f"Ошибка генерации контекста: {e}")
            return f"Проект в {project_path} (ошибка анализа: {str(e)})"

    def _create_analysis_prompt(self, project_path: Path, project_context: str, params: dict) -> str:
        """
        Создает промпт для начального анализа проекта

        РЕАЛЬНАЯ РЕАЛИЗАЦИЯ: Анализирует структуру проекта и создает план документации
        """

        docs_structure = params.get('docs_structure', 'standard')
        target_guide_length = params.get('target_guide_length', 150)

        return f"""Ты - эксперт по созданию технической документации. Проанализируй проект и создай план генерации документации.

# ПРОЕКТ ДЛЯ АНАЛИЗА:
{project_context}

# ПАРАМЕТРЫ ГЕНЕРАЦИИ:
- Структура документации: {docs_structure}
- Целевая длина руководств: {target_guide_length} строк
- Путь проекта: {project_path}

# ЗАДАЧА:
1. Проанализируй структуру проекта, его назначение и технологии
2. Определи какая документация нужна (README, API docs, guides и т.д.)
3. Создай план первых 2-3 файлов документации
4. Включи практические примеры использования

# ВАЖНО: ИСПОЛЬЗУЙ ТОЛЬКО ЭТИ ТИПЫ ДЕЙСТВИЙ:
- "create_file" - создать файл с содержимым
- "create_directory" - создать папку
- "update_file" - обновить существующий файл

# ВЕРНИ ОТВЕТ СТРОГО В JSON ФОРМАТЕ:
{{
    "status": "in_progress",
    "summary": "Краткое описание плана документации",
    "analysis": "Детальный анализ проекта и его потребностей в документации",
    "next_steps": [
        {{
            "action": "create_directory",
            "path": "docs"
        }},
        {{
            "action": "create_file",
            "path": "docs/README.md",
            "content": "# Название проекта\\n\\n## Обзор\\nОписание проекта...\\n\\n## Установка\\n```bash\\n# команды установки\\n```"
        }}
    ]
}}

# СТРОГИЕ ТРЕБОВАНИЯ:
- ТОЛЬКО JSON формат ответа
- ТОЛЬКО действия: create_file, create_directory, update_file
- НИКАКИХ других типов действий
- НЕ создавай более 3 файлов за раз
- Markdown разметка в content
- Практичные примеры использования

Начни анализ и верни план в JSON формате."""

    def _create_progress_prompt(self, project_path: Path, session_state: SessionState) -> str:
        """
        Создает промпт для проверки прогресса

        РЕАЛЬНАЯ РЕАЛИЗАЦИЯ: Анализирует текущее состояние документации
        """

        completed_steps = session_state.completed_steps

        # Проверяем что существует в папке docs
        docs_path = project_path / "docs"
        existing_files = []
        if docs_path.exists():
            for file_path in docs_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(project_path)
                    existing_files.append(str(relative_path))

        return f"""Проверь прогресс генерации документации для проекта.

# ПРОЕКТ: {project_path}
# ВЫПОЛНЕНО ШАГОВ: {len(completed_steps)}

# ВЫПОЛНЕННЫЕ ШАГИ:
{json.dumps(completed_steps, indent=2, ensure_ascii=False)}

# СУЩЕСТВУЮЩИЕ ФАЙЛЫ ДОКУМЕНТАЦИИ:
{json.dumps(existing_files, indent=2, ensure_ascii=False)}

# ЗАДАЧА:
1. Проанализируй что уже создано
2. Определи полноту документации
3. Если документация достаточна - верни status: "completed"
4. Если нужны дополнения - дай следующие 2-3 действия

# КРИТЕРИИ ЗАВЕРШЕНИЯ:
- Есть основной README.md с описанием проекта
- Есть инструкции по установке и использованию
- Есть примеры кода (если это библиотека/фреймворк)
- Документация логично структурирована

# ВАЖНО: ИСПОЛЬЗУЙ ТОЛЬКО ЭТИ ТИПЫ ДЕЙСТВИЙ:
- "create_file" - создать файл с содержимым
- "create_directory" - создать папку
- "update_file" - обновить существующий файл

# ВЕРНИ ОТВЕТ В JSON ФОРМАТЕ:
{{
    "status": "in_progress" или "completed",
    "summary": "Описание текущего состояния и следующих шагов",
    "next_steps": [
        {{
            "action": "create_file",
            "path": "путь/к/файлу.md",
            "content": "содержимое файла"
        }}
    ]
}}

СТРОГО: НИКАКИХ других типов действий кроме create_file, create_directory, update_file!
Оцени прогресс и верни план в JSON формате."""

    async def _get_demo_initial_analysis(self, project_path: Path) -> AIResponse:
        """Демо-версия начального анализа для случая недоступности ИИ"""

        self.logger.info("⚠️ Используется демо режим начального анализа")

        demo_response = {
            "status": "in_progress",
            "summary": "Проанализирован проект. Создаю базовую структуру документации.",
            "analysis": f"Проект в {project_path} содержит Python код. Необходима документация.",
            "next_steps": [
                {
                    "action": "create_directory",
                    "path": "docs"
                },
                {
                    "action": "create_file",
                    "path": "docs/README.md",
                    "content": "# Документация neira-code-analyzer\n\n## Обзор\nMCP сервер для продвинутого анализа кодовых баз.\n\n## Быстрый старт\n1. Установите зависимости: `uv sync`\n2. Запустите сервер: `uv run python -m src.neira_code_analyzer.main`"
                }
            ]
        }

        return AIResponse(**demo_response)

    async def _get_demo_next_instructions(self, session_state: SessionState) -> AIResponse:
        """Демо-версия следующих инструкций"""

        self.logger.info("⚠️ Используется демо режим следующих инструкций")

        completed_steps = len(session_state.completed_steps)

        if completed_steps < 2:
            # Еще один шаг
            demo_response = {
                "status": "in_progress",
                "summary": f"Шаг {completed_steps + 2}: Создание дополнительной документации",
                "next_steps": [
                    {
                        "action": "create_file",
                        "path": "docs/QUICKSTART.md",
                        "content": "# Быстрый старт\n\n## Установка\n```bash\nuv sync\n```\n\n## Запуск\n```bash\nuv run python -m src.neira_code_analyzer.main\n```"
                    }
                ]
            }
        else:
            # Завершение
            demo_response = {
                "status": "completed",
                "summary": "Генерация документации завершена успешно!",
                "next_steps": []
            }

        return AIResponse(**demo_response)

    def _generate_start_report(
        self,
        project_path: Path,
        session_state: SessionState,
        ai_response: AIResponse
    ) -> str:
        """Генерирует отчет о начале сессии"""

        report_lines = [
            "🤖 ПОШАГОВАЯ ГЕНЕРАЦИЯ ДОКУМЕНТАЦИИ",
            "=" * 40,
            f"📁 Проект: {project_path}",
            f"🎯 Сессия: {session_state.session_id}",
            f"📋 Шаг: {session_state.step}/? - НАЧАЛЬНЫЙ АНАЛИЗ",
            "",
            "🧠 АНАЛИЗ ЗАВЕРШЕН - JSON ИНСТРУКЦИИ ПОЛУЧЕНЫ",
            "-" * 40,
            "",
            f"📊 **Статус:** {ai_response.status}",
            f"📝 **Анализ:** {ai_response.summary}",
            f"🔧 **Действий запланировано:** {len(ai_response.next_steps)}",
            "",
            "🔄 Для выполнения инструкций запустите gen_docs еще раз",
            "",
        ]

        if ai_response.analysis:
            report_lines.extend([
                "📋 **Детальный анализ:**",
                ai_response.analysis,
                ""
            ])

        return "\n".join(report_lines)

    def _generate_continue_report(
        self,
        project_path: Path,
        session_state: SessionState,
        ai_response: AIResponse,
        execution_summary: ExecutionSummary | None
    ) -> str:
        """Генерирует отчет о продолжении сессии"""

        report_lines = [
            "🔄 ПРОДОЛЖЕНИЕ СЕССИИ ДОКУМЕНТАЦИИ",
            "=" * 40,
            f"📁 Проект: {project_path}",
            f"🎯 Сессия: {session_state.session_id}",
            f"📋 Шаг: {session_state.step}/? - ВЫПОЛНЕНИЕ",
            "",
        ]

        if execution_summary:
            report_lines.extend([
                "✅ ВЫПОЛНЕНИЕ ЗАВЕРШЕНО",
                "-" * 30,
                f"🎯 Действий выполнено: {execution_summary.successful_actions}/{execution_summary.total_actions}",
                f"📊 Процент успеха: {execution_summary.success_rate:.1f}%",
                "",
            ])

            # Детали выполненных действий
            for result in execution_summary.results:
                emoji = "✅" if result.success else "❌"
                report_lines.append(f"{emoji} {result.message}")

            report_lines.append("")

        # Статус и следующие шаги
        report_lines.extend([
            f"📊 **ИИ Статус:** {ai_response.status}",
            f"📝 **Резюме:** {ai_response.summary}",
            ""
        ])

        if ai_response.status == 'completed':
            report_lines.extend([
                "🎉 **ГЕНЕРАЦИЯ ДОКУМЕНТАЦИИ ЗАВЕРШЕНА!**",
                "",
                "📂 Проверьте папку docs/ для просмотра созданной документации",
                "🧹 Временные файлы сессии автоматически очищены",
                ""
            ])
        else:
            report_lines.extend([
                f"🔧 **Следующих действий:** {len(ai_response.next_steps)}",
                "🔄 Запустите gen_docs снова для продолжения",
                ""
            ])

        return "\n".join(report_lines)

    def _generate_error_report(
        self,
        project_path: Path,
        session_state: SessionState,
        error_message: str
    ) -> str:
        """Генерирует отчет об ошибке"""

        return f"""❌ ОШИБКА ГЕНЕРАЦИИ ДОКУМЕНТАЦИИ

📁 Проект: {project_path}
🎯 Сессия: {session_state.session_id}
📋 Шаг: {session_state.step}

🚨 Ошибка: {error_message}

🔧 Рекомендации:
1. Проверьте доступность ИИ модели
2. Убедитесь в корректности путей
3. Проверьте права доступа к файлам
4. Попробуйте очистить сессию и начать заново

💡 Для очистки сессии удалите папку .docs_session/
"""
