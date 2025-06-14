#!/usr/bin/env python3
"""
Тестовый скрипт для проверки AST-парсера в AnalysisActionExecutor

Проверяет корректность замены regex на AST-парсер
"""

import tempfile
from pathlib import Path
import sys
import os

# Добавляем src в PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from neira_code_analyzer.analysis_action_executor import AnalysisActionExecutor, AnalysisExecutionSummary

def test_ast_parser():
    """Тестирует AST-парсер для рефакторинга функций"""
    
    print("🧪 Тестируем AST-парсер...")
    
    # Создаем тестовый код
    test_code = '''
def old_function(x, y):
    """Старая функция"""
    return x + y

def another_function():
    pass
'''

    new_function = '''
def old_function(x: int, y: int) -> int:
    """Обновленная функция с типами"""
    return x + y
'''

    # Создаем экземпляр executor
    executor = AnalysisActionExecutor()
    
    # Создаем временный файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_path = Path(f.name)

    try:
        print(f"📁 Тестовый файл: {temp_path}")
        
        # Создаем сводку
        summary = AnalysisExecutionSummary(
            actions_executed=0,
            actions_succeeded=0,
            actions_failed=0,
            files_modified=[],
            files_created=[],
            files_backed_up=[],
            errors=[],
            duration_seconds=0.0
        )
        
        # Проверяем новый AST-метод
        print("🔄 Применяем AST-рефакторинг...")
        result = executor._refactor_python_function_with_ast(
            test_code, temp_path, 'old_function', new_function, summary
        )
        
        if result:
            print("✅ AST-рефакторинг выполнен успешно!")
            
            # Читаем результат
            with open(temp_path, 'r') as f:
                result_code = f.read()
            
            print("📝 Результат рефакторинга:")
            print("=" * 50)
            print(result_code)
            print("=" * 50)
            
            # Проверяем что изменения корректны
            if "x: int, y: int" in result_code and "-> int:" in result_code:
                print("✅ Типы добавлены корректно")
            else:
                print("❌ Ошибка: типы не найдены в результате")
                return False
                
            if "another_function" in result_code:
                print("✅ Другие функции сохранены")
            else:
                print("❌ Ошибка: другие функции потеряны")
                return False
                
        else:
            print("❌ AST-рефакторинг завершился с ошибкой")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False
    finally:
        temp_path.unlink()
        
    return True

def test_ast_parser_with_decorators():
    """Тестирует AST-парсер с декораторами"""
    
    print("\n🧪 Тестируем AST-парсер с декораторами...")
    
    # Тестовый код с декораторами
    test_code = '''
@property
@lru_cache(maxsize=128)
def decorated_function(self, value):
    """Функция с декораторами"""
    return self._process(value)

def normal_function():
    pass
'''

    new_function = '''
@property
@lru_cache(maxsize=128)
def decorated_function(self, value: str) -> str:
    """Обновленная функция с декораторами и типами"""
    return self._process(value)
'''

    executor = AnalysisActionExecutor()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_path = Path(f.name)

    try:
        summary = AnalysisExecutionSummary(0, 0, 0, [], [], [], [], 0.0)
        
        result = executor._refactor_python_function_with_ast(
            test_code, temp_path, 'decorated_function', new_function, summary
        )
        
        if result:
            print("✅ Рефакторинг с декораторами выполнен успешно!")
            
            with open(temp_path, 'r') as f:
                result_code = f.read()
            
            print("📝 Результат с декораторами:")
            print("=" * 50)
            print(result_code)
            print("=" * 50)
            
            # Проверяем сохранение декораторов
            if "@property" in result_code and "@lru_cache" in result_code:
                print("✅ Декораторы сохранены")
            else:
                print("❌ Ошибка: декораторы потеряны")
                return False
                
        else:
            print("❌ Рефакторинг с декораторами завершился с ошибкой")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования декораторов: {e}")
        return False
    finally:
        temp_path.unlink()
        
    return True

if __name__ == "__main__":
    print("🚀 Тестирование AST-парсера AnalysisActionExecutor")
    print("=" * 60)
    
    # Запускаем тесты
    test1_result = test_ast_parser()
    test2_result = test_ast_parser_with_decorators()
    
    print("\n" + "=" * 60)
    print("📊 Результаты тестирования:")
    print(f"  - Базовый AST-рефакторинг: {'✅ ПРОЙДЕН' if test1_result else '❌ ПРОВАЛЕН'}")
    print(f"  - AST с декораторами: {'✅ ПРОЙДЕН' if test2_result else '❌ ПРОВАЛЕН'}")
    
    if test1_result and test2_result:
        print("\n🎉 Все тесты AST-парсера пройдены успешно!")
        sys.exit(0)
    else:
        print("\n💥 Некоторые тесты провалены!")
        sys.exit(1) 