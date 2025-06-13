#!/usr/bin/env python3
"""
Тест интеграции DocsAgent с реальным ИИ
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.abspath('.'))

from src.neira_code_analyzer.main import gen_docs_tool

async def test_gen_docs():
    """Тестирует работу gen_docs с новой интеграцией ИИ"""
    
    print("🧪 ТЕСТ ИНТЕГРАЦИИ DOCSAGENT С ИИ")
    print("=" * 50)
    
    try:
        # Тестируем gen_docs
        result = await gen_docs_tool({
            'path': '/Users/konstantin/Projects/neira-code-analyzer',
            'docs_structure': 'standard',
            'target_guide_length': 100
        })
        
        output = result[0].text if result else "Нет результата"
        print("✅ gen_docs выполнен успешно")
        print("📄 Результат:")
        print("-" * 30)
        print(output[:1000] + "..." if len(output) > 1000 else output)
        print("-" * 30)
        
        # Проверяем создались ли файлы
        import os
        if os.path.exists('docs'):
            print("\n📂 Созданные файлы:")
            for root, dirs, files in os.walk('docs'):
                for file in files:
                    file_path = os.path.join(root, file)
                    print(f"  📄 {file_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_gen_docs())
    print(f"\n🎯 Результат теста: {'✅ Успех' if success else '❌ Ошибка'}") 