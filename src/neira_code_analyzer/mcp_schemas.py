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
    "description": "List of glob patterns for files to include (e.g., ['*.py', '*.rs', '*.js']). If empty, includes all files.",
    "default": []
}

COMMON_EXCLUDE_PATTERNS_SCHEMA = {
    "type": "array", 
    "items": {"type": "string"},
    "description": "List of glob patterns for files to exclude (e.g., ['*.txt', 'node_modules/**', '*.log']). Applied after include patterns. Common exclusions: ['node_modules/**', '*.log', '*.tmp', 'dist/**', 'build/**'].",
    "default": []
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
                "description": "Automatically run analyze_filters on the target directory after generating context. Provides additional insights about the analyzed codebase.",
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

def get_analyze_filters_schema() -> Dict[str, Any]:
    """
    Схема для инструмента analyze_filters
    """
    return {
        "type": "object",
        "properties": {
            "path": COMMON_PATH_SCHEMA,
            "include_patterns": {
                **COMMON_INCLUDE_PATTERNS_SCHEMA,
                "description": "List of glob patterns for files to include (e.g., ['*.py', '*.rs', '*.js']). If empty, includes all files. Test different patterns to optimize selection."
            },
            "exclude_patterns": COMMON_EXCLUDE_PATTERNS_SCHEMA,
            "include_priority": COMMON_INCLUDE_PRIORITY_SCHEMA,
            "follow_symlinks": COMMON_FOLLOW_SYMLINKS_SCHEMA,
            "include_hidden": COMMON_INCLUDE_HIDDEN_SCHEMA,
            "encoding": COMMON_ENCODING_SCHEMA,
            "show_top_files": {
                "type": "integer",
                "description": "Number of largest files to show in detailed breakdown. Helps identify files that consume most tokens.",
                "default": 10,
                "minimum": 1,
                "maximum": 50
            },
            "max_directory_depth": {
                "type": "integer", 
                "description": "Maximum depth for directory tree analysis. Deeper levels will be summarized to avoid overwhelming output.",
                "default": 3,
                "minimum": 1,
                "maximum": 10
            },
            "min_file_size": {
                "type": "integer",
                "description": "Minimum file size in characters to include in analysis. Filters out tiny files that don't impact token count significantly.",
                "default": 0,
                "minimum": 0
            },
            "save_to_file": {
                "type": "string",
                "description": "Path to save the analysis results to a file. Relative paths automatically create versioned structure: analysis/YYYY-MM-DD/project-name/ with files named project-name-v1.N.filters.md. Absolute paths save directly to specified location."
            }
        },
        "examples": [
            {
                "description": "Analyze Python project structure",
                "path": "/path/to/project",
                "include_patterns": ["*.py"],
                "exclude_patterns": ["tests/**", "__pycache__/**", "*.pyc"]
            },
            {
                "description": "Test web app filters",
                "path": "/path/to/webapp",
                "include_patterns": ["*.py", "*.js", "*.html", "*.css"],
                "exclude_patterns": ["node_modules/**", "dist/**", "*.min.js", "*.min.css"]
            },
            {
                "description": "Analyze all files with exclusions",
                "path": "/path/to/project",
                "exclude_patterns": ["*.log", "*.tmp", ".git/**", "*.lock"]
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
                "description": "Template to use for AI analysis. Each template provides specialized analysis for different purposes.",
                "default": "code-review"
            },
            "include_patterns": {
                **COMMON_INCLUDE_PATTERNS_SCHEMA,
                "description": "List of glob patterns for files to include (e.g., ['*.py', '*.js', '*.ts']). If empty, includes all relevant code files."
            },
            "exclude_patterns": COMMON_EXCLUDE_PATTERNS_SCHEMA,
            "max_tokens": {
                "type": "integer",
                "description": "Maximum number of tokens to send to AI. If codebase exceeds this limit, aggressive filters will be applied automatically.",
                "default": 1000000,
                "minimum": 10000,
                "maximum": 2000000
            },
            "google_ai_model": {
                "type": "string",
                "description": "AI model to use for analysis. gemini-2.5-pro-preview provides the most detailed analysis.",
                "default": "gemini-2.5-pro-preview-06-05",
                "enum": ["gemini-2.5-pro-preview-06-05", "gemini-pro", "gemini-pro-vision"]
            }
        }
    }

# 📋 Маппинг инструментов к их схемам
TOOL_SCHEMAS = {
    "get_context": get_context_schema,
    "analyze_filters": get_analyze_filters_schema,
    "get_templates": get_get_templates_schema,
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