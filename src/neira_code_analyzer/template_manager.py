"""
Менеджер шаблонов для Neira Code Analyzer

Централизованная логика работы с шаблонами анализа кода.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class TemplateManager:
    """Управление шаблонами для анализа кода"""

    def __init__(self, templates_dir: Path | None = None):
        """
        Инициализация менеджера шаблонов

        Args:
            templates_dir: Путь к папке с шаблонами. По умолчанию ищет в проекте.
        """
        if templates_dir is None:
            # Определяем путь к папке templates относительно текущего файла
            current_dir = Path(__file__).parent.parent.parent
            self.templates_dir = current_dir / "templates"
        else:
            self.templates_dir = templates_dir

        logger.info(f"Template manager initialized with dir: {self.templates_dir}")

    def get_available_templates(self) -> list[str]:
        """
        Получить список доступных шаблонов

        Returns:
            List[str]: Список названий шаблонов без расширения
        """
        if not self.templates_dir.exists():
            logger.warning(f"Templates directory does not exist: {self.templates_dir}")
            return []

        templates = []
        for template_file in self.templates_dir.glob("*.hbs"):
            templates.append(template_file.stem)

        logger.info(f"Found templates: {templates}")
        return templates

    def load_template(self, template_name: str) -> str | None:
        """
        Загрузить содержимое шаблона по названию

        Args:
            template_name: Название шаблона без расширения

        Returns:
            Optional[str]: Содержимое шаблона или None если не найден
        """
        template_path = self.templates_dir / f"{template_name}.hbs"

        if not template_path.exists():
            logger.error(f"Template not found: {template_path}")
            return None

        try:
            content = template_path.read_text(encoding='utf-8')
            logger.info(f"Loaded template: {template_name}")
            return content
        except Exception as e:
            logger.error(f"Error reading template {template_name}: {e}")
            return None

    def get_template_descriptions(self) -> dict[str, str]:
        """
        Получить описания всех доступных шаблонов

        Returns:
            Dict[str, str]: Словарь {название: описание}
        """
        descriptions = {
            "code-review": "Детальный анализ кода с рекомендациями по улучшению",
            "security-audit": "Анализ безопасности кода и поиск уязвимостей",
            "documentation": "Генерация технической документации проекта",
            "refactoring": "Анализ кода для рефакторинга и оптимизации",
            "migration-guide": "Помощь в миграции между версиями/технологиями",
            "api-documentation": "Документирование API и интерфейсов",
            "performance-analysis": "Анализ производительности и оптимизации"
        }

        # Возвращаем только описания для существующих шаблонов
        available = self.get_available_templates()
        return {name: descriptions.get(name, "Пользовательский шаблон")
                for name in available}

    def get_file_type_from_template(self, template_name: str, is_analyze: bool = False) -> str:
        """
        Определить тип файла по названию шаблона

        Args:
            template_name: Название шаблона
            is_analyze: Если True, то это анализ фильтров

        Returns:
            str: Тип файла для использования в названии
        """
        if is_analyze:
            return "filters"

        type_mapping = {
            "code-review": "review",
            "security-audit": "security",
            "documentation": "docs",
            "refactoring": "refactor",
            "migration-guide": "migration",
            "api-documentation": "api",
            "performance-analysis": "performance",
            "custom": "code",
            "default": "code"
        }

        return type_mapping.get(template_name, "code")

    def validate_template_name(self, template_name: str) -> bool:
        """
        Проверить существование шаблона

        Args:
            template_name: Название шаблона

        Returns:
            bool: True если шаблон существует
        """
        return template_name in self.get_available_templates()

    def get_templates_info(self, show_content: bool = False) -> str:
        """
        Получить информацию о доступных шаблонах

        Args:
            show_content: Показать содержимое шаблонов

        Returns:
            str: Форматированная информация о шаблонах
        """
        if not self.templates_dir.exists():
            return "❌ Папка с шаблонами не найдена"

        # Краткая информация о шаблонах - только суть
        templates_info = {
            "code-review.hbs": {
                "name": "🔍 Code Review",
                "purpose": "Анализ качества кода, стандартов и потенциальных проблем",
                "template_name": "code-review"
            },
            "security-audit.hbs": {
                "name": "🔒 Security Audit",
                "purpose": "Поиск уязвимостей OWASP Top 10 и проблем безопасности",
                "template_name": "security-audit"
            },
            "documentation.hbs": {
                "name": "📖 Documentation",
                "purpose": "Автоматическая генерация технической документации",
                "template_name": "documentation"
            },
            "refactoring.hbs": {
                "name": "🔄 Refactoring",
                "purpose": "Анализ кода для рефакторинга и улучшения архитектуры",
                "template_name": "refactoring"
            },
            "migration-guide.hbs": {
                "name": "🚀 Migration Guide",
                "purpose": "План миграции на новые технологии с оценкой рисков",
                "template_name": "migration-guide"
            },
            "api-documentation.hbs": {
                "name": "📡 API Documentation",
                "purpose": "Полная документация API с примерами использования",
                "template_name": "api-documentation"
            },
            "performance-analysis.hbs": {
                "name": "⚡ Performance Analysis",
                "purpose": "Анализ производительности и оптимизации кода",
                "template_name": "performance-analysis"
            }
        }

        # Проверяем какие шаблоны реально существуют
        available_templates = {}
        for template_file, info in templates_info.items():
            template_path = self.templates_dir / template_file
            if template_path.exists():
                available_templates[template_file] = info

        if not available_templates:
            return "❌ Шаблоны не найдены в папке templates"

        # Формируем краткий ответ
        response = "# 🎯 Доступные шаблоны анализа кода\n\n"

        # Краткий список с назначением
        for template_file, info in available_templates.items():
            response += f"**`{info['template_name']}`** - {info['name']}\n"
            response += f"└─ {info['purpose']}\n\n"

        # Пример использования
        response += "## 📋 Использование\n"
        response += "```json\n"
        response += '{\n  "template_name": "documentation",\n  "path": "/path/to/project",\n  "include_patterns": ["*.py", "*.md"]\n}\n'
        response += "```\n\n"

        # Показать содержимое если запрошено
        if show_content:
            response += "## 📄 Содержимое шаблонов\n\n"
            for template_file, info in available_templates.items():
                template_path = self.templates_dir / template_file
                try:
                    content = template_path.read_text(encoding='utf-8')
                    response += f"### {info['name']}\n"
                    response += f"```handlebars\n{content[:300]}...\n```\n\n"
                except Exception as e:
                    logger.warning(f"Could not read template {template_file}: {e}")

        response += f"📍 **Всего:** {len(available_templates)} шаблонов"

        return response


# Глобальный экземпляр убран - используем DI контейнер для получения экземпляра
