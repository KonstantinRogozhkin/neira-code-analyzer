#!/usr/bin/env python3
"""
Скрипт для проверки импортов модулей
"""

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
    
    # Список модулей для проверки: (путь_модуля, описание)
    modules_to_test = [
        ("mcp", "Model Context Protocol"),
        ("src.neira_code_analyzer.main", "Основной модуль MCP сервера"),
        ("src.neira_code_analyzer.context_generator", "Генератор контекста"),
        ("src.neira_code_analyzer.ai_analyzer", "AI анализатор"),
        ("src.neira_code_analyzer.filters", "Система фильтров")
    ]
    
    # Проверяем все модули и считаем результаты
    successful_imports = 0
    total_imports = len(modules_to_test)
    
    for module_path, description in modules_to_test:
        if test_import(module_path, description):
            successful_imports += 1
    
    # Выводим итоговую статистику
    print(f"\n📊 Результат: {successful_imports}/{total_imports} модулей импортированы успешно")
    
    if successful_imports == total_imports:
        print("🎉 Все модули работают корректно!")
    else:
        failed_imports = total_imports - successful_imports
        print(f"⚠️ Найдено {failed_imports} проблем с импортами")

if __name__ == "__main__":
    main() 