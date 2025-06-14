#!/usr/bin/env python3
"""
Интеграционный тест DocsAgent с реальным ИИ
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest

from neira_code_analyzer.main import gen_docs_tool


@pytest.mark.asyncio
async def test_gen_docs_integration():
    """Тестирует работу gen_docs с новой интеграцией ИИ"""

    print("🧪 ТЕСТ ИНТЕГРАЦИИ DOCSAGENT С ИИ")
    print("=" * 50)

    try:
        # Тестируем gen_docs (исправлено: используем относительный путь)
        result = await gen_docs_tool(
            {"path": ".", "docs_structure": "standard", "target_guide_length": 100}
        )

        output = result[0].text if result else "Нет результата"
        print("✅ gen_docs выполнен успешно")
        print("📄 Результат:")
        print("-" * 30)
        print(output[:1000] + "..." if len(output) > 1000 else output)
        print("-" * 30)

        # Проверяем создались ли файлы
        if os.path.exists("docs"):
            print("\n📂 Созданные файлы:")
            for root, _dirs, files in os.walk("docs"):
                for file in files:
                    file_path = os.path.join(root, file)
                    print(f"  📄 {file_path}")

        assert result is not None
        assert len(result) > 0

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback

        traceback.print_exc()
        pytest.fail(f"Интеграционный тест провален: {e}")


if __name__ == "__main__":
    asyncio.run(test_gen_docs_integration())
