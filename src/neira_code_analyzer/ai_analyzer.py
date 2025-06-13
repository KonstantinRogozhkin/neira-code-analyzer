"""
Neira анализатор для Neira Code Analyzer

Модуль для интеграции с AI сервисами и анализа кода.
"""

from typing import Optional, Dict, Any
import logging
from pathlib import Path
from dataclasses import dataclass

# Убираем прямые импорты глобальных экземпляров для устранения циклических зависимостей
from .filters import get_code_only_patterns

logger = logging.getLogger(__name__)

# Константы для устранения "магических" значений
DEFAULT_TEMPLATE_NAME = "code-review"
DEFAULT_ENCODING = "cl100k"
DEFAULT_MODEL = "gemini-2.5-pro-preview-06-05"

@dataclass
class AnalysisJob:
    """Класс для хранения параметров анализа кода"""
    path: str
    template_name: str = DEFAULT_TEMPLATE_NAME
    include_patterns: list = None
    exclude_patterns: list = None
    max_tokens: int = 1000000
    ai_model: str = DEFAULT_MODEL
    preset_name: str = None
    merge_with_preset: bool = False
    save_as_preset: str = None
    
    # Рабочие переменные (заполняются в процессе)
    resolved_include: list = None
    resolved_exclude: list = None
    current_tokens: int = 0
    code_content: str = ""
    ai_analysis: str = ""
    
    def __post_init__(self):
        """Инициализация значений по умолчанию"""
        if self.include_patterns is None:
            self.include_patterns = []
        if self.exclude_patterns is None:
            self.exclude_patterns = []

class NeiraAnalyzer:
    """Анализатор кода с помощью Neira"""
    
    def __init__(self):
        """Инициализация Neira анализатора"""
        # Инициализируем ai модуль из ai_utils для избежания циклических зависимостей
        self._ai_module_available = False
        try:
            from .ai_utils import generate_ai_review
            self._generate_ai_review_func = generate_ai_review
            self._ai_module_available = True
            logger.info("Google AI analyzer initialized with Google AI module")
        except ImportError:
            logger.warning("Google AI analyzer initialized without Google AI module")
            self._generate_ai_review_func = None
            
        # АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: Создаем context_generator напрямую
        # Это устраняет циклическую зависимость через DI-контейнер
        self.context_generator = None
        try:
            from .context_generator import ContextGenerator
            self.context_generator = ContextGenerator()
            logger.info("Context generator initialized directly (no DI container)")
        except Exception as e:
            logger.error(f"Failed to initialize context generator: {e}")

    def generate_ai_review(self, prompt_text: str, model_name: str = DEFAULT_MODEL) -> str:
        """
        Код ревью с помощью Neira
        
        Args:
            prompt_text: Промпт с кодом для анализа
            model_name: Название модели Google AI/Gemini
            
        Returns:
            str: Neira анализ кода
            
        Raises:
            ImportError: Если ai модуль недоступен
            ValueError: Если API ключ не установлен
            Exception: При ошибке взаимодействия с AI
        """
        if not self._ai_module_available:
            raise ImportError("Модуль ai недоступен. Убедитесь, что файл ai.py существует в src/neira_code_analyzer/ и установлены зависимости")
        
        try:
            logger.info(f"Вызываем Google AI анализ с моделью {model_name}")
            result = self._generate_ai_review_func(prompt_text, model_name)
            
            if result and result.strip():
                return result.strip()
            else:
                raise Exception("Получен пустой ответ от Google AI")
                
        except Exception as e:
            logger.error(f"Ошибка Google AI анализа: {e}")
            raise

    async def perform_code_review(self, path: str, template_name: str = DEFAULT_TEMPLATE_NAME,
                           include_patterns: list = None, exclude_patterns: list = None, 
                           max_tokens: int = 1000000, ai_model: str = DEFAULT_MODEL,
                           preset_name: str = None, merge_with_preset: bool = False,
                           save_as_preset: str = None) -> str:
        """
        Выполнить автоматический Neira анализ кода
        
        Args:
            path: Путь к проекту для анализа
            template_name: Название шаблона анализа
            include_patterns: Паттерны включения файлов
            exclude_patterns: Паттерны исключения файлов  
            max_tokens: Максимальное количество токенов
            ai_model: Модель Neira
            preset_name: Название пресета для фильтрации файлов
            merge_with_preset: Объединить пресет с пользовательскими паттернами
            save_as_preset: Сохранить текущие настройки как новый пресет
            
        Returns:
            str: Результат анализа и статистика
        """
        # Создаем объект задания анализа
        job = AnalysisJob(
            path=path,
            template_name=template_name,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            max_tokens=max_tokens,
            ai_model=ai_model,
            preset_name=preset_name,
            merge_with_preset=merge_with_preset,
            save_as_preset=save_as_preset
        )
        
        try:
            # Этап 1: Валидация параметров
            validation_error = self._validate_parameters(job)
            if validation_error:
                return validation_error
            
            # Этап 2: Разрешение фильтров и пресетов
            self._resolve_filters(job)
            
            # Этап 3: Генерация контекста кода
            context_response = await self._generate_code_context(job)
            if not job.code_content:
                return context_response  # Вернем ошибку генерации контекста
            
            # Этап 4: Проверка лимита токенов
            if job.current_tokens > job.max_tokens:
                return context_response + f"❌ **ОШИБКА:** Размер кода ({job.current_tokens:,} токенов) превышает лимит ({job.max_tokens:,}).\n"
            
            # Этап 5: AI анализ
            ai_response = await self._fetch_ai_analysis(job)
            
            # Этап 6: Сохранение результатов
            save_response = self._save_analysis_results(job)
            
            # Этап 7: Сохранение пресета (если запрошено)
            preset_response = self._save_preset_if_requested(job)
            
            # Формируем итоговый ответ
            return self._build_final_response(job, context_response, ai_response, save_response, preset_response)
            
        except Exception as e:
            logger.error(f"Code review error: {e}")
            return f"❌ **КРИТИЧЕСКАЯ ОШИБКА:** {str(e)}\n"

    def _validate_parameters(self, job: AnalysisJob) -> str:
        """Валидация входных параметров"""
        if not job.path or not isinstance(job.path, str):
            return "❌ **ОШИБКА ВАЛИДАЦИИ:** Параметр 'path' обязателен и должен быть строкой.\n"
            
        if not job.template_name or not isinstance(job.template_name, str):
            return f"❌ **ОШИБКА ВАЛИДАЦИИ:** Параметр 'template_name' должен быть строкой. Получено: {type(job.template_name)}\n"
        
        if not isinstance(job.include_patterns, list):
            return f"❌ **ОШИБКА ВАЛИДАЦИИ:** 'include_patterns' должен быть списком. Получено: {type(job.include_patterns)}\n"
            
        if not isinstance(job.exclude_patterns, list):
            return f"❌ **ОШИБКА ВАЛИДАЦИИ:** 'exclude_patterns' должен быть списком. Получено: {type(job.exclude_patterns)}\n"
            
        if not isinstance(job.max_tokens, int) or job.max_tokens <= 0:
            return f"❌ **ОШИБКА ВАЛИДАЦИИ:** 'max_tokens' должен быть положительным числом. Получено: {job.max_tokens}\n"
            
        if not job.ai_model or not isinstance(job.ai_model, str):
            return f"❌ **ОШИБКА ВАЛИДАЦИИ:** 'ai_model' должен быть строкой. Получено: {type(job.ai_model)}\n"
            
        if job.preset_name is not None and not isinstance(job.preset_name, str):
            return f"❌ **ОШИБКА ВАЛИДАЦИИ:** 'preset_name' должен быть строкой или None. Получено: {type(job.preset_name)}\n"
            
        if not isinstance(job.merge_with_preset, bool):
            return f"❌ **ОШИБКА ВАЛИДАЦИИ:** 'merge_with_preset' должен быть boolean. Получено: {type(job.merge_with_preset)}\n"
            
        return ""  # Все параметры валидны

    def _resolve_filters(self, job: AnalysisJob) -> None:
        """Разрешение паттернов с учетом пресета"""
        if not job.preset_name:
            job.resolved_include = job.include_patterns
            job.resolved_exclude = job.exclude_patterns
            return
            
        try:
            # Получаем паттерны из пресета
            from .filters import load_preset
            preset_patterns = load_preset(job.preset_name)
            
            if not preset_patterns:
                logger.warning(f"Пресет '{job.preset_name}' не найден, используем исходные паттерны")
                job.resolved_include = job.include_patterns
                job.resolved_exclude = job.exclude_patterns
                return
                
            preset_include = preset_patterns.get("include", [])
            preset_exclude = preset_patterns.get("exclude", [])
            
            if job.merge_with_preset:
                # Объединяем паттерны: пресет + пользовательские
                job.resolved_include = list(set(preset_include + job.include_patterns))  
                job.resolved_exclude = list(set(preset_exclude + job.exclude_patterns))
                logger.info(f"Объединены паттерны пресета '{job.preset_name}' с пользовательскими")
            else:
                # Заменяем паттерны на паттерны из пресета
                job.resolved_include = preset_include
                job.resolved_exclude = preset_exclude
                logger.info(f"Используются паттерны из пресета '{job.preset_name}'")
                
        except Exception as e:
            logger.error(f"Ошибка при загрузке пресета '{job.preset_name}': {e}")
            job.resolved_include = job.include_patterns
            job.resolved_exclude = job.exclude_patterns

    async def _generate_code_context(self, job: AnalysisJob) -> str:
        """Генерация контекста кода"""
        logger.info(f"Starting Neira analysis for {job.path} with template: {job.template_name}, max tokens: {job.max_tokens}")
        
        # Проверяем что context_generator инициализирован
        if not self.context_generator:
            return "❌ **КРИТИЧЕСКАЯ ОШИБКА:** Context generator не инициализирован. Перезапустите сервер.\n"
        
        response = f"# 🔍 Автоматический анализ кода через Neira\n\n"
        response += f"**🎯 Шаблон анализа:** {job.template_name}\n\n"
        
        # Добавляем информацию о пресете если используется
        if job.preset_name:
            response += f"**🎛️ Пресет:** {job.preset_name} ({'объединен' if job.merge_with_preset else 'заменен'})\n\n"
        
        response += "## 📁 Этап 1: Сбор и анализ кода\n\n"
        
        # Используем ContextGenerator для получения кода с resolved паттернами
        context_args = {
            "path": job.path,
            "template_name": job.template_name,
            "include_patterns": job.resolved_include,
            "exclude_patterns": job.resolved_exclude,
            "line_numbers": True,
            "code_blocks": True,
            "follow_symlinks": False,
            "encoding": "cl100k"
        }
        
        context_results = await self.context_generator.get_context(context_args)
        job.code_content = context_results[0].text if context_results else ""
        
        if not job.code_content or len(job.code_content.strip()) < 100:
            return response + "❌ **ОШИБКА:** Не удалось извлечь достаточно кода для анализа.\n"
        
        # Пытаемся получить точное количество токенов из результата code2prompt-rs
        # Если недоступно, используем эстимацию с явным предупреждением
        try:
            # Попытка извлечь точное количество токенов из контекста
            # (в будущих версиях может быть улучшено)
            job.current_tokens = int(len(job.code_content.split()) * 1.3)  # Эвристика: ~1.3 токена на слово
            
            response += f"**📊 Размер кодовой базы:** {job.current_tokens:,} токенов ⚠️ *(оценочно)*\n\n"
            response += "**💡 Примечание:** Количество токенов рассчитано приблизительно. Для точного подсчета требуется дополнительная интеграция с токенизатором.\n\n"
        except Exception as e:
            logger.warning(f"Unable to estimate tokens accurately: {e}")
            job.current_tokens = 0
            response += f"**📊 Размер кодовой базы:** *(не удалось определить)*\n\n"
        
        return response

    async def _fetch_ai_analysis(self, job: AnalysisJob) -> str:
        """Получение AI анализа кода"""
        response = "## 🤖 Этап 4: Анализ через Neira\n\n"
        response += f"**🔄 Отправляем на анализ в {job.ai_model}...**\n"
        response += f"**📝 Размер промпта:** {len(job.code_content):,} символов\n\n"
        
        try:
            job.ai_analysis = self.generate_ai_review(job.code_content, job.ai_model)
            response += "**✅ Анализ получен от Neira:**\n\n"
            return response
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            response += f"❌ **ОШИБКА AI АНАЛИЗА:** {str(e)}\n\n"
            return response

    def _save_analysis_results(self, job: AnalysisJob) -> str:
        """Сохранение результатов анализа"""
        if not job.ai_analysis:
            return ""
            
        response = "## 💾 Этап 5: Сохранение результатов\n\n"
        
        try:
            saved_files = self._save_review_results(
                job.path, job.ai_analysis, job.code_content, 
                job.current_tokens, job.ai_model
            )
            
            for i, file_path in enumerate(saved_files, 1):
                file_type = "Neira анализ" if "analyze" in file_path else "Код"
                response += f"- 📋 {file_type}: `{file_path}`\n"
            
            response += f"\n**📋 Всего файлов сохранено:** {len(saved_files)}\n\n"
            return response
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return f"❌ **ОШИБКА СОХРАНЕНИЯ:** {str(e)}\n\n"

    def _save_preset_if_requested(self, job: AnalysisJob) -> str:
        """Сохранение пресета если запрошено"""
        if not job.save_as_preset:
            return ""
            
        try:
            from .filters import FilterManager
            manager = FilterManager()
            
            # Определяем описание на основе пути
            project_name = job.path.split('/')[-1] if '/' in job.path else job.path
            description = f"Настройки для проекта {project_name}"
            
            saved_name = manager.save_preset(
                job.save_as_preset, job.resolved_include, job.resolved_exclude, description
            )
            
            return f"\n## 💾 Пресет сохранен\n\n**Название:** {saved_name}\n**Описание:** {description}\n\n"
            
        except Exception as e:
            logger.error(f"Ошибка сохранения пресета '{job.save_as_preset}': {e}")
            return f"\n❌ **ОШИБКА:** Не удалось сохранить пресет '{job.save_as_preset}': {str(e)}\n\n"

    def _build_final_response(self, job: AnalysisJob, context_response: str, 
                             ai_response: str, save_response: str, preset_response: str) -> str:
        """Построение итогового ответа"""
        response = context_response + ai_response + save_response + preset_response

        # Добавляем заключение
        if job.ai_analysis:
            response += "## ✅ Анализ завершён\n\n"
            # Находим путь к файлу анализа для отображения
            if "analyze" in save_response:
                import re
                analyze_file_match = re.search(r'`([^`]*analyze[^`]*)`', save_response)
                if analyze_file_match:
                    analyze_file_path = analyze_file_match.group(1)
                    response += f"**📄 Полный отчёт сохранён в:** `{analyze_file_path}`\n\n"
            
            response += "**🔍 Следующие шаги:**\n"
            response += f"1. Откройте файл с анализом для изучения детального анализа\n"
            response += "2. Изучите рекомендации и приоритеты исправлений\n"
            response += "3. Внесите изменения в проект согласно анализу\n\n"
            response += "**💡 Для получения детального анализа и рекомендаций откройте сохранённый файл.**"
        
        return response

    def _save_review_results(self, path: str, ai_analysis: str, code_content: str,
                           token_count: int, model_name: str) -> list[str]:
        """
        Сохранение результатов анализа в версионированную структуру файлов
        
        Returns:
            list[str]: Список путей сохраненных файлов
        """
        try:
            from .project_manager import ProjectManager
            
            # Создаем экземпляр менеджера проектов и получаем версионированный путь
            project_manager = ProjectManager()
            base_path, version = project_manager.get_next_project_version(path)
            
            # Формируем имя проекта из пути
            project_name = Path(path).name if Path(path).name else "project"
            
            # Сохраняем файл с AI анализом
            analyze_filename = f"{project_name}.analyze.md"
            analyze_path = base_path / analyze_filename
            
            analyze_content = f"# 🔍 Code Review Analysis - {project_name}\n\n"
            analyze_content += f"**📅 Дата анализа:** {base_path.parent.parent.name}\n"  # Извлекаем дату из структуры папок
            analyze_content += f"**🎯 Модель:** {model_name}\n"
            analyze_content += f"**📊 Токенов проанализировано:** {token_count:,}\n"
            analyze_content += f"**📁 Проект:** `{path}`\n\n"
            analyze_content += "---\n\n"
            analyze_content += ai_analysis
            
            with open(analyze_path, "w", encoding="utf-8") as f:
                f.write(analyze_content)
            
            # Сохраняем файл с исходным кодом
            code_filename = f"{project_name}.code.md"
            code_path = base_path / code_filename
            
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(code_content)
            
            saved_files = [str(analyze_path), str(code_path)]
            logger.info(f"Analysis results saved to: {saved_files}")
            
            return saved_files
        
        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
            raise


# Глобальный экземпляр убран - используем DI контейнер для получения экземпляра 