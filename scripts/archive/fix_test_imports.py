#!/usr/bin/env python3
"""
Скрипт для исправления импортов в тестах.
Заменяет 'from src.neira_code_analyzer' на 'from neira_code_analyzer' и добавляет sys.path.
"""

import os
import re
from pathlib import Path


def fix_imports_in_file(file_path: Path) -> bool:
    """Исправляет импорты в одном файле"""
    
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Заменяем import'ы
        content = re.sub(
            r'from src\.neira_code_analyzer',
            'from neira_code_analyzer',
            content
        )
        
        # Проверяем, нужно ли добавить sys.path
        if 'from neira_code_analyzer' in content and 'sys.path.insert' not in content:
            # Ищем первый import pytest
            import_match = re.search(r'import pytest', content)
            if import_match:
                # Добавляем sys.path setup перед pytest import
                sys_path_setup = '''import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

'''
                content = content[:import_match.start()] + sys_path_setup + content[import_match.start():]
            
        # Сохраняем только если были изменения
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True
            
    except Exception as e:
        print(f"Ошибка обработки {file_path}: {e}")
        return False
        
    return False


def main():
    """Основная функция"""
    
    # Находим корень проекта
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    tests_dir = project_root / "tests"
    
    if not tests_dir.exists():
        print(f"Папка tests не найдена: {tests_dir}")
        return
        
    # Находим все Python файлы в tests
    python_files = list(tests_dir.rglob("*.py"))
    
    print(f"Найдено {len(python_files)} Python файлов в tests/")
    
    fixed_count = 0
    for file_path in python_files:
        if file_path.name == "__init__.py":
            continue
            
        print(f"Проверяю: {file_path.relative_to(project_root)}")
        
        if fix_imports_in_file(file_path):
            print(f"✅ Исправлен: {file_path.relative_to(project_root)}")
            fixed_count += 1
        else:
            print(f"⚪ Не требует изменений: {file_path.relative_to(project_root)}")
            
    print(f"\n🎉 Готово! Исправлено файлов: {fixed_count}")


if __name__ == "__main__":
    main() 