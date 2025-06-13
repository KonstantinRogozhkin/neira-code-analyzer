"""
Централизованный парсер для ответов ИИ.
Устраняет дублирование кода между различными агентами.
"""

import json
import re
from typing import Dict, Any, Optional
import logging

# Настройка логирования
logger = logging.getLogger(__name__)


class AIResponseParser:
    """Централизованный парсер для очистки и парсинга JSON-ответов от ИИ."""
    
    @staticmethod
    def from_json(response_text: str) -> Optional[Dict[str, Any]]:
        """
        Парсит JSON из ответа ИИ, убирая лишние символы и исправляя форматирование.
        
        Args:
            response_text: Текст ответа от ИИ
            
        Returns:
            Словарь с данными или None если парсинг не удался
        """
        if not response_text or not response_text.strip():
            logger.warning("Получен пустой ответ от ИИ")
            return None
            
        try:
            # Убираем markdown блоки если есть
            text = response_text.strip()
            if text.startswith('```json'):
                text = text[7:]  # убираем ```json
            if text.endswith('```'):
                text = text[:-3]  # убираем ```
            
            text = text.strip()
            
            # Пытаемся найти JSON блок в тексте
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                text = json_match.group()
            
            # Парсим JSON
            parsed_data = json.loads(text)
            
            # Проверяем что получили словарь
            if not isinstance(parsed_data, dict):
                logger.error(f"Ожидался словарь, получен {type(parsed_data)}")
                return None
                
            logger.debug(f"Успешно распарсен ответ ИИ: {len(parsed_data)} ключей")
            return parsed_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            logger.debug(f"Проблемный текст: {text[:200]}...")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при парсинге: {e}")
            return None
    
    @staticmethod
    def extract_actions(parsed_response: Dict[str, Any]) -> list:
        """
        Извлекает список действий из распарсенного ответа.
        
        Args:
            parsed_response: Распарсенный ответ от ИИ
            
        Returns:
            Список действий
        """
        if not parsed_response:
            return []
            
        # Пытаемся найти действия в разных возможных ключах
        actions_keys = ['actions', 'action', 'tasks', 'steps']
        
        for key in actions_keys:
            if key in parsed_response:
                actions = parsed_response[key]
                if isinstance(actions, list):
                    return actions
                elif isinstance(actions, dict):
                    return [actions]  # Если одно действие в виде словаря
                    
        logger.warning("Не найдены действия в ответе ИИ")
        return []
    
    @staticmethod
    def validate_response_structure(parsed_response: Dict[str, Any], required_keys: list = None) -> bool:
        """
        Проверяет структуру ответа ИИ на наличие обязательных ключей.
        
        Args:
            parsed_response: Распарсенный ответ
            required_keys: Список обязательных ключей
            
        Returns:
            True если структура корректна
        """
        if not parsed_response:
            return False
            
        if not required_keys:
            return True
            
        missing_keys = [key for key in required_keys if key not in parsed_response]
        
        if missing_keys:
            logger.warning(f"Отсутствуют обязательные ключи: {missing_keys}")
            return False
            
        return True 