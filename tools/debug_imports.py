#!/usr/bin/env python3
"""
Скрипт для проверки импортов модулей
"""

# Список модулей для проверки: (путь_модуля, описание)
MODULES_TO_TEST = [
    ("mcp", "Model Context Protocol"),
    ("src.neira_code_analyzer.main", "Основной модуль MCP сервера"),
    ("src.neira_code_analyzer.context_generator", "Генератор контекста"),
    ("src.neira_code_analyzer.ai_analyzer", "AI анализатор"),
    ("src.neira_code_analyzer.filters", "Система фильтров")
]

def test_import(module_path: str, description: str) -> bool:
    """
    Проверяет возможность импорта модуля
    
    Args:
        module_path: Путь к модулю для импорта
        description: Описание модуля для вывода
        
    Returns:
        bool: True если импорт успешен, False если ошибка
    """
    try:
        __import__(module_path)
        print(f"✅ {description}: ОК")
        return True
    except ImportError as e:
        print(f"❌ {description}: ОШИБКА - {e}")
        return False

def main():
    """Основная функция для проверки всех модулей"""
    print("🔍 Проверка импортов модулей neira-code-analyzer...\n")
    
    # Используем sum() для более лаконичного подсчета успешных импортов
    results = [test_import(path, desc) for path, desc in MODULES_TO_TEST]
    successful_imports = sum(results)
    total_imports = len(MODULES_TO_TEST)
    
    # Выводим итоговую статистику
    print(f"\n📊 Результат: {successful_imports}/{total_imports} модулей импортированы успешно")
    
    if successful_imports == total_imports:
        print("🎉 Все модули работают корректно!")
    else:
        failed_imports = total_imports - successful_imports
        print(f"⚠️ Найдено {failed_imports} проблем с импортами")

if __name__ == "__main__":
    main() 