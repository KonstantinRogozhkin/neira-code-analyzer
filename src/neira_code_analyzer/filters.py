"""
Централизованная конфигурация фильтров для анализа кода.

Содержит константы со списками исключений для различных типов проектов
и задач анализа, избегая дублирования кода.
"""

from typing import List

# Базовые исключения - применяются везде для разумного анализа
DEFAULT_EXCLUDES: List[str] = [
    # Зависимости - все уровни вложенности (КРИТИЧНО!)
    "node_modules/**", "*/node_modules/**", "**/node_modules/**", 
    "tmp-*/**/node_modules/**", "*/tmp-*/**/node_modules/**",
    
    # Временные билды (очень много мусора!)
    "tmp-*/**", "*/tmp-*/**", "**/tmp-*/**",
    
    # Медиа файлы
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.ico", "*.webp",
    "*.wav", "*.mp3", "*.mp4", "*.avi", "*.mov", 
    
    # Файлы иконок (занимают много токенов)
    "*.icns", "*.icl", "*.cur",
    
    # Шрифты (много токенов для анализа)
    "*.woff", "*.woff2", "*.ttf", "*.eot", "*.otf",
    
    # Бинарные и специальные файлы 
    "*.blob", "*.bin", "*.exe", "*.dll", "*.db", "*.sqlite", "*.sqlite3",
    
    # Сборка и компиляция
    "dist/**", "**/dist/**", "build/**", "**/build/**", "out/**", "**/out/**",
    ".webpack/**", "*/.webpack/**", "**/.webpack/**",
    "*.tsbuildinfo", "*.map", "*.min.js", "*.min.css", "*.bundle.js", "*.chunk.js",
    
    # Системные и IDE файлы
    ".git/**", ".DS_Store", "Thumbs.db", "*.log", "*.tmp", "*.cache", "*.lock", "uv.lock", "*.backup",
    ".idea/**", ".vscode/**", ".devcontainer/**", "*.pyc", "*.pyo", "*.pyd",
    
    # Lock-файлы менеджеров пакетов (очень большие)
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Pipfile.lock",
    
    # Тесты - основные паттерны
    "test/**", "tests/**", "__tests__/**", "spec/**",
    "**/test/**", "**/tests/**", "**/spec/**",
    
    # Тестовые данные и записи (КРИТИЧНО!)
    "**/test/**/recordings/**", "**/test/**/fixtures/**", "**/test/**/results/**",
    "**/test/**/data/**", "**/perf-tests/**", "**/colorize-tests/**",
    "**/colorize-perf-tests/**", "**/browser/recordings/**", 
    
    # Тестовые файлы по именам
    "*.test.js", "*.test.ts", "*.test.jsx", "*.test.tsx",
    "*.spec.js", "*.spec.ts", "*.spec.jsx", "*.spec.tsx",
    "*test*.json", "*fixture*.json", "*recording*.ts", "*perf-data*.ts",
    
    # Отчеты тестов (все варианты + более точные паттерны)
    "playwright-report/**", "**/playwright-report/**", "*/playwright-report/**",
    "test-results/**", "**/test-results/**", "*/test-results/**",
    "coverage/**", "**/coverage/**", "*/coverage/**",
    ".nyc_output/**", "**/.nyc_output/**",
    
    # Конкретные файлы отчетов
    "playwright-report/index.html", "**/playwright-report/index.html",
    "*/playwright-report/index.html",
    
    # Кэши сборки и временные папки
    "/.build-cache/", "/.cache/", "/cache/", "/caches/",
    "/.next/", "/.nuxt/", "/.output/", "/.vercel/", "/.netlify/",
    "/.turbo/", "/.parcel-cache/", "/.swc/", "/.vite/", "/.rollup.cache/",
    "/.npm/", "/.yarn/", "/.pnpm-store/", "/.pnpm/",
    "/.mypy_cache/", "/.tox/", "/.coverage/",
    "/.gradle/", "/.m2/",
    "/.ccls-cache/", "/.clangd/", "/cmake-build-",
    "/DerivedData/", "/Pods/",
    "/Library/", "/Temp/", "/Binaries/", "/Intermediate/", "/Saved/",
    "/tmp/", "/temp/", "/temporary/",
]

# Агрессивные исключения для code review (когда нужно сократить токены)
AGGRESSIVE_EXCLUDES: List[str] = DEFAULT_EXCLUDES + [
    # Документация
    "*.md", "README*", "CHANGELOG*", "LICENSE*",
    "docs/**", "documentation/**", 
    
    # Конфигурационные файлы
    "*.json", "package*.json", "*.yaml", "*.yml",
    "scripts/**", "tools/**", "*.sh", "*.bat",
    
    # Стили и разметка
    "*.css", "*.scss", "*.less", "*.html",
    "assets/**", "public/**", "static/**",
]

# Паттерны для включения только основных файлов кода
CODE_ONLY_INCLUDES: List[str] = [
    "*.py", "*.js", "*.ts", "*.tsx", "*.jsx", "*.java", "*.cpp", "*.c", "*.h", "*.go", "*.rs", "*.php"
]

def get_default_excludes() -> List[str]:
    """Возвращает базовые исключения для большинства случаев."""
    return DEFAULT_EXCLUDES.copy()

def get_aggressive_excludes() -> List[str]:
    """Возвращает агрессивные исключения для экономии токенов."""
    return AGGRESSIVE_EXCLUDES.copy()

def get_code_only_patterns() -> tuple[List[str], List[str]]:
    """Возвращает паттерны для анализа только кода (includes, excludes)."""
    return CODE_ONLY_INCLUDES.copy(), AGGRESSIVE_EXCLUDES.copy() 