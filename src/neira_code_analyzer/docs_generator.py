"""
Пошаговый генератор документации с использованием Neira

Работает как агент-помощник:
1. gen_docs → анализирует проект через Neira
2. Neira выдает конкретные инструкции что делать
3. Агент выполняет инструкции (создает файлы, структуру)
4. gen_docs снова → проверка и следующие инструкции  
5. И так пошагово до завершения

Принцип: Neira - мозг (анализ + инструкции), агент - руки (выполнение)
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class DocsGenerator:
    """
    Пошаговый генератор документации с Neira
    
    Этапы работы:
    1. ANALYZE - Neira анализирует проект и состояние
    2. INSTRUCT - Neira выдает конкретные инструкции
    3. EXECUTE - Агент выполняет инструкции  
    4. CHECK - Neira проверяет результат
    5. NEXT - Переход к следующему шагу
    """
    
    def __init__(self):
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.step_counter = 0
        self.session_log = []
        
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
        Запуск пошагового процесса генерации документации
        
        Возвращает либо инструкции от Neira, либо отчет о выполнении
        """
        project_path = Path(path).resolve()
        
        logger.info(f"🤖 Запуск пошагового gen_docs для: {project_path}")
        
        # Загружаем состояние сессии если есть
        session_state = self._load_session_state(project_path)
        
        if session_state is None:
            # Новая сессия - начинаем с анализа
            return await self._start_new_session(project_path, ai_model, kwargs)
        else:
            # Продолжаем существующую сессию
            return await self._continue_session(project_path, session_state, ai_model, kwargs)
    
    async def _start_new_session(self, project_path: Path, ai_model: str, params: Dict) -> str:
        """Начинает новую сессию документации"""
        
        self.step_counter = 1
        
        # Создаем рабочую папку для сессии
        session_dir = project_path / ".docs_session"
        session_dir.mkdir(exist_ok=True)
        
        report = []
        report.append("🤖 ПОШАГОВАЯ ГЕНЕРАЦИЯ ДОКУМЕНТАЦИИ")
        report.append("=" * 40)
        report.append(f"📁 Проект: {project_path}")
        report.append(f"🎯 Сессия: {self.session_id}")
        report.append(f"📋 Шаг: {self.step_counter}/? - НАЧАЛЬНЫЙ АНАЛИЗ")
        report.append("")
        
        try:
            # ТЕСТОВЫЙ РЕЖИМ: Используем заготовленные инструкции вместо Neira
            # TODO: Потом заменить на реальный вызов Neira
            
            # Генерируем тестовые инструкции на основе структуры проекта
            instructions = self._generate_test_instructions(project_path)
            
            # Сохраняем состояние сессии
            session_state = {
                'session_id': self.session_id,
                'project_path': str(project_path),
                'step': self.step_counter,
                'status': 'analyzing',
                'params': params,
                'instructions': instructions,
                'completed_steps': [],
                'ai_model': ai_model
            }
            
            self._save_session_state(project_path, session_state)
            
            report.append("🧠 АНАЛИЗ ЗАВЕРШЕН - ПОЛУЧЕНЫ ИНСТРУКЦИИ")
            report.append("-" * 40)
            report.append("")
            report.append("📋 ИНСТРУКЦИИ (ТЕСТОВЫЙ РЕЖИМ):")
            report.extend(instructions)
            report.append("")
            report.append("🔄 Для выполнения инструкций запустите gen_docs еще раз")
            
        except Exception as e:
            logger.error(f"Ошибка анализа: {e}")
            report.append(f"❌ ОШИБКА АНАЛИЗА: {str(e)}")
            
        return "\n".join(report)
    
    def _generate_test_instructions(self, project_path: Path) -> List[str]:
        """Генерирует тестовые инструкции для проверки логики"""
        
        # Проверяем что уже есть в проекте
        docs_exists = (project_path / "docs").exists()
        readme_exists = (project_path / "README.md").exists()
        
        instructions = []
        
        if not docs_exists:
            instructions.extend([
                "STEP 1: Создать базовую структуру документации",
                "Создать docs/README.md с содержимым:",
                "```",
                "# Документация neira-code-analyzer",
                "",
                "## Обзор",
                "MCP сервер для продвинутого анализа кодовых баз.",
                "",
                "## Быстрый старт",
                "1. Установите зависимости: `uv sync`",
                "2. Запустите сервер: `uv run python -m src.neira_code_analyzer.main`",
                "```"
            ])
        
        if not (project_path / "docs" / "guides").exists():
            instructions.extend([
                "STEP 2: Создать папку руководств",
                "Создать docs/guides/quickstart.md с содержимым:",
                "```",
                "# Быстрый старт",
                "",
                "## Установка",
                "```bash",
                "git clone https://github.com/odancona/neira-code-analyzer.git",
                "cd neira-code-analyzer",
                "uv sync",
                "```",
                "",
                "## Первый запуск",
                "```bash",
                "uv run python -m src.neira_code_analyzer.main",
                "```",
                "```"
            ])
        
        if not instructions:
            instructions = ["COMPLETED"]
            
        return instructions
    
    async def _continue_session(self, project_path: Path, session_state: Dict, ai_model: str, params: Dict) -> str:
        """Продолжает существующую сессию"""
        
        self.step_counter = session_state['step'] + 1
        
        report = []
        report.append("🔄 ПРОДОЛЖЕНИЕ СЕССИИ ДОКУМЕНТАЦИИ")
        report.append("=" * 40)
        report.append(f"📁 Проект: {project_path}")  
        report.append(f"🎯 Сессия: {session_state['session_id']}")
        report.append(f"📋 Шаг: {self.step_counter}/? - ВЫПОЛНЕНИЕ ИНСТРУКЦИЙ")
        report.append("")
        
        try:
            # Выполняем инструкции из предыдущего шага
            execution_result = await self._execute_instructions(project_path, session_state['instructions'])
            
            report.append("✅ ВЫПОЛНЕНИЕ ЗАВЕРШЕНО")
            report.append("-" * 30)
            report.extend(execution_result)
            report.append("")
            
            # Обновляем состояние
            session_state['step'] = self.step_counter
            session_state['completed_steps'].append({
                'step': self.step_counter,
                'instructions': session_state['instructions'],
                'result': execution_result
            })
            
            # Запрашиваем у Neira следующие инструкции
            next_instructions = await self._get_next_instructions(project_path, session_state, ai_model)
            
            if next_instructions and len(next_instructions) > 0 and next_instructions[0] != "COMPLETED":
                # Есть еще работа
                session_state['instructions'] = next_instructions
                session_state['status'] = 'continuing'
                self._save_session_state(project_path, session_state)
                
                report.append("🧠 ПОЛУЧЕНЫ СЛЕДУЮЩИЕ ИНСТРУКЦИИ")
                report.append("-" * 30)
                report.extend(next_instructions)
                report.append("")
                report.append("🔄 Для продолжения запустите gen_docs еще раз")
                
            else:
                # Документация завершена
                session_state['status'] = 'completed'
                self._save_session_state(project_path, session_state)
                
                report.append("🎉 ГЕНЕРАЦИЯ ДОКУМЕНТАЦИИ ЗАВЕРШЕНА!")
                report.append("-" * 30)
                report.append(f"📊 Выполнено шагов: {len(session_state['completed_steps'])}")
                report.append("🗂️ Проверьте папку docs/ для просмотра результата")
                
                # Очищаем сессию
                self._cleanup_session(project_path)
            
        except Exception as e:
            logger.error(f"Ошибка выполнения: {e}")
            report.append(f"❌ ОШИБКА ВЫПОЛНЕНИЯ: {str(e)}")
            
        return "\n".join(report)
    
    def _create_docs_analysis_prompt(self, project_path: Path, params: Dict) -> str:
        """Создает промпт для анализа проекта и генерации инструкций"""
        
        return f"""
ЗАДАЧА: Проанализируй проект и выдай пошаговые инструкции для создания документации.

ПРОЕКТ: {project_path}
ПАРАМЕТРЫ: {json.dumps(params, indent=2)}

АНАЛИЗИРУЙ:
1. Структуру проекта и существующую документацию
2. Тип проекта (Python, React, библиотека, сервис и т.д.)
3. Что нужно документировать (API, установка, использование и т.д.)
4. Какие файлы уже есть и что нужно создать/обновить

ВЫДАЙ КОНКРЕТНЫЕ ПОШАГОВЫЕ ИНСТРУКЦИИ:
- Начни с "STEP 1:", "STEP 2:" и т.д.
- Для каждого шага укажи:
  * Что создать/обновить (файл, папку)
  * Какое содержимое написать
  * Конкретный путь к файлу
  * Конкретный текст/структуру

ПРИМЕР ИНСТРУКЦИЙ:
STEP 1: Создать docs/README.md с содержимым:
```
# Документация проекта
...конкретный текст...
```

STEP 2: Создать docs/setup/installation.md с содержимым:
```
# Установка
...конкретные шаги...
```

ВАЖНО: Давай только первые 2-3 шага, не все сразу. После выполнения я запрошу следующие инструкции.
"""
    
    def _extract_instructions_from_analysis(self, analysis_result: str) -> List[str]:
        """Извлекает инструкции из результата анализа Neira"""
        
        instructions = []
        lines = analysis_result.split('\n')
        
        current_step = None
        current_content = []
        
        for line in lines:
            stripped = line.strip()
            
            # Ищем начало шага
            if stripped.startswith('STEP ') and ':' in stripped:
                # Сохраняем предыдущий шаг
                if current_step:
                    instructions.append(f"{current_step}")
                    if current_content:
                        instructions.extend(current_content)
                
                # Начинаем новый шаг
                current_step = stripped
                current_content = []
                
            elif current_step and stripped:
                # Добавляем содержимое к текущему шагу
                current_content.append(line)
        
        # Добавляем последний шаг
        if current_step:
            instructions.append(current_step)
            if current_content:
                instructions.extend(current_content)
        
        return instructions
    
    async def _execute_instructions(self, project_path: Path, instructions: List[str]) -> List[str]:
        """Выполняет инструкции от Neira"""
        
        results = []
        
        current_step = None
        step_content = []
        
        for instruction in instructions:
            if instruction.startswith('STEP '):
                # Выполняем предыдущий шаг
                if current_step and step_content:
                    step_result = self._execute_single_step(project_path, current_step, step_content)
                    results.extend(step_result)
                
                # Начинаем новый шаг
                current_step = instruction
                step_content = []
                
            else:
                step_content.append(instruction)
        
        # Выполняем последний шаг
        if current_step and step_content:
            step_result = self._execute_single_step(project_path, current_step, step_content)
            results.extend(step_result)
        
        return results
    
    def _execute_single_step(self, project_path: Path, step_title: str, step_content: List[str]) -> List[str]:
        """Выполняет один шаг инструкций"""
        
        results = [f"🔧 {step_title}"]
        
        try:
            # Парсим инструкции шага
            file_path = None
            content_lines = []
            in_code_block = False
            
            for line in step_content:
                stripped = line.strip()
                
                # Ищем путь к файлу
                if ('создать' in line.lower() or 'create' in line.lower()) and ('.md' in line or '.txt' in line):
                    # Извлекаем путь к файлу
                    words = line.split()
                    for word in words:
                        if '.md' in word or '.txt' in word:
                            file_path = word
                            break
                
                # Собираем содержимое из блока кода
                if line.startswith('```'):
                    in_code_block = not in_code_block
                    continue
                    
                if in_code_block:
                    content_lines.append(line)
            
            # Создаем файл если указан путь и есть содержимое
            if file_path and content_lines:
                full_path = project_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
                content = '\n'.join(content_lines)
                full_path.write_text(content, encoding='utf-8')
                
                results.append(f"✅ Создан: {file_path}")
                results.append(f"📝 Размер: {len(content_lines)} строк")
                
            else:
                results.append("⚠️ Не удалось определить файл или содержимое")
                
        except Exception as e:
            results.append(f"❌ Ошибка: {str(e)}")
            
        return results
    
    async def _get_next_instructions(self, project_path: Path, session_state: Dict, ai_model: str) -> List[str]:
        """Запрашивает у Neira следующие инструкции"""
        
        try:
            # ТЕСТОВЫЙ РЕЖИМ: Генерируем следующие инструкции без вызова Neira
            # TODO: Потом заменить на реальный вызов Neira
            
            completed_steps = session_state.get('completed_steps', [])
            
            # Простая логика: если выполнили менее 3 шагов, даем еще один
            if len(completed_steps) < 2:
                return self._generate_next_test_instructions(project_path, completed_steps)
            else:
                # Завершаем после 2-3 шагов
                return ["COMPLETED"]
            
        except Exception as e:
            logger.error(f"Ошибка получения следующих инструкций: {e}")
            return []

    def _generate_next_test_instructions(self, project_path: Path, completed_steps: List[Dict]) -> List[str]:
        """Генерирует следующие тестовые инструкции"""
        
        step_count = len(completed_steps)
        
        if step_count == 1:
            # После первого шага - создаем changelog
            return [
                "STEP 3: Создать файл changelog",
                "Создать docs/CHANGELOG.md с содержимым:",
                "```",
                "# Changelog",
                "",
                "## [Unreleased]",
                "",
                "### Added", 
                "- Пошаговая генерация документации",
                "- Интеграция с Neira для анализа кода",
                "",
                "### Fixed",
                "- Исправлены проблемы с таймаутами",
                "```"
            ]
        
        # После второго шага завершаем
        return ["COMPLETED"]
    
    def _create_progress_prompt(self, project_path: Path, session_state: Dict) -> str:
        """Создает промпт для проверки прогресса и получения следующих шагов"""
        
        completed_steps = session_state.get('completed_steps', [])
        
        return f"""
ПРОГРЕСС ГЕНЕРАЦИИ ДОКУМЕНТАЦИИ:

ПРОЕКТ: {project_path}
ВЫПОЛНЕНО ШАГОВ: {len(completed_steps)}

ВЫПОЛНЕННЫЕ ШАГИ:
{json.dumps(completed_steps, indent=2, ensure_ascii=False)}

ПРОВЕРЬ:
1. Что уже создано в папке docs/
2. Какие файлы успешно созданы
3. Что осталось сделать

ВЫДАЙ СЛЕДУЮЩИЕ 2-3 ШАГА:
- Если документация не завершена - дай следующие инструкции
- Если все готово - верни COMPLETED

ФОРМАТ ИНСТРУКЦИЙ:
STEP X: Конкретное действие
```
конкретное содержимое
```

Или просто:
COMPLETED
"""
    
    def _load_session_state(self, project_path: Path) -> Optional[Dict]:
        """Загружает состояние сессии"""
        
        session_file = project_path / ".docs_session" / "state.json"
        
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Ошибка загрузки сессии: {e}")
                
        return None
    
    def _save_session_state(self, project_path: Path, state: Dict):
        """Сохраняет состояние сессии"""
        
        session_dir = project_path / ".docs_session"
        session_dir.mkdir(exist_ok=True)
        
        session_file = session_dir / "state.json"
        
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Ошибка сохранения сессии: {e}")
    
    def _cleanup_session(self, project_path: Path):
        """Очищает файлы сессии после завершения"""
        
        session_dir = project_path / ".docs_session"
        
        if session_dir.exists():
            try:
                import shutil
                shutil.rmtree(session_dir)
                logger.info("Сессия очищена")
            except Exception as e:
                logger.warning(f"Ошибка очистки сессии: {e}") 