#!/usr/bin/env python3
"""
Тестовый скрипт для проверки улучшений производительности

Проверяет оптимизацию двойного обхода файловой системы и фильтрацию файлов
"""

import time
import tempfile
from pathlib import Path
import sys
import os

# Добавляем src в PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from neira_code_analyzer.context_generator import ContextGenerator
from neira_code_analyzer.filters import create_file_size_filter

def create_test_project(base_path: Path, num_files: int = 50) -> Path:
    """Создает тестовый проект с заданным количеством файлов"""
    
    project_path = base_path / "test_project"
    project_path.mkdir(exist_ok=True)
    
    # Создаем Python файлы разного размера
    for i in range(num_files):
        file_path = project_path / f"module_{i}.py"
        
        # Создаем файлы разного размера
        if i < 10:  # Маленькие файлы
            content = f"""
def function_{i}():
    '''Маленький файл {i}'''
    return {i}
"""
        elif i < 30:  # Средние файлы
            content = f"""
def function_{i}():
    '''Средний файл {i}'''
    # Добавляем больше содержимого
""" + "\n".join([f"    # Comment line {j}" for j in range(50)])
        else:  # Большие файлы
            content = f"""
def function_{i}():
    '''Большой файл {i}'''
    # Генерируем много кода
""" + "\n".join([f"    # Large comment line {j} with more text content" for j in range(200)])
        
        with open(file_path, 'w') as f:
            f.write(content)
    
    # Создаем несколько подпапок
    for subdir in ['utils', 'tests', 'docs']:
        subdir_path = project_path / subdir
        subdir_path.mkdir(exist_ok=True)
        
        for i in range(5):
            file_path = subdir_path / f"{subdir}_file_{i}.py"
            with open(file_path, 'w') as f:
                f.write(f"# {subdir} file {i}\n")
    
    return project_path

def test_file_size_filtering():
    """Тестирует активацию фильтрации по размеру файлов"""
    
    print("🧪 Тестируем фильтрацию по размеру файлов...")
    
    # Создаем фильтр
    filter_obj = create_file_size_filter(max_size_kb=1)  # 1KB лимит
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = create_test_project(temp_path, num_files=20)
        
        # Собираем все файлы
        all_files = list(project_path.rglob("*.py"))
        print(f"📁 Создано {len(all_files)} файлов")
        
        # Применяем фильтр
        remaining_files, excluded_files = filter_obj.filter_file_list(all_files)
        
        print(f"✅ Оставлено файлов: {len(remaining_files)}")
        print(f"🚫 Исключено файлов: {len(excluded_files)}")
        
        # Получаем статистику
        stats = filter_obj.get_stats(all_files)
        print(f"📊 Статистика:")
        print(f"  - Общий размер: {stats['total_size_mb']:.2f}MB")
        print(f"  - Больших файлов: {stats['large_files_count']}")
        print(f"  - Размер больших файлов: {stats['large_files_size_mb']:.2f}MB")
        print(f"  - Самый большой файл: {stats['largest_file']}")
        
        return len(excluded_files) > 0  # Успех если что-то исключено

def test_context_generation_performance():
    """Тестирует производительность генерации контекста"""
    
    print("\n🧪 Тестируем производительность генерации контекста...")
    
    generator = ContextGenerator()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = create_test_project(temp_path, num_files=30)
        
        print(f"📁 Тестовый проект: {project_path}")
        
        # Тестируем новую оптимизированную версию
        start_time = time.time()
        
        try:
            result, saved_file = generator.generate_context({
                "path": str(project_path),
                "include_patterns": ["*.py"],
                "exclude_patterns": ["tests/**"],
                "line_numbers": False,
                "encoding": "cl100k"
            })
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"⏱️ Время генерации: {duration:.2f} секунд")
            print(f"📊 Размер результата: {len(result)} символов")
            
            # Проверяем что результат содержит код
            if "def function_" in result and len(result) > 1000:
                print("✅ Контекст сгенерирован корректно")
                return True, duration
            else:
                print("❌ Контекст сгенерирован некорректно")
                return False, duration
                
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            print(f"❌ Ошибка генерации контекста: {e}")
            return False, duration

def test_lightweight_validation():
    """Тестирует легковесную валидацию проекта"""
    
    print("\n🧪 Тестируем легковесную валидацию...")
    
    generator = ContextGenerator()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = create_test_project(temp_path, num_files=100)
        
        print(f"📁 Большой тестовый проект: {project_path}")
        
        # Тестируем легковесную валидацию
        start_time = time.time()
        
        try:
            generator._validate_project_size_lightweight(str(project_path))
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"⚡ Время легковесной валидации: {duration:.3f} секунд")
            print("✅ Легковесная валидация завершена успешно")
            
            return True, duration
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            print(f"❌ Ошибка валидации: {e}")
            return False, duration

def test_apply_file_size_filtering():
    """Тестирует применение фильтрации размера файлов"""
    
    print("\n🧪 Тестируем применение фильтрации в _apply_file_size_filtering...")
    
    generator = ContextGenerator()
    filter_obj = create_file_size_filter(max_size_kb=2)  # 2KB лимит
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = create_test_project(temp_path, num_files=25)
        
        try:
            # Вызываем метод фильтрации
            generator._apply_file_size_filtering(None, filter_obj, str(project_path))
            print("✅ Фильтрация применена успешно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка применения фильтрации: {e}")
            return False

if __name__ == "__main__":
    print("🚀 Тестирование улучшений производительности")
    print("=" * 70)
    
    # Запускаем тесты
    test1_result = test_file_size_filtering()
    test2_result, context_duration = test_context_generation_performance()
    test3_result, validation_duration = test_lightweight_validation()
    test4_result = test_apply_file_size_filtering()
    
    print("\n" + "=" * 70)
    print("📊 Результаты тестирования производительности:")
    print(f"  - Фильтрация по размеру: {'✅ РАБОТАЕТ' if test1_result else '❌ НЕ РАБОТАЕТ'}")
    print(f"  - Генерация контекста: {'✅ РАБОТАЕТ' if test2_result else '❌ НЕ РАБОТАЕТ'} ({context_duration:.2f}с)")
    print(f"  - Легковесная валидация: {'✅ РАБОТАЕТ' if test3_result else '❌ НЕ РАБОТАЕТ'} ({validation_duration:.3f}с)")
    print(f"  - Применение фильтрации: {'✅ РАБОТАЕТ' if test4_result else '❌ НЕ РАБОТАЕТ'}")
    
    # Анализ производительности
    print(f"\n⚡ Анализ производительности:")
    if validation_duration < 0.1:
        print(f"  ✅ Легковесная валидация очень быстрая: {validation_duration:.3f}с")
    elif validation_duration < 0.5:
        print(f"  ✅ Легковесная валидация достаточно быстрая: {validation_duration:.3f}с")
    else:
        print(f"  ⚠️ Легковесная валидация медленная: {validation_duration:.3f}с")
    
    if context_duration < 5.0:
        print(f"  ✅ Генерация контекста быстрая: {context_duration:.2f}с")
    elif context_duration < 15.0:
        print(f"  ✅ Генерация контекста приемлемая: {context_duration:.2f}с")
    else:
        print(f"  ⚠️ Генерация контекста медленная: {context_duration:.2f}с")
    
    # Итоговый результат
    all_tests_passed = test1_result and test2_result and test3_result and test4_result
    
    if all_tests_passed:
        print(f"\n🎉 Все тесты производительности пройдены успешно!")
        print(f"✨ Исправления работают корректно!")
        sys.exit(0)
    else:
        print(f"\n💥 Некоторые тесты производительности провалены!")
        sys.exit(1) 