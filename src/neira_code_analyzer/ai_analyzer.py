"""
Neira анализатор для Neira Code Analyzer

Модуль для интеграции с Neira сервисами и анализа кода.
"""

from typing import Optional, Dict, Any
import logging
from pathlib import Path

# Убираем прямые импорты глобальных экземпляров для устранения циклических зависимостей
from .filters import get_code_only_patterns

logger = logging.getLogger(__name__)

# Константы для устранения "магических" значений
DEFAULT_TEMPLATE_NAME = "code-review"
DEFAULT_ENCODING = "cl100k"
DEFAULT_MODEL = "neira-2.5-pro-preview-06-05"

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
            logger.info("Neira analyzer initialized with Neira module")
        except ImportError:
            logger.warning("Neira analyzer initialized without Neira module")
            self._generate_ai_review_func = None

    def generate_ai_review(self, prompt_text: str, model_name: str = DEFAULT_MODEL) -> str:
        """
        Код ревью с помощью Neira
        
        Args:
            prompt_text: Промпт с кодом для анализа
            model_name: Название модели Neira
            
        Returns:
            str: Neira анализ кода
            
        Raises:
            ImportError: Если ai модуль недоступен
            ValueError: Если API ключ не установлен
            Exception: При ошибке взаимодействия с Neira
        """
        if not self._ai_module_available:
            raise ImportError("Модуль ai недоступен. Убедитесь, что файл ai.py существует в src/neira_code_analyzer/ и установлены зависимости")
        
        try:
            logger.info(f"Вызываем Neira анализ с моделью {model_name}")
            result = self._generate_ai_review_func(prompt_text, model_name)
            
            if result and result.strip():
                return result.strip()
            else:
                raise Exception("Получен пустой ответ от Neira")
                
        except Exception as e:
            logger.error(f"Ошибка Neira анализа: {e}")
            raise

    async def perform_code_review(self, path: str, template_name: str = DEFAULT_TEMPLATE_NAME,
                           include_patterns: list = None, exclude_patterns: list = None, 
                           max_tokens: int = 1000000, ai_model: str = DEFAULT_MODEL) -> str:
        """
        Выполнить автоматический Neira анализ кода
        
        Args:
            path: Путь к проекту для анализа
            template_name: Название шаблона анализа
            include_patterns: Паттерны включения файлов
            exclude_patterns: Паттерны исключения файлов  
            max_tokens: Максимальное количество токенов
            ai_model: Модель Neira
            
        Returns:
            str: Результат анализа и статистика
        """
        if include_patterns is None:
            include_patterns = []
        if exclude_patterns is None:
            exclude_patterns = []
            
        logger.info(f"Starting Neira analysis for {path} with template: {template_name}, max tokens: {max_tokens}")
        
        response = f"# 🔍 Автоматический Neira анализ через Neira\n\n"
        response += f"**🎯 Шаблон анализа:** {template_name}\n\n"
        
        try:
            # ЭТАП 1: Генерация промпта из кода
            response += "## 📁 Этап 1: Сбор и анализ кода\n\n"
            
            # Используем ContextGenerator для получения кода
            code_content = self.context_generator.get_context(
                path=path, 
                template_name=template_name,
                include_patterns=include_patterns or [],
                exclude_patterns=exclude_patterns or [],
                line_numbers=True,
                code_blocks=True,
                follow_symlinks=False,
                encoding="cl100k"
            )
            
            if not code_content or len(code_content.strip()) < 100:
                return response + "❌ **ОШИБКА:** Не удалось извлечь достаточно кода для анализа.\n"
            
            # Проверяем количество токенов
            current_tokens = self.context_generator.count_tokens(code_content, "cl100k")
            response += f"**📊 Размер кодовой базы:** {current_tokens:,} токенов\n\n"
            
            if current_tokens > max_tokens:
                return response + f"❌ **ОШИБКА:** Размер кода ({current_tokens:,} токенов) превышает лимит ({max_tokens:,}).\n"
            
            # ЭТАП 4: Анализ через Neira
            ai_analysis, ai_response = await self._fetch_ai_review(code_content, ai_model)
            response += ai_response
            
            # ЭТАП 5: Сохранение результатов (только если есть Neira анализ)
            if ai_analysis:
                response += self._save_results(path, ai_analysis, code_content, current_tokens, ai_model)
                
        except Exception as e:
            logger.error(f"Code review error: {e}")
            return f"❌ **КРИТИЧЕСКАЯ ОШИБКА:** {str(e)}\n"
        
        return response

    async def _run_filter_analysis(self, path: str, include_patterns: list, exclude_patterns: list) -> tuple[int, str]:
        """
        Запуск анализа фильтров
        
        Returns:
            tuple: (количество токенов, текст ответа)
        """
        # Получаем context_generator через DI контейнер для устранения циклических зависимостей
        from .container import get_context_generator
        context_generator = get_context_generator()
        
        response = "## 📊 Этап 1: Анализ структуры проекта\n\n"
        
        # ИСПРАВЛЕНИЕ: Используем analyze_filters вместо set_filters для анализа без побочных эффектов
        filter_args = {
            "path": path,
            "include_patterns": include_patterns,
            "exclude_patterns": exclude_patterns,
            "show_top_files": 5,
            "encoding": DEFAULT_ENCODING
        }
        
        # Получаем структурированный результат анализа
        filter_result = await context_generator.analyze_filters(filter_args)
        current_tokens = filter_result.total_tokens
        
        response += f"**🎯 Текущее количество токенов:** {current_tokens:,}\n"
        
        return current_tokens, response

    async def _optimize_filters_if_needed(self, path: str, current_tokens: int, max_tokens: int,
                                        include_patterns: list, exclude_patterns: list) -> tuple[int, list, list, str]:
        """
        Оптимизация фильтров если количество токенов превышает лимит
        
        Returns:
            tuple: (оптимизированные токены, финальные include паттерны, финальные exclude паттерны, текст ответа)
        """
        # Получаем context_generator через DI контейнер для устранения циклических зависимостей
        from .container import get_context_generator
        context_generator = get_context_generator()
        
        response = ""
        final_include_patterns = include_patterns
        final_exclude_patterns = exclude_patterns
        
        if current_tokens > max_tokens:
            response += "## ⚠️ Этап 2: Оптимизация фильтров\n\n"
            response += f"**Проблема:** {current_tokens:,} токенов превышает лимит {max_tokens:,}\n\n"
            
            # Используем централизованные агрессивные фильтры
            from .filters import get_code_only_patterns
            final_include_patterns, final_exclude_patterns = get_code_only_patterns()
            
            # Если были переданы пользовательские паттерны, объединяем их
            if include_patterns:
                final_include_patterns = list(set(final_include_patterns + include_patterns))
            if exclude_patterns:
                final_exclude_patterns = list(set(final_exclude_patterns + exclude_patterns))
            
            # Повторяем анализ с новыми фильтрами
            optimized_filter_args = {
                "path": path,
                "include_patterns": final_include_patterns,
                "exclude_patterns": final_exclude_patterns,
                "show_top_files": 3,
                "encoding": DEFAULT_ENCODING
            }
            
            # ИСПРАВЛЕНИЕ: Используем analyze_filters вместо set_filters для анализа без побочных эффектов
            optimized_result = await context_generator.analyze_filters(optimized_filter_args)
            optimized_tokens = optimized_result.total_tokens
            
            response += f"**🎯 После оптимизации:** {optimized_tokens:,} токенов\n"
            response += f"**📉 Экономия:** {current_tokens - optimized_tokens:,} токенов\n\n"
            
            current_tokens = optimized_tokens
            
            if current_tokens > max_tokens:
                response += f"❌ **КРИТИЧЕСКАЯ ОШИБКА:** Даже после оптимизации ({current_tokens:,} токенов) превышен лимит {max_tokens:,}.\n"
                response += "💡 **Рекомендация:** Увеличьте max_tokens или анализируйте только часть проекта.\n\n"
                return current_tokens, final_include_patterns, final_exclude_patterns, response
        else:
            response += "## ✅ Этап 2: Фильтры оптимальны\n\n"
            response += f"Количество токенов {current_tokens:,} не превышает лимит {max_tokens:,}\n\n"
        
        return current_tokens, final_include_patterns, final_exclude_patterns, response

    async def _extract_code_with_template(self, path: str, final_include_patterns: list,
                                        final_exclude_patterns: list, current_tokens: int, 
                                        template_name: str = DEFAULT_TEMPLATE_NAME) -> tuple[str, str]:
        """
        Извлечение кода с применением шаблона
        
        Returns:
            tuple: (код содержимое, текст ответа)
        """
        # Получаем зависимости через DI контейнер для устранения циклических зависимостей
        from .container import get_template_manager, get_context_generator
        template_manager = get_template_manager()
        context_generator = get_context_generator()
        
        response = "## 💻 Этап 3: Извлечение кода\n\n"
        
        # Загружаем указанный шаблон
        template_content = template_manager.load_template(template_name)
        
        if not template_content:
            response += f"❌ **ОШИБКА:** Шаблон {template_name}.hbs не найден\n"
            return "", response
        
        # Генерируем код с шаблоном
        context_args = {
            "path": path,
            "template": template_content,
            "include_patterns": final_include_patterns,
            "exclude_patterns": final_exclude_patterns,
            "line_numbers": True,
            "code_blocks": True,
            "encoding": DEFAULT_ENCODING
        }
        
        context_results = await context_generator.get_context(context_args)
        code_content = context_results[0].text if context_results else ""
        
        response += f"**✅ Код извлечен:** ~{current_tokens:,} токенов\n"
        response += f"**🎯 Шаблон:** {template_name}.hbs\n\n"
        
        return code_content, response

    async def _fetch_ai_review(self, code_content: str, ai_model: str) -> tuple[str, str]:
        """
        Получение Neira анализа
        
        Returns:
            tuple: (Neira анализ, текст ответа)
        """
        response = "## 🤖 Этап 4: Анализ через Neira\n\n"
        
        try:
            response += f"**🔄 Отправляем на анализ в {ai_model}...**\n"
            response += f"**📝 Размер промпта:** {len(code_content):,} символов\n\n"
            
            # Вызываем Neira анализ
            ai_analysis = self.generate_ai_review(code_content, ai_model)
            
            if ai_analysis and ai_analysis.strip():
                ai_analysis = ai_analysis.strip()
                response += "**✅ Анализ получен от Neira:**\n\n"
                return ai_analysis, response
            else:
                response += "❌ **ОШИБКА:** Получен пустой ответ от Neira\n"
                return "", response
                
        except Exception as ai_error:
            response += f"❌ **ОШИБКА Neira:** {str(ai_error)}\n"
            logger.error(f"Neira analysis error: {ai_error}")
            return "", response

    def _save_results(self, path: str, ai_analysis: str, code_content: str,
                     current_tokens: int, ai_model: str) -> str:
        """
        Сохранение результатов анализа и возврат краткого отчёта
        
        Returns:
            str: Краткий отчёт со ссылкой на сохранённый файл
        """
        response = "## 💾 Этап 5: Сохранение результатов\n\n"
        
        # Сохраняем результаты
        saved_files = self._save_review_results(
            path, ai_analysis, code_content, current_tokens, ai_model
        )
        
        analyze_file_path = None
        for file_info in saved_files:
            response += f"- {file_info}\n"
            # Ищем путь к файлу анализа
            if "Neira анализ:" in file_info and "`" in file_info:
                analyze_file_path = file_info.split("`")[1]
        
        response += f"\n**📋 Всего файлов сохранено:** {len(saved_files)}\n\n"
        
        # Выводим краткий отчёт вместо полного содержимого
        response += "## ✅ Анализ завершён\n\n"
        if analyze_file_path:
            response += f"**📄 Полный отчёт сохранён в:** `{analyze_file_path}`\n\n"
            response += f"**🔍 Следующие шаги:**\n"
            response += f"1. Откройте файл `{analyze_file_path}` для изучения детального анализа\n"
            response += f"2. Изучите рекомендации и приоритеты исправлений\n"
            response += f"3. Внесите изменения в проект согласно анализу\n\n"
            response += f"**💡 Для получения детального анализа и рекомендаций откройте сохранённый файл.**"
        else:
            # Если не удалось найти путь к файлу, показываем анализ как раньше
            response += "---\n\n"
            response += ai_analysis
        
        return response

    def _save_review_results(self, path: str, ai_analysis: str, code_content: str,
                           token_count: int, model_name: str) -> list[str]:
        """
        Сохранить результаты анализа в файлы
        
        Returns:
            list[str]: Список описаний сохраненных файлов
        """
        from datetime import datetime
        
        # Получаем project_manager через DI контейнер
        from .container import get_project_manager
        project_manager = get_project_manager()
        
        # Создаем версионированную структуру для сохранения
        project_folder, version = project_manager.get_next_project_version(path)
        project_name = project_manager.get_project_name(path)
        
        saved_files = []
        
        try:
            # 1. Сохраняем Neira анализ
            analyze_filename = f"{project_name}.analyze.md"
            analyze_save_path = project_folder / analyze_filename
            
            final_content = f"# 🔍 Code Review Analysis - {project_name}\n\n"
            final_content += f"**📅 Дата анализа:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            final_content += f"**🎯 Модель:** {model_name}\n"
            final_content += f"**📊 Токенов проанализировано:** {token_count:,}\n"
            final_content += f"**📁 Проект:** `{path}`\n\n"
            final_content += "---\n\n"
            final_content += ai_analysis
            
            analyze_save_path.write_text(final_content, encoding='utf-8')
            saved_files.append(f"📋 Neira анализ: `{analyze_save_path}`")
            
            # 2. Сохраняем извлеченный код
            code_filename = f"{project_name}.code.md"
            code_save_path = project_folder / code_filename
            code_save_path.write_text(code_content, encoding='utf-8')
            saved_files.append(f"💻 Код: `{code_save_path}`")
            
            logger.info(f"Review results saved to {len(saved_files)} files")
            
        except Exception as e:
            logger.error(f"Error saving review results: {e}")
            saved_files.append(f"❌ Ошибка сохранения: {e}")
        
        return saved_files


# Глобальный экземпляр убран - используем DI контейнер для получения экземпляра 