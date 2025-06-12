"""
Менеджер проектов и версионирования для Neira Code Analyzer

Централизованная логика работы с проектами, версиями и сохранением файлов.
"""

from typing import Tuple, Optional
from pathlib import Path
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

class ProjectManager:
    """Управление проектами и версионированием"""
    
    def __init__(self, base_analysis_path: Optional[Path] = None):
        """
        Инициализация менеджера проектов
        
        Args:
            base_analysis_path: Базовый путь для анализов. По умолчанию определяется автоматически.
        """
        if base_analysis_path is None:
            self.base_analysis_path = self._get_base_analysis_path()
        else:
            self.base_analysis_path = base_analysis_path
            
        logger.info(f"Project manager initialized with base path: {self.base_analysis_path}")

    def _get_base_analysis_path(self) -> Path:
        """
        Определить базовый путь для сохранения анализов
        
        Использует переменную окружения NEIRA_ANALYSIS_PATH или создаёт папку
        в текущем проекте/домашней директории пользователя.
        
        Returns:
            Path: Путь к папке analysis
        """
        # Попробуем получить путь из переменной окружения
        env_path = os.environ.get("NEIRA_ANALYSIS_PATH")
        if env_path:
            base_path = Path(env_path)
            logger.info(f"Using analysis path from environment: {base_path}")
            base_path.mkdir(parents=True, exist_ok=True)
            return base_path
        
        # Если не задан, попробуем найти корень проекта (где есть pyproject.toml)
        current_dir = Path(__file__).parent.parent.parent
        project_analysis_path = current_dir / "analysis"
        
        if (current_dir / "pyproject.toml").exists():
            # Мы в корне проекта neira-code-analyzer
            logger.info(f"Using project analysis path: {project_analysis_path}")
            project_analysis_path.mkdir(parents=True, exist_ok=True)
            return project_analysis_path
        
        # Если не в проекте, используем домашнюю директорию
        home_analysis_path = Path.home() / "neira-analysis"
        logger.info(f"Using home analysis path: {home_analysis_path}")
        home_analysis_path.mkdir(parents=True, exist_ok=True)
        return home_analysis_path

    def get_next_project_version(self, project_path: str) -> Tuple[Path, str]:
        """
        Определить следующую версию для проекта и создать структуру папок
        
        Создает структуру: analysis/YYYY-MM-DD/project-name/v1.N/
        Версии: 1.1, 1.2, 1.3, ... (инкремент на каждый запрос)
        
        Args:
            project_path: Путь к анализируемому проекту
            
        Returns:
            Tuple[Path, str]: Путь к папке версии и версия (например: "1.3")
        """
        # Извлекаем название проекта из пути (последний компонент)
        project_name = Path(project_path).name
        if not project_name:
            project_name = "unknown-project"
        
        # Получаем текущую дату
        today = datetime.now().strftime("%Y-%m-%d")
        date_path = self.base_analysis_path / today
        project_folder = date_path / project_name
        
        # Создаем папки проекта если не существуют
        project_folder.mkdir(parents=True, exist_ok=True)
        
        # Ищем последнюю версию во всех подпапках версий И в старых файлах
        version_numbers = []
        
        # 1. Ищем папки с паттерном v1.N в папке проекта (новая структура)
        for version_folder in project_folder.glob("v1.*"):
            if version_folder.is_dir():
                try:
                    # Извлекаем номер версии из имени папки: v1.N
                    version_part = version_folder.name.split('v1.')[1]
                    version_numbers.append(int(version_part))
                except (ValueError, IndexError):
                    continue
        
        # 2. Ищем старые файлы с паттерном project-name-v1.N.* (совместимость)
        for file_path in project_folder.glob(f"{project_name}-v1.*"):
            if file_path.is_file():
                try:
                    # Формат: project-name-v1.N.type.md
                    parts = file_path.stem.split('-v1.')
                    if len(parts) > 1:
                        # Берем часть после v1. и до следующей точки
                        version_part = parts[1].split('.')[0]
                        version_numbers.append(int(version_part))
                except (ValueError, IndexError):
                    continue
        
        # Определяем следующую версию
        if not version_numbers:
            next_version = "1.1"
        else:
            max_version = max(version_numbers)
            next_version = f"1.{max_version + 1}"
        
        # Создаем папку для новой версии
        version_folder = project_folder / f"v{next_version}"
        version_folder.mkdir(parents=True, exist_ok=True)
        
        return version_folder, next_version

    def create_versioned_path(self, project_path: str, save_to_file: str, 
                             file_type: str) -> Path:
        """
        Создать версионированный путь для сохранения файла
        
        Args:
            project_path: Путь к анализируемому проекту
            save_to_file: Желаемое имя файла (может быть относительным)
            file_type: Тип файла (для создания имени)
            
        Returns:
            Path: Полный путь для сохранения файла
        """
        # 🔒 SECURITY FIX: Валидация и нормализация путей для предотвращения path injection
        try:
            save_path = Path(save_to_file).resolve()
        except (OSError, ValueError) as e:
            logger.error(f"Invalid path provided: {save_to_file}, error: {e}")
            # Если путь некорректен, создаем безопасное имя файла
            safe_filename = "".join(c for c in save_to_file if c.isalnum() or c in ('-', '_', '.'))
            save_path = Path(safe_filename)
        
        # Если указан относительный путь, используем версионированную структуру
        if not save_path.is_absolute():
            # Создаем версионированную структуру в папке analysis
            project_folder, version = self.get_next_project_version(project_path)
            
            # 🔒 SECURITY: Санитизация имени проекта для предотвращения path traversal
            project_name = self._sanitize_filename(Path(project_path).name)
            if not project_name:
                project_name = "unknown-project"
            
            # 🔒 SECURITY: Санитизация типа файла
            safe_file_type = self._sanitize_filename(file_type)
            
            # Создаем имя файла в формате: project-name.type.md (версия в папке)
            filename = f"{project_name}.{safe_file_type}.md"
            save_path = project_folder / filename
            
            logger.info(f"Relative path: {save_to_file} saved to versioned project folder: {save_path}")
        else:
            # 🔒 SECURITY: Проверяем что абсолютный путь не ведет за пределы базовой папки анализа
            try:
                # Проверяем что resolved путь остается в пределах допустимой области
                resolved_path = save_path.resolve()
                base_resolved = self.base_analysis_path.resolve()
                
                # Если путь не в пределах нашей базовой папки анализа, перенаправляем в безопасное место
                if not str(resolved_path).startswith(str(base_resolved)):
                    logger.warning(f"Path {resolved_path} is outside analysis base {base_resolved}, redirecting to safe location")
                    # Перенаправляем в безопасную папку
                    safe_filename = self._sanitize_filename(save_path.name)
                    save_path = self.base_analysis_path / "external" / safe_filename
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                
            except (OSError, ValueError) as e:
                logger.error(f"Error resolving absolute path {save_path}: {e}")
                # Fallback к безопасному пути
                safe_filename = self._sanitize_filename(save_path.name if save_path.name else "fallback.md")
                save_path = self.base_analysis_path / "fallback" / safe_filename
                save_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Using absolute path: {save_path}")
            # Создаем директорию если не существует
            save_path.parent.mkdir(parents=True, exist_ok=True)
        
        return save_path

    def _sanitize_filename(self, filename: str) -> str:
        """
        Санитизация имени файла для предотвращения path injection
        
        Args:
            filename: Исходное имя файла
            
        Returns:
            str: Безопасное имя файла
        """
        if not filename:
            return "unknown"
        
        # Убираем потенциально опасные символы
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
        sanitized = "".join(c for c in filename if c in safe_chars)
        
        # Убираем path traversal последовательности
        sanitized = sanitized.replace("..", "").replace("./", "").replace("../", "")
        
        # Обеспечиваем что имя не пустое
        if not sanitized:
            sanitized = "sanitized"
        
        return sanitized

    def get_project_name(self, project_path: str) -> str:
        """
        Получить название проекта из пути
        
        Args:
            project_path: Путь к проекту
            
        Returns:
            str: Название проекта
        """
        project_name = Path(project_path).name
        return project_name if project_name else "unknown-project"


# Глобальный экземпляр убран - используем DI контейнер для получения экземпляра 