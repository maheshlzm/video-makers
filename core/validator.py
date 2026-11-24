"""AST syntax validator and structure analyzer for AI-generated scripts.
Zero render dependencies - pure static code analysis.
"""

import ast
from typing import Tuple, List, Dict, Any


def validate_script_ast(code: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """Validates Python code syntax via AST and extracts all scene functions and their details.
    Does NOT execute or render any code. Attempts auto-healing on syntax errors.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        try:
            from core.generator import auto_heal_syntax_errors
            healed = auto_heal_syntax_errors(code)
            tree = ast.parse(healed)
        except Exception:
            return False, f"Syntax Error on line {e.lineno}: {e.msg}", []

    scenes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("scene_"):
            doc = ast.get_docstring(node) or "No description"
            args = [a.arg for a in node.args.args]
            scenes.append({
                "name": node.name,
                "line": node.lineno,
                "args": args,
                "description": doc,
            })

    scenes.sort(key=lambda s: int(s["name"].split("_")[1]) if s["name"].split("_")[1].isdigit() else 99)
    if not scenes:
        return False, "No 'def scene_N()' functions found in script.", []

    scene_names = [s["name"] for s in scenes]
    return True, f"✔ Valid Python syntax ({len(scenes)} scenes detected: {', '.join(scene_names)})", scenes
