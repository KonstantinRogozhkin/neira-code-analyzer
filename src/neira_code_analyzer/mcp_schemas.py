"""
Централизованные схемы для MCP инструментов
Устраняет дублирование определений параметров между различными инструментами

Содержит общие схемы параметров, которые используются в нескольких инструментах,
и функции для их компоновки в финальные схемы инструментов.
"""

from typing import Dict, Any, List

# 🎯 Динамическая генерация enum'ов для устранения дублирования

def _get_available_presets() -> List[str]:
    """
    Динамически получает список доступных пресетов из FilterPresetManager
    Устраняет дублирование хардкоженных enum списков
    """
    try:
        from .filters import list_available_presets
        return list(list_available_presets().keys())
    except Exception:
        # Fallback для случая ошибок
        return ["default", "aggressive", "code-only", "python-project", "web-app", "react-app", "electron-app"]

def _get_available_templates() -> List[str]:
    """
    Динамически получает список доступных шаблонов из TemplateManager
    Устраняет дублирование хардкоженных enum списков
    """
    try:
        from .template_manager import TemplateManager
        manager = TemplateManager()
        return manager.get_available_templates()
    except Exception:
        # Fallback для случая ошибок
        return ["code-review", "security-audit", "documentation", "refactoring", "migration-guide", "api-documentation", "performance-analysis"]

# 🎯 Общие схемы параметров для переиспользования

COMMON_PATH_SCHEMA = {
    "type": "string",
    "description": "Full path to the codebase directory to analyze (e.g., '/Users/username/Projects/my-project'). Avoid using '.' as it may cause issues - always specify complete path.",
    "default": "."
}

COMMON_INCLUDE_PATTERNS_SCHEMA = {
    "type": "array",
    "items": {"type": "string"},
    "description": "List of glob patterns for files to include (e.g., ['*.py', '*.rs', '*.js']). If empty, includes all files. Can be overridden by preset_name parameter.",
    "default": []
}

COMMON_EXCLUDE_PATTERNS_SCHEMA = {
    "type": "array", 
    "items": {"type": "string"},
    "description": "List of glob patterns for files to exclude (e.g., ['*.txt', 'node_modules/**', '*.log']). Applied after include patterns. Common exclusions: ['node_modules/**', '*.log', '*.tmp', 'dist/**', 'build/**']. Can be overridden by preset_name parameter.",
    "default": []
}

def _get_preset_name_schema() -> Dict[str, Any]:
    """Динамически генерируемая схема для пресетов"""
    return {
        "type": "string",
        "description": "Name of preset filter configuration to use. Available presets are loaded dynamically from FilterPresetManager. When specified, overrides include_patterns and exclude_patterns unless merge_with_preset is true.",
        "enum": _get_available_presets()
    }

COMMON_MERGE_WITH_PRESET_SCHEMA = {
    "type": "boolean", 
    "description": "If true and preset_name is specified, merges preset patterns with manually specified include_patterns and exclude_patterns. If false, preset completely overrides manual patterns.",
    "default": False
}

COMMON_SAVE_AS_PRESET_SCHEMA = {
    "type": "string",
    "description": "If specified, saves the current filter configuration as a new preset with this name for future reuse."
}

COMMON_INCLUDE_PRIORITY_SCHEMA = {
    "type": "boolean",
    "description": "When True, include patterns take priority over exclude patterns in case of conflicts. When False, exclude patterns take priority.",
    "default": False
}

COMMON_FOLLOW_SYMLINKS_SCHEMA = {
    "type": "boolean",
    "description": "Follow symbolic links when traversing directories. WARNING: May cause infinite loops if circular links exist.",
    "default": False
}

COMMON_INCLUDE_HIDDEN_SCHEMA = {
    "type": "boolean",
    "description": "Include hidden files and directories (those starting with a dot like .env, .git). Usually not needed for code analysis.",
    "default": False
}

COMMON_ENCODING_SCHEMA = {
    "type": "string",
    "description": "Tokenizer encoding for token counting. 'cl100k' for ChatGPT/GPT-4, 'p50k' for Codex, 'gpt2' for GPT-3, 'o200k' for GPT-4o.",
    "default": "cl100k",
    "enum": ["cl100k", "p50k", "gpt2", "o200k"]
}

def _get_template_name_schema() -> Dict[str, Any]:
    """Динамически генерируемая схема для шаблонов"""
    return {
        "type": "string",
        "description": "Name of predefined template to use. Available options are loaded dynamically from TemplateManager.",
        "enum": _get_available_templates()
    }

CUSTOM_TEMPLATE_SCHEMA = {
    "type": "string",
    "description": "Custom Handlebars template string for formatting the output. Use this for custom templates or when you want to modify an existing template."
}

# 🔧 Специализированные схемы для конкретных инструментов

def get_context_schema() -> Dict[str, Any]:
    """
    Схема для инструмента get_context
    """
    return {
        "type": "object",
        "properties": {
            "path": COMMON_PATH_SCHEMA,
            "template_name": {
                **_get_template_name_schema(),
                "description": "Name of predefined template to use. Use this for quick access to professional templates. If specified, 'template' parameter is ignored."
            },
            "template": {
                **CUSTOM_TEMPLATE_SCHEMA,
                "description": "Custom Handlebars template string for formatting the output. If 'template_name' is specified, this parameter is ignored."
            },
            "include_patterns": {
                **COMMON_INCLUDE_PATTERNS_SCHEMA,
                "description": "List of glob patterns for files to include (e.g., ['*.py', '*.rs', '*.js']). If empty, includes all files. Examples: ['*.py'] for Python only, ['src/**/*.js', '*.md'] for JS in src and all markdown files."
            },
            "exclude_patterns": COMMON_EXCLUDE_PATTERNS_SCHEMA,
            "include_priority": {
                **COMMON_INCLUDE_PRIORITY_SCHEMA,
                "description": "When True, include patterns take priority over exclude patterns in case of conflicts. Recommended: False for most cases."
            },
            "line_numbers": {
                "type": "boolean",
                "description": "Add line numbers to source code blocks for easier reference and debugging. Highly recommended for code review and analysis.",
                "default": True
            },
            "absolute_paths": {
                "type": "boolean",
                "description": "Use absolute file paths instead of relative paths in the generated output. Useful when analyzing multiple projects.",
                "default": False
            },
            "full_directory_tree": {
                "type": "boolean",
                "description": "Include the complete directory tree structure in the output, showing all directories and subdirectories. Useful for architecture analysis.",
                "default": False
            },
            "code_blocks": {
                "type": "boolean",
                "description": "Wrap source code in markdown code blocks with syntax highlighting. Disable for plain text output only in special cases.",
                "default": True
            },
            "follow_symlinks": COMMON_FOLLOW_SYMLINKS_SCHEMA,
            "include_hidden": COMMON_INCLUDE_HIDDEN_SCHEMA,
            "encoding": COMMON_ENCODING_SCHEMA,
            "save_to_file": {
                "type": "string",
                "description": "Path to save the generated context to a file. Relative paths automatically create versioned structure: analysis/YYYY-MM-DD/project-name/ with files named project-name-v1.N.type.md. Absolute paths save directly to specified location."
            },
            "auto_analyze": {
                "type": "boolean",
                "description": "Automatically run set_filters on the target directory after generating context. Provides additional insights about the analyzed codebase.",
                "default": True
            }
        },
        "examples": [
            {
                "description": "Generate documentation for Python project",
                "path": "/path/to/project",
                "template_name": "documentation",
                "include_patterns": ["*.py", "*.md", "*.txt"]
            },
            {
                "description": "Security audit for web application", 
                "path": "/path/to/webapp",
                "template_name": "security-audit",
                "include_patterns": ["*.py", "*.js", "*.html", "*.sql"]
            },
            {
                "description": "Code review for specific module",
                "path": "/path/to/project",
                "template_name": "code-review",
                "include_patterns": ["src/module/**/*.py"],
                "exclude_patterns": ["tests/**", "*.pyc"]
            },
            {
                "description": "Save context to versioned file with auto analysis",
                "path": "/path/to/project",
                "template_name": "documentation",
                "save_to_file": "project_context.md",
                "auto_analyze": True,
                "include_patterns": ["*.py", "*.md"]
            }
        ]
    }

def get_set_filters_schema() -> Dict[str, Any]:
    """
    Схема для инструмента set_filters
    """
    return {
        "type": "object",
        "properties": {
            "path": COMMON_PATH_SCHEMA,
            "preset_name": {
                **_get_preset_name_schema(),
                "description": "Preset filter configuration name. If not specified, automatically detects project type. Available presets are loaded dynamically from FilterPresetManager"
            },
            "include_patterns": {
                **COMMON_INCLUDE_PATTERNS_SCHEMA,
                "description": "Additional file inclusion patterns. Example: ['*.md', '*.txt']. Merged with preset if merge_with_preset=true"
            },
            "exclude_patterns": {
                **COMMON_EXCLUDE_PATTERNS_SCHEMA,
                "description": "Additional file exclusion patterns. Example: ['temp/**', '*.backup']. Merged with preset if merge_with_preset=true"
            },
            "merge_with_preset": {
                **COMMON_MERGE_WITH_PRESET_SCHEMA,
                "description": "Merge specified patterns with preset (true) or replace preset (false)"
            },
            "encoding": {
                **COMMON_ENCODING_SCHEMA,
                "description": "Token counting encoding: cl100k (GPT-4), p50k (Codex), gpt2 (GPT-3)"
            }
        },
        "examples": [
            {
                "description": "Automatic filter setup (detects project type)",
                "path": "/path/to/project"
            },
            {
                "description": "Setup with specific preset",
                "path": "/path/to/webapp",
                "preset_name": "react-app"
            },
            {
                "description": "Preset + additional files",
                "path": "/path/to/project",
                "preset_name": "python-project",
                "merge_with_preset": True,
                "include_patterns": ["*.md", "*.txt"]
            },
            {
                "description": "Fully custom filters",
                "path": "/path/to/project",
                "include_patterns": ["*.py", "*.js"],
                "exclude_patterns": ["tests/**", "temp/**"]
            }
        ]
    }

def get_get_templates_schema() -> Dict[str, Any]:
    """
    Схема для инструмента get_templates
    """
    return {
        "type": "object",
        "properties": {
            "show_content": {
                "type": "boolean",
                "description": "Show the actual content of templates in addition to descriptions. Warning: This will make the output much larger.",
                "default": False
            }
        }
    }

def get_manage_presets_schema() -> Dict[str, Any]:
    """
    Схема для инструмента manage_presets
    """
    return {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Action to perform with presets: 'list' - show all presets, 'create' - create new, 'details' - preset details, 'delete' - delete, 'export' - export to file, 'import' - import from file",
                "enum": ["list", "create", "details", "delete", "export", "import"],
                "default": "list"
            },
            "name": {
                "type": "string",
                "description": "Preset name. Required for: create, details, delete, export"
            },
            "include_patterns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "File inclusion patterns (for create only). Example: ['*.py', '*.js']",
                "default": []
            },
            "exclude_patterns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "File exclusion patterns (for create only). Example: ['tests/**', 'node_modules/**']",
                "default": []
            },
            "description": {
                "type": "string",
                "description": "Preset description (for create only)",
                "default": ""
            },
            "file_path": {
                "type": "string",
                "description": "File path for export/import. Example: '/path/to/preset.json'"
            }
        },
        "examples": [
            {
                "description": "List all available presets",
                "action": "list"
            },
            {
                "description": "Create new preset",
                "action": "create",
                "name": "my-web-app",
                "include_patterns": ["*.js", "*.ts", "*.html", "*.css"],
                "exclude_patterns": ["node_modules/**", "dist/**"],
                "description": "My custom web app preset"
            },
            {
                "description": "Get details of specific preset",
                "action": "details",
                "name": "python-project"
            },
            {
                "description": "Delete user preset",
                "action": "delete",
                "name": "my-old-preset"
            },
            {
                "description": "Export preset to file",
                "action": "export",
                "name": "my-preset",
                "file_path": "/path/to/preset.json"
            },
            {
                "description": "Import preset from file",
                "action": "import",
                "file_path": "/path/to/preset.json"
            }
        ]
    }

def get_analyze_schema() -> Dict[str, Any]:
    """
    Схема для инструмента get_analyze
    """
    return {
        "type": "object",
        "properties": {
            "path": COMMON_PATH_SCHEMA,
            "template_name": {
                **_get_template_name_schema(),
                "description": "Template to use for Neira analysis. Each template provides specialized analysis for different purposes. Examples: 'code-review' - детальный анализ кода, 'security-audit' - проверка безопасности, 'documentation' - создание документации, 'refactoring' - предложения по рефакторингу, 'performance-analysis' - анализ производительности.",
                "enum": _get_available_templates()
            },
            "preset_name": _get_preset_name_schema(),
            "include_patterns": {
                **COMMON_INCLUDE_PATTERNS_SCHEMA,
                "description": "List of glob patterns for files to include (e.g., ['*.py', '*.js', '*.ts']). If empty, includes all relevant code files. Overridden by preset_name unless merge_with_preset is true."
            },
            "exclude_patterns": COMMON_EXCLUDE_PATTERNS_SCHEMA,
            "merge_with_preset": COMMON_MERGE_WITH_PRESET_SCHEMA,
            "save_as_preset": COMMON_SAVE_AS_PRESET_SCHEMA,
            "max_tokens": {
                "type": "integer",
                "default": 1000000,
                "minimum": 10000,
                "maximum": 2000000,
                "description": "Maximum number of tokens to send to Neira. If codebase exceeds this limit, aggressive filters will be applied automatically."
            },
            "ai_model": {
                "type": "string",
                                  "description": "Neira model to use for analysis. gemini-2.5-pro-preview provides the most detailed analysis.",
                "default": "gemini-2.5-pro-preview-06-05",
                "enum": ["gemini-2.5-pro-preview-06-05", "gemini-2.0-flash", "gemini-1.5-pro"]
            }
        }
    }

def get_gen_docs_schema() -> Dict[str, Any]:
    """
    Схема для инструмента gen_docs - автоматическая генерация и обновление документации
    """
    return {
        "type": "object",
        "properties": {
            "path": COMMON_PATH_SCHEMA,
            "docs_structure": {
                "type": "string",
                "description": "Target documentation structure. 'standard' creates docs/ with changelog, guides, help folders. 'minimal' creates basic README updates only.",
                "enum": ["standard", "minimal"],
                "default": "standard"
            },
            "scan_depth": {
                "type": "integer",
                "description": "How deep to scan for documentation files to process (in directory levels). Higher values scan more files but take longer.",
                "minimum": 1,
                "maximum": 5,
                "default": 3
            },
            "max_file_size": {
                "type": "integer", 
                "description": "Maximum size of markdown files to process (in lines). Files larger than this will be archived or compressed.",
                "minimum": 50,
                "maximum": 1000,
                "default": 400
            },
            "archive_processed": {
                "type": "boolean",
                "description": "Whether to move processed files to docs/archive/ after extracting knowledge. Recommended for keeping the docs clean.",
                "default": True
            },
            "update_changelog": {
                "type": "boolean",
                "description": "Automatically update CHANGELOG.md from git commits and processed files.",
                "default": True
            },
            "git_scan_days": {
                "type": "integer",
                "description": "How many days back to scan git history for changes to include in documentation.",
                "minimum": 1,
                "maximum": 90,
                "default": 14
            },
            "compress_guides": {
                "type": "boolean",
                "description": "Compress guides to meet the target length (≤150 lines) while preserving essential information.",
                "default": True
            },
            "target_guide_length": {
                "type": "integer",
                "description": "Target maximum length for guides in lines. Guides longer than this will be compressed.",
                "minimum": 50,
                "maximum": 300,
                "default": 150
            }
        },
        "examples": [
            {
                "description": "Standard documentation generation",
                "path": "/path/to/project",
                "docs_structure": "standard",
                "archive_processed": True
            },
            {
                "description": "Minimal docs update with changelog",
                "path": "/path/to/project", 
                "docs_structure": "minimal",
                "update_changelog": True,
                "git_scan_days": 7
            },
            {
                "description": "Deep scan with compression",
                "path": "/path/to/project",
                "scan_depth": 4,
                "max_file_size": 300,
                "compress_guides": True,
                "target_guide_length": 100
            }
        ]
    }

# 📋 Маппинг инструментов к их схемам
TOOL_SCHEMAS = {
    "get_context": get_context_schema,
    "set_filters": get_set_filters_schema,
    "get_templates": get_get_templates_schema,
    "manage_presets": get_manage_presets_schema,
    "get_analyze": get_analyze_schema,
    "gen_docs": get_gen_docs_schema
}

def get_tool_schema(tool_name: str) -> Dict[str, Any]:
    """
    Получить схему для указанного инструмента
    
    Args:
        tool_name: Название инструмента
        
    Returns:
        Dict[str, Any]: Схема инструмента
        
    Raises:
        ValueError: Если инструмент не найден
    """
    if tool_name not in TOOL_SCHEMAS:
        raise ValueError(f"Unknown tool: {tool_name}. Available tools: {list(TOOL_SCHEMAS.keys())}")
    
    return TOOL_SCHEMAS[tool_name]()

def get_all_tool_schemas() -> Dict[str, Dict[str, Any]]:
    """
    Получить схемы всех инструментов
    
    Returns:
        Dict[str, Dict[str, Any]]: Словарь {название_инструмента: схема}
    """
    return {name: schema_func() for name, schema_func in TOOL_SCHEMAS.items()} 