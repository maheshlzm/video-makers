"""Core module for Local AI Script Generation and AST Validation.
Zero render overhead.
"""

from core.ai_client import query_llm, query_llm_stream, get_available_models, is_ollama_reachable, DEFAULT_MODEL
from core.generator import generate_motion_script, build_user_prompt, clean_script_code, VISUAL_SCRIPT_SYSTEM_PROMPT
from core.validator import validate_script_ast

__all__ = [
    "query_llm",
    "query_llm_stream",
    "get_available_models",
    "is_ollama_reachable",
    "DEFAULT_MODEL",
    "generate_motion_script",
    "build_user_prompt",
    "clean_script_code",
    "validate_script_ast",
    "VISUAL_SCRIPT_SYSTEM_PROMPT",
]
