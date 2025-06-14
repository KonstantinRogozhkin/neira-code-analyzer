#!/usr/bin/env python3
"""
Тестовый скрипт для проверки BaseActionExecutor

Проверяет устранение дублирования кода между ActionExecutor и AnalysisActionExecutor
"""

import tempfile
from pathlib import Path
import sys
import os

# Добавляем src в PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from neira_code_analyzer.base_action_executor import BaseActionExecutor, BaseExecutionSummary
from neira_code_analyzer.analysis_action_executor import AnalysisActionExecutor

def test_base_action_executor_inheritance():
    """Тестирует наследование от BaseActionExecutor"""
    
    print("🧪 Тестируем наследование от BaseActionExecutor...")
    
    # Создаем экземпляр
    executor = AnalysisActionExecutor()
    
    # Проверяем что это экземпляр базового класса
    if isinstance(executor, BaseActionExecutor):
        print("✅ AnalysisActionExecutor наследуется от BaseActionExecutor")
    else:
        print("❌ Ошибка наследования")
        return False
    
    # Проверяем наличие базовых методов
    base_methods = [
        '_validate_file_path',
        '_backup_file_to_backup_dir',
        '_create_file_safely',
        '_update_file_safely',
        'rollback_changes'
    ]
    
    for method_name in base_methods:
        if hasattr(executor, method_name):
            print(f"✅ Метод {method_name} доступен")
        else:
            print(f"❌ Метод {method_name} отсутствует")
            return False
    
    return True

def test_path_validation():
    """Тестирует валидацию путей"""
    
    print("\n🧪 Тестируем валидацию путей...")
    
    executor = AnalysisActionExecutor()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Безопасный путь
        safe_file = temp_path / "safe_file.txt"
        safe_file.touch()
        
        if executor._validate_file_path(safe_file, temp_path):
            print("✅ Безопасный путь прошел валидацию")
        else:
            print("❌ Безопасный путь не прошел валидацию")
            return False
        
        # Небезопасный путь (path traversal)
        unsafe_file = temp_path / ".." / "unsafe_file.txt"
        
        if not executor._validate_file_path(unsafe_file, temp_path):
            print("✅ Небезопасный путь заблокирован")
        else:
            print("❌ Небезопасный путь пропущен")
            return False
    
    return True

def test_backup_functionality():
    """Тестирует функциональность резервного копирования"""
    
    print("\n🧪 Тестируем функциональность backup...")
    
    executor = AnalysisActionExecutor()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Создаем backup директорию
        backup_dir = temp_path / "backups" / "test_session"
        backup_dir.mkdir(parents=True)
        executor.backup_dir = backup_dir
        
        # Создаем тестовый файл
        test_file = temp_path / "test_file.txt"
        test_content = "Это тестовый файл"
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Тестируем backup
        if executor._backup_file_to_backup_dir(test_file):
            print("✅ Backup файла создан")
            
            # Проверяем что backup существует
            backup_files = list(backup_dir.rglob("*"))
            if backup_files:
                print(f"✅ Backup файл найден: {backup_files[0]}")
                
                # Проверяем содержимое
                with open(backup_files[0], 'r') as f:
                    backup_content = f.read()
                
                if backup_content == test_content:
                    print("✅ Содержимое backup файла корректно")
                else:
                    print("❌ Содержимое backup файла некорректно")
                    return False
            else:
                print("❌ Backup файл не найден")
                return False
        else:
            print("❌ Ошибка создания backup")
            return False
    
    return True

def test_file_operations():
    """Тестирует базовые файловые операции"""
    
    print("\n🧪 Тестируем базовые файловые операции...")
    
    executor = AnalysisActionExecutor()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Настраиваем backup
        backup_dir = temp_path / "backups" / "test_session"
        backup_dir.mkdir(parents=True)
        executor.backup_dir = backup_dir
        
        # Создаем сводку
        summary = BaseExecutionSummary(
            actions_executed=0,
            actions_succeeded=0,
            actions_failed=0,
            files_modified=[],
            files_created=[],
            files_backed_up=[],
            errors=[],
            duration_seconds=0.0
        )
        
        # Тестируем создание файла
        new_file = temp_path / "new_file.txt"
        content = "Новый файл"
        
        if executor._create_file_safely(new_file, content, temp_path, summary):
            print("✅ Файл создан безопасно")
            
            if new_file.exists():
                print("✅ Файл существует")
                
                with open(new_file, 'r') as f:
                    if f.read() == content:
                        print("✅ Содержимое файла корректно")
                    else:
                        print("❌ Содержимое файла некорректно")
                        return False
            else:
                print("❌ Файл не создан")
                return False
        else:
            print("❌ Ошибка создания файла")
            return False
        
        # Тестируем обновление файла
        updated_content = "Обновленный файл"
        
        if executor._update_file_safely(new_file, updated_content, temp_path, summary):
            print("✅ Файл обновлен безопасно")
            
            with open(new_file, 'r') as f:
                if f.read() == updated_content:
                    print("✅ Обновленное содержимое корректно")
                else:
                    print("❌ Обновленное содержимое некорректно")
                    return False
            
            # Проверяем что backup создан
            if len(summary.files_backed_up) > 0:
                print("✅ Backup создан при обновлении")
            else:
                print("❌ Backup не создан")
                return False
        else:
            print("❌ Ошибка обновления файла")
            return False
    
    return True

def test_rollback_functionality():
    """Тестирует функциональность отката"""
    
    print("\n🧪 Тестируем функциональность отката...")
    
    executor = AnalysisActionExecutor()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Создаем тестовый файл
        test_file = temp_path / "rollback_test.txt"
        original_content = "Оригинальное содержимое"
        with open(test_file, 'w') as f:
            f.write(original_content)
        
        # Настраиваем backup
        session_id = "test_rollback_session"
        backup_dir = temp_path / ".neira" / "backups" / session_id
        backup_dir.mkdir(parents=True)
        executor.backup_dir = backup_dir
        
        # Создаем backup
        executor._backup_file_to_backup_dir(test_file)
        
        # Изменяем файл
        modified_content = "Измененное содержимое"
        with open(test_file, 'w') as f:
            f.write(modified_content)
        
        # Проверяем что файл изменен
        with open(test_file, 'r') as f:
            if f.read() == modified_content:
                print("✅ Файл успешно изменен")
            else:
                print("❌ Файл не изменен")
                return False
        
        # Откатываем изменения
        if executor.rollback_changes(session_id, temp_path):
            print("✅ Откат выполнен")
            
            # Проверяем что файл восстановлен
            with open(test_file, 'r') as f:
                restored_content = f.read()
                
            if restored_content == original_content:
                print("✅ Файл восстановлен корректно")
            else:
                print(f"❌ Файл не восстановлен. Ожидалось: '{original_content}', получено: '{restored_content}'")
                return False
        else:
            print("❌ Ошибка отката")
            return False
    
    return True

if __name__ == "__main__":
    print("🚀 Тестирование BaseActionExecutor")
    print("=" * 60)
    
    # Запускаем тесты
    test1_result = test_base_action_executor_inheritance()
    test2_result = test_path_validation()
    test3_result = test_backup_functionality()
    test4_result = test_file_operations()
    test5_result = test_rollback_functionality()
    
    print("\n" + "=" * 60)
    print("📊 Результаты тестирования BaseActionExecutor:")
    print(f"  - Наследование: {'✅ ПРОЙДЕН' if test1_result else '❌ ПРОВАЛЕН'}")
    print(f"  - Валидация путей: {'✅ ПРОЙДЕН' if test2_result else '❌ ПРОВАЛЕН'}")
    print(f"  - Backup функциональность: {'✅ ПРОЙДЕН' if test3_result else '❌ ПРОВАЛЕН'}")
    print(f"  - Файловые операции: {'✅ ПРОЙДЕН' if test4_result else '❌ ПРОВАЛЕН'}")
    print(f"  - Откат изменений: {'✅ ПРОЙДЕН' if test5_result else '❌ ПРОВАЛЕН'}")
    
    all_tests_passed = all([test1_result, test2_result, test3_result, test4_result, test5_result])
    
    if all_tests_passed:
        print("\n🎉 Все тесты BaseActionExecutor пройдены успешно!")
        print("✨ Устранение дублирования кода работает корректно!")
        sys.exit(0)
    else:
        print("\n💥 Некоторые тесты провалены!")
        sys.exit(1) 