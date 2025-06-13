"""
Тест для параметра session_id
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile
import shutil

from src.neira_code_analyzer.analysis_agent import AnalysisAgent
from src.neira_code_analyzer.analysis_session_manager import AnalysisSessionState


class TestSessionIdParameter:
    """Тесты для проверки session_id параметра"""
    
    @pytest.fixture
    def temp_project_path(self):
        """Создаем временную папку для тестов"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def analysis_agent(self):
        """Создаем экземпляр AnalysisAgent для тестов"""
        agent = AnalysisAgent()
        return agent
    
    def test_session_id_parameter_exists(self, analysis_agent):
        """Проверяем что параметр session_id существует в сигнатуре метода"""
        import inspect
        
        signature = inspect.signature(analysis_agent.analyze_code)
        assert 'session_id' in signature.parameters
        assert signature.parameters['session_id'].default == ""
    
    @pytest.mark.asyncio
    async def test_session_id_provided_continues_session(self, analysis_agent, temp_project_path):
        """Тест что session_id продолжает существующую сессию"""
        
        # Создаем существующую сессию
        existing_session = AnalysisSessionState(
            session_id="test_session_123",
            project_path=str(temp_project_path),
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            status="active",
            session_type="analysis",
            params={},
            ai_model="gemini-2.5-pro-preview-06-05",
            template_name="code-review"
        )
        
        # Мокаем методы session_manager
        with patch.object(analysis_agent.session_manager, 'load_session') as mock_load, \
             patch.object(analysis_agent, '_start_new_analysis_session') as mock_start_new, \
             patch.object(analysis_agent, '_continue_analysis_session') as mock_continue:
            
            # Настраиваем моки
            mock_load.return_value = existing_session
            mock_start_new.return_value = "New session created"
            mock_continue.return_value = "Continuing existing session"
            
            # Тест: С session_id должен продолжить существующую сессию
            result = await analysis_agent.analyze_code(
                path=str(temp_project_path),
                session_id="test_session_123",
                user_query="Продолжи анализ"
            )
            
            # Проверяем что была загружена существующая сессия
            mock_load.assert_called_once()
            mock_continue.assert_called_once()
            mock_start_new.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_session_id_empty_creates_new_session(self, analysis_agent, temp_project_path):
        """Тест что пустой session_id создает новую сессию"""
        
        with patch.object(analysis_agent.session_manager, 'load_session') as mock_load, \
             patch.object(analysis_agent, '_start_new_analysis_session') as mock_start_new, \
             patch.object(analysis_agent, '_continue_analysis_session') as mock_continue:
            
            mock_start_new.return_value = "New session created"
            
            # Тест с пустым session_id
            result = await analysis_agent.analyze_code(
                path=str(temp_project_path),
                session_id="",
                user_query="Новый анализ"
            )
            
            # НЕ должен загружать сессию, должен создать новую
            mock_load.assert_not_called()
            mock_start_new.assert_called_once()
            mock_continue.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_session_id_not_provided_creates_new_session(self, analysis_agent, temp_project_path):
        """Тест что когда session_id не передан, создается новая сессия"""
        
        with patch.object(analysis_agent.session_manager, 'load_session') as mock_load, \
             patch.object(analysis_agent, '_start_new_analysis_session') as mock_start_new, \
             patch.object(analysis_agent, '_continue_analysis_session') as mock_continue:
            
            mock_start_new.return_value = "New session created"
            
            # Тест без session_id (по умолчанию)
            result = await analysis_agent.analyze_code(
                path=str(temp_project_path),
                user_query="Новый анализ"
            )
            
            # НЕ должен загружать сессию, должен создать новую
            mock_load.assert_not_called()
            mock_start_new.assert_called_once()
            mock_continue.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_session_id_not_found_creates_new_session(self, analysis_agent, temp_project_path):
        """Тест что если сессия с указанным ID не найдена, создается новая"""
        
        # Создаем существующую сессию с другим ID
        existing_session = AnalysisSessionState(
            session_id="different_session_456",
            project_path=str(temp_project_path),
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            status="active",
            session_type="analysis",
            params={},
            ai_model="gemini-2.5-pro-preview-06-05",
            template_name="code-review"
        )
        
        with patch.object(analysis_agent.session_manager, 'load_session') as mock_load, \
             patch.object(analysis_agent, '_start_new_analysis_session') as mock_start_new, \
             patch.object(analysis_agent, '_continue_analysis_session') as mock_continue:
            
            # Сессия существует, но с другим ID
            mock_load.return_value = existing_session
            mock_start_new.return_value = "New session created"
            
            # Пытаемся продолжить сессию с неправильным ID
            result = await analysis_agent.analyze_code(
                path=str(temp_project_path),
                session_id="nonexistent_session_789",
                user_query="Продолжи анализ"
            )
            
            # Должен загрузить сессию, но не найти совпадение и создать новую
            mock_load.assert_called_once()
            mock_start_new.assert_called_once()
            mock_continue.assert_not_called() 