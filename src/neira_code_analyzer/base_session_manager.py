"""
Базовый менеджер сессий для устранения дублирования кода

АРХИТЕКТУРНОЕ УЛУЧШЕНИЕ: Создан для унификации управления сессиями
между различными типами анализа (код, документация, и т.д.)
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

@dataclass
class BaseSessionState(ABC):
    """Базовое состояние сессии - должно быть унаследовано конкретными типами"""
    session_id: str
    project_path: str
    created_at: str
    updated_at: str
    status: str  # 'active', 'completed', 'error', 'paused'
    session_type: str  # 'analysis', 'docs', 'refactoring', etc.
    
    def __post_init__(self):
        """Инициализация базовых полей"""
        if not self.session_id:
            self.session_id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

class BaseSessionManager(ABC):
    """
    Базовый менеджер сессий с общей логикой
    
    АРХИТЕКТУРНОЕ УЛУЧШЕНИЕ: Устраняет дублирование кода между
    различными типами менеджеров сессий (анализ, документация, и т.д.)
    """
    
    def __init__(self, session_type: str):
        self.session_type = session_type
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
    @abstractmethod
    def create_new_session(self, project_path: Path, **kwargs) -> BaseSessionState:
        """Создает новую сессию - должно быть реализовано в наследниках"""
        pass
    
    @abstractmethod
    def _deserialize_session(self, data: Dict[str, Any]) -> BaseSessionState:
        """Десериализует данные сессии - должно быть реализовано в наследниках"""
        pass
    
    def get_session_file_path(self, project_path: Path) -> Path:
        """Получает путь к файлу сессии"""
        neira_dir = project_path / ".neira"
        neira_dir.mkdir(exist_ok=True)
        return neira_dir / f"{self.session_type}_session.json"
    
    def load_session(self, project_path: Path) -> Optional[BaseSessionState]:
        """
        Загружает существующую сессию из файла
        
        Args:
            project_path: Путь к проекту
            
        Returns:
            BaseSessionState или None если сессия не найдена
        """
        session_file = self.get_session_file_path(project_path)
        
        if not session_file.exists():
            self.logger.debug(f"Файл сессии не найден: {session_file}")
            return None
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Проверяем тип сессии
            if session_data.get('session_type') != self.session_type:
                self.logger.warning(f"Неверный тип сессии в файле: {session_data.get('session_type')} != {self.session_type}")
                return None
            
            session_state = self._deserialize_session(session_data)
            self.logger.info(f"✅ Загружена сессия {self.session_type}: {session_state.session_id}")
            return session_state
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки сессии {self.session_type}: {e}")
            return None
    
    def save_session(self, project_path: Path, session_state: BaseSessionState) -> bool:
        """
        Сохраняет состояние сессии в файл
        
        Args:
            project_path: Путь к проекту
            session_state: Состояние сессии для сохранения
            
        Returns:
            bool: True если сохранение успешно
        """
        try:
            # Обновляем время последнего изменения
            session_state.updated_at = datetime.now().isoformat()
            
            session_file = self.get_session_file_path(project_path)
            
            # Создаем директорию если не существует
            session_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Сериализуем состояние в JSON
            session_data = asdict(session_state)
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"✅ Сессия {self.session_type} сохранена: {session_state.session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения сессии {self.session_type}: {e}")
            return False
    
    def delete_session(self, project_path: Path) -> bool:
        """
        Удаляет файл сессии
        
        Args:
            project_path: Путь к проекту
            
        Returns:
            bool: True если удаление успешно
        """
        try:
            session_file = self.get_session_file_path(project_path)
            
            if session_file.exists():
                session_file.unlink()
                self.logger.info(f"🗑️ Сессия {self.session_type} удалена")
                return True
            else:
                self.logger.debug(f"Файл сессии {self.session_type} не существует")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка удаления сессии {self.session_type}: {e}")
            return False
    
    def get_session_info(self, project_path: Path) -> Dict[str, Any]:
        """
        Получает информацию о сессии без полной загрузки
        
        Args:
            project_path: Путь к проекту
            
        Returns:
            Dict с базовой информацией о сессии
        """
        session_file = self.get_session_file_path(project_path)
        
        if not session_file.exists():
            return {
                "exists": False,
                "session_type": self.session_type
            }
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            return {
                "exists": True,
                "session_type": session_data.get('session_type'),
                "session_id": session_data.get('session_id'),
                "status": session_data.get('status'),
                "created_at": session_data.get('created_at'),
                "updated_at": session_data.get('updated_at')
            }
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения информации о сессии: {e}")
            return {
                "exists": False,
                "error": str(e),
                "session_type": self.session_type
            }
    
    def list_all_sessions(self, project_path: Path) -> List[Dict[str, Any]]:
        """
        Получает список всех сессий в проекте
        
        Args:
            project_path: Путь к проекту
            
        Returns:
            List[Dict]: Список информации о всех сессиях
        """
        neira_dir = project_path / ".neira"
        
        if not neira_dir.exists():
            return []
        
        sessions = []
        
        try:
            # Ищем все файлы сессий
            for session_file in neira_dir.glob("*_session.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    sessions.append({
                        "file": session_file.name,
                        "session_type": session_data.get('session_type'),
                        "session_id": session_data.get('session_id'),
                        "status": session_data.get('status'),
                        "created_at": session_data.get('created_at'),
                        "updated_at": session_data.get('updated_at')
                    })
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Ошибка чтения сессии {session_file}: {e}")
                    
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения списка сессий: {e}")
        
        return sessions
    
    def cleanup_old_sessions(self, project_path: Path, max_age_days: int = 30) -> int:
        """
        Очищает старые сессии
        
        Args:
            project_path: Путь к проекту
            max_age_days: Максимальный возраст сессии в днях
            
        Returns:
            int: Количество удаленных сессий
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        deleted_count = 0
        
        try:
            all_sessions = self.list_all_sessions(project_path)
            
            for session_info in all_sessions:
                try:
                    updated_at = datetime.fromisoformat(session_info.get('updated_at', ''))
                    
                    if updated_at < cutoff_date:
                        session_file = project_path / ".neira" / session_info['file']
                        session_file.unlink()
                        deleted_count += 1
                        self.logger.info(f"🗑️ Удалена старая сессия: {session_info['session_id']}")
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Ошибка удаления старой сессии: {e}")
                    
        except Exception as e:
            self.logger.error(f"❌ Ошибка очистки старых сессий: {e}")
        
        return deleted_count 