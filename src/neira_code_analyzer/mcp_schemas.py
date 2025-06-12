"""
Централизованные схемы для MCP инструментов
Устраняет дублирование определений параметров между различными инструментами

Содержит общие схемы параметров, которые используются в нескольких инструментах,
и функции для их компоновки в финальные схемы инструментов.
"""

from typing import Dict, Any, List

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

COMMON_PRESET_NAME_SCHEMA = {
    "type": "string",
    "description": "Name of preset filter configuration to use. Available presets: 'default', 'aggressive', 'code-only', 'python-project', 'web-app', 'react-app', 'electron-app', plus any user-defined presets. When specified, overrides include_patterns and exclude_patterns unless merge_with_preset is true.",
    "enum": ["default", "aggressive", "code-only", "python-project", "web-app", "react-app", "electron-app"]
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

TEMPLATE_NAME_SCHEMA = {
    "type": "string",
    "description": "Name of predefined template to use. Available options: 'code-review', 'security-audit', 'documentation', 'refactoring', 'migration-guide', 'api-documentation', 'performance-analysis'.",
    "enum": ["code-review", "security-audit", "documentation", "refactoring", "migration-guide", "api-documentation", "performance-analysis"]
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
                **TEMPLATE_NAME_SCHEMA,
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
                **COMMON_PRESET_NAME_SCHEMA,
                "description": "Preset filter configuration name. If not specified, automatically detects project type. Available: python-project, web-app, react-app, electron-app, code-only, aggressive"
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

def get_code_review_schema() -> Dict[str, Any]:
    """
    Схема для инструмента code_review
    """
    return {
        "type": "object",
        "properties": {
            "path": COMMON_PATH_SCHEMA,
            "template_name": {
                **TEMPLATE_NAME_SCHEMA,
                "description": "Template to use for Neira analysis. Each template provides specialized analysis for different purposes.",
                "enum": ["code-review", "security-audit", "documentation", "refactoring", "migration-guide", "api-documentation", "performance-analysis"]
            },
            "preset_name": COMMON_PRESET_NAME_SCHEMA,
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
                "description": "Neira model to use for analysis. neira-2.5-pro-preview provides the most detailed analysis.",
                "default": "neira-2.5-pro-preview-06-05",
                "enum": ["neira-2.5-pro-preview-06-05", "neira-pro", "neira-pro-vision"]
            }
        }
    }

# 📋 Маппинг инструментов к их схемам
TOOL_SCHEMAS = {
    "get_context": get_context_schema,
    "set_filters": get_set_filters_schema,
    "get_templates": get_get_templates_schema,
    "manage_presets": get_manage_presets_schema,
    "code_review": get_code_review_schema
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