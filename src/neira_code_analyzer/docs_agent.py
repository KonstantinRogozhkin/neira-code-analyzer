"""
DocsAgent - умный оркестратор генерации документации

Основной класс-оркестратор, который координирует работу DocsSessionManager 
и ActionExecutor. Использует JSON контракт с ИИ вместо хрупкого парсинга текста.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .docs_session_manager import DocsSessionManager, SessionState
from .action_executor import ActionExecutor, ExecutionSummary

logger = logging.getLogger(__name__)

@dataclass
class AIResponse:
    """Структурированный ответ от ИИ"""
    status: str  # 'in_progress', 'completed', 'error'
    next_steps: List[Dict[str, Any]]  # JSON действия
    summary: str
    analysis: Optional[str] = None
    
    @classmethod
    def from_json(cls, json_data: str) -> 'AIResponse':
        """Создает объект из JSON строки"""
        try:
            data = json.loads(json_data)
            return cls(**data)
        except Exception as e:
            # Fallback для некорректного JSON
            return cls(
                status='error',
                next_steps=[],
                summary=f"Ошибка парсинга JSON: {str(e)}",
                analysis=json_data[:500] if isinstance(json_data, str) else str(json_data)
            )

class DocsAgent:
    """
    Умный оркестратор генерации документации
    
    Координирует работу всех компонентов:
    - DocsSessionManager - управление состоянием
    - ActionExecutor - выполнение действий
    - AI взаимодействие - JSON контракт
    """
    
    def __init__(self):
        self.session_manager = DocsSessionManager()
        self.action_executor = ActionExecutor()
        self.logger = logging.getLogger(self.__class__.__name__)
    
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
        params: Dict
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
        params: Dict
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
        params: Dict, 
        ai_model: str
    ) -> AIResponse:
        """
        Получает начальный анализ проекта от ИИ
        
        В реальной реализации здесь будет вызов к ИИ с JSON промптом.
        Сейчас возвращаем демо-данные для тестирования архитектуры.
        """
        
        self.logger.info("Запрос начального анализа от ИИ")
        
        # TODO: Заменить на реальный вызов ИИ
        # prompt = self._create_analysis_prompt(project_path, params)
        # ai_response_text = await call_ai_model(ai_model, prompt)
        # return AIResponse.from_json(ai_response_text)
        
        # Демо-ответ для тестирования
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
    
    async def _get_next_instructions(
        self, 
        project_path: Path, 
        session_state: SessionState, 
        ai_model: str
    ) -> AIResponse:
        """
        Получает следующие инструкции от ИИ на основе текущего прогресса
        """
        
        self.logger.info("Запрос следующих инструкций от ИИ")
        
        # TODO: Заменить на реальный вызов ИИ
        # prompt = self._create_progress_prompt(project_path, session_state)
        # ai_response_text = await call_ai_model(ai_model, prompt)
        # return AIResponse.from_json(ai_response_text)
        
        # Демо-логика для тестирования
        completed_steps = len(session_state.completed_steps)
        
        if completed_steps < 2:
            # Еще один шаг
            demo_response = {
                "status": "in_progress",
                "summary": f"Шаг {completed_steps + 2}: Создание дополнительной документации",
                "next_steps": [
                    {
                        "action": "create_file",
                        "path": "docs/CHANGELOG.md",
                        "content": "# Changelog\n\n## [Unreleased]\n\n### Added\n- Пошаговая генерация документации\n- Интеграция с Neira для анализа кода\n\n### Fixed\n- Исправлены проблемы с таймаутами"
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
    
    def _create_analysis_prompt(self, project_path: Path, params: Dict) -> str:
        """
        Создает промпт для начального анализа проекта
        
        Возвращает JSON-структурированный промпт для ИИ.
        """
        
        return f"""
Проанализируй проект в папке {project_path} и создай план генерации документации.

ВЕРНИ ОТВЕТ СТРОГО В JSON ФОРМАТЕ:
{{
    "status": "in_progress",
    "summary": "Краткое описание что будет сделано",
    "analysis": "Детальный анализ проекта",
    "next_steps": [
        {{
            "action": "create_file",
            "path": "путь/к/файлу.md",
            "content": "содержимое файла"
        }},
        {{
            "action": "create_directory",
            "path": "путь/к/папке"
        }}
    ]
}}

ПОДДЕРЖИВАЕМЫЕ ДЕЙСТВИЯ:
- create_file: создать файл с содержимым
- create_directory: создать папку
- update_file: обновить существующий файл

ПРАВИЛА:
1. Анализируй структуру проекта
2. Создавай логичную структуру документации
3. Включай практические примеры
4. Используй markdown форматирование
5. НЕ создавай более 3-4 файлов за раз

Начни анализ проекта и верни первые шаги в JSON формате.
"""
    
    def _create_progress_prompt(self, project_path: Path, session_state: SessionState) -> str:
        """
        Создает промпт для проверки прогресса
        """
        
        completed_steps = session_state.completed_steps
        
        return f"""
ПРОВЕРКА ПРОГРЕССА ГЕНЕРАЦИИ ДОКУМЕНТАЦИИ

ПРОЕКТ: {project_path}
ВЫПОЛНЕНО ШАГОВ: {len(completed_steps)}

ВЫПОЛНЕННЫЕ ШАГИ:
{json.dumps(completed_steps, indent=2, ensure_ascii=False)}

ЗАДАЧА:
1. Проверь что уже создано в папке docs/
2. Определи что осталось сделать для завершения документации
3. Если документация готова - верни status: "completed"
4. Если нужны еще шаги - дай следующие 2-3 действия

ВЕРНИ ОТВЕТ В JSON ФОРМАТЕ:
{{
    "status": "in_progress" или "completed",
    "summary": "Что сделано и что дальше",
    "next_steps": [
        // список действий или пустой массив если завершено
    ]
}}
"""
    
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
        execution_summary: Optional[ExecutionSummary]
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