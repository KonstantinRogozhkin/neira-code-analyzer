"""
AnalysisSessionManager - управление состоянием сессии анализа кода

АРХИТЕКТУРНОЕ УЛУЧШЕНИЕ: Теперь наследуется от BaseSessionManager
для устранения дублирования кода и унификации управления сессиями.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from .base_session_manager import BaseSessionManager, BaseSessionState

logger = logging.getLogger(__name__)

@dataclass
class AnalysisSessionState(BaseSessionState):
    """
    АРХИТЕКТУРНОЕ УЛУЧШЕНИЕ: Наследуется от BaseSessionState
    для унификации управления сессиями
    """
    step: int = 1
    params: Dict = None
    completed_analyses: List[Dict] = None
    ai_model: str = "gemini-2.5-pro-preview-06-05"
    template_name: str = "code-review"
    user_query: Optional[str] = None
    current_focus: Optional[str] = None  # Текущий фокус анализа
    analysis_history: List[Dict] = None  # История запросов и ответов
    
    def __post_init__(self):
        """Инициализация значений по умолчанию"""
        super().__post_init__()
        if not self.session_type:
            self.session_type = "analysis"
        if self.params is None:
            self.params = {}
        if self.completed_analyses is None:
            self.completed_analyses = []
        if self.analysis_history is None:
            self.analysis_history = []
    
    def to_dict(self) -> Dict:
        """Конвертирует в словарь для JSON сериализации"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AnalysisSessionState':
        """Создает объект из словаря"""
        return cls(**data)

class AnalysisSessionManager(BaseSessionManager):
    """
    АРХИТЕКТУРНОЕ УЛУЧШЕНИЕ: Наследуется от BaseSessionManager
    для устранения дублирования кода
    
    Управляет состоянием сессии анализа кода с унифицированным API.
    """
    
    def __init__(self):
        super().__init__("analysis")
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _deserialize_session(self, data: Dict[str, Any]) -> AnalysisSessionState:
        """Десериализует данные сессии анализа"""
        return AnalysisSessionState.from_dict(data)
    
    def create_new_session(
        self, 
        project_path: Path, 
        params: Dict, 
        ai_model: str,
        template_name: str,
        user_query: Optional[str] = None
    ) -> AnalysisSessionState:
        """
        Создает новую сессию анализа кода
        
        Args:
            project_path: Путь к проекту
            params: Параметры анализа
            ai_model: Модель ИИ для использования
            template_name: Шаблон анализа
            user_query: Пользовательский запрос
            
        Returns:
            AnalysisSessionState: Новое состояние сессии
        """
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        timestamp = datetime.now().isoformat()
        
        session_state = AnalysisSessionState(
            session_id=session_id,
            project_path=str(project_path),
            created_at=timestamp,
            updated_at=timestamp,
            status='analyzing',
            session_type='analysis',
            step=1,
            params=params,
            completed_analyses=[],
            ai_model=ai_model,
            template_name=template_name,
            user_query=user_query,
            current_focus=user_query,
            analysis_history=[]
        )
        
        # Создаем рабочую папку для сессии
        self._ensure_session_directory(project_path)
        
        self.logger.info(f"Создана новая сессия анализа: {session_id}")
        return session_state
    
    # АРХИТЕКТУРНОЕ УЛУЧШЕНИЕ: load_session и save_session теперь наследуются от BaseSessionManager
    
    def add_analysis_interaction(
        self, 
        session_state: AnalysisSessionState, 
        user_request: str,
        ai_response: str,
        new_focus: Optional[str] = None
    ) -> AnalysisSessionState:
        """
        Добавляет новое взаимодействие в историю анализа
        
        Args:
            session_state: Текущее состояние
            user_request: Запрос пользователя
            ai_response: Ответ ИИ
            new_focus: Новый фокус анализа (опционально)
            
        Returns:
            AnalysisSessionState: Обновленное состояние
        """
        interaction = {
            "step": session_state.step,
            "timestamp": datetime.now().isoformat(),
            "user_request": user_request,
            "ai_response_summary": ai_response[:500] + "..." if len(ai_response) > 500 else ai_response,
            "focus": new_focus or session_state.current_focus
        }
        
        session_state.analysis_history.append(interaction)
        session_state.step += 1
        
        if new_focus:
            session_state.current_focus = new_focus
            
        # Обновляем статус на интерактивный после первого взаимодействия
        if session_state.status == 'analyzing':
            session_state.status = 'interactive'
        
        session_state.updated_at = datetime.now().isoformat()
        
        self.logger.info(f"Добавлено взаимодействие в сессию: шаг {session_state.step}")
        return session_state
    
    def complete_session(
        self, 
        session_state: AnalysisSessionState,
        final_analysis: Dict
    ) -> AnalysisSessionState:
        """
        Завершает сессию анализа
        
        Args:
            session_state: Текущее состояние
            final_analysis: Финальный анализ
            
        Returns:
            AnalysisSessionState: Завершенное состояние
        """
        session_state.completed_analyses.append(final_analysis)
        session_state.status = 'completed'
        session_state.updated_at = datetime.now().isoformat()
        
        self.logger.info(f"Сессия анализа завершена: {session_state.session_id}")
        return session_state
    
    def cleanup_session(self, project_path: Path) -> bool:
        """
        Очищает файлы сессии после завершения
        
        Args:
            project_path: Путь к проекту
            
        Returns:
            bool: True если очистка успешна
        """
        session_dir = self._get_session_directory(project_path)
        
        if not session_dir.exists():
            return True
        
        try:
            import shutil
            shutil.rmtree(session_dir)
            self.logger.info("Сессия анализа очищена")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки сессии анализа: {e}")
            return False
    
    def get_session_info(self, project_path: Path) -> Optional[Dict]:
        """
        Получает краткую информацию о сессии
        
        Args:
            project_path: Путь к проекту
            
        Returns:
            Dict с информацией о сессии или None
        """
        session_state = self.load_session(project_path)
        
        if not session_state:
            return None
        
        return {
            "session_id": session_state.session_id,
            "status": session_state.status,
            "step": session_state.step,
            "template": session_state.template_name,
            "current_focus": session_state.current_focus,
            "interactions": len(session_state.analysis_history),
            "created_at": session_state.created_at,
            "updated_at": session_state.updated_at
        }
    
    # АРХИТЕКТУРНОЕ УЛУЧШЕНИЕ: Методы работы с файлами теперь наследуются от BaseSessionManager
    
    def _ensure_session_directory(self, project_path: Path):
        """Создает папку сессии если её нужно (совместимость со старым кодом)"""
        # Базовый класс уже создает .neira директорию
        pass 