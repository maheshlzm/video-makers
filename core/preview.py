"""Visual Preview Engine: Instant Keyframe Storyboards & Interactive Scrubbing.
Executes procedural PIL scenes in memory with zero video encoding overhead.
"""

import ast
import re
import sys
import types
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_script_module(script_code: str) -> types.ModuleType:
    """Dynamically compiles and executes a standalone motion script into a temporary module."""
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    module_name = f"motion_script_preview_{abs(hash(script_code)) % 1000000}"
    mod = types.ModuleType(module_name)
    mod.__file__ = str(PROJECT_ROOT / "scripts" / f"{module_name}.py")

    # Execute script code within module namespace
    exec(script_code, mod.__dict__)
    return mod


def get_scene_names(script_code: str) -> List[str]:
    """Inspects AST to find all scene_N functions in numeric order."""
    try:
        tree = ast.parse(script_code)
    except SyntaxError:
        return []

    scenes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("scene_"):
            scenes.append(node.name)

    # Sort numerically: scene_1, scene_2, scene_10...
    def _scene_key(name: str) -> int:
        parts = re.findall(r"\d+", name)
        return int(parts[0]) if parts else 999

    return sorted(scenes, key=_scene_key)


def render_scene_keyframe(
    script_code: str,
    scene_name: str,
    progress: float = 0.5,
    time_s: float = 2.0,
) -> Image.Image:
    """Executes a single scene function at a specific progress and returns PIL image."""
    try:
        mod = load_script_module(script_code)
        if not hasattr(mod, scene_name):
            # Fallback blank frame with notice
            img = Image.new("RGBA", (1080, 1920), (15, 23, 42, 255))
            return img

        func = getattr(mod, scene_name)
        # Check function parameter count
        import inspect
        sig = inspect.signature(func)
        if len(sig.parameters) >= 2:
            frame = func(float(progress), float(time_s))
        elif len(sig.parameters) == 1:
            frame = func(float(progress))
        else:
            frame = func()

        if isinstance(frame, Image.Image):
            return frame
        else:
            img = Image.new("RGBA", (1080, 1920), (15, 23, 42, 255))
            return img

    except Exception as e:
        # On error return dark frame with error text
        from PIL import ImageDraw
        img = Image.new("RGBA", (1080, 1920), (20, 10, 20, 255))
        draw = ImageDraw.Draw(img)
        draw.text((100, 900), f"Preview Error in {scene_name}:\n{str(e)[:150]}", fill=(248, 113, 113, 255))
        return img


def generate_storyboard(
    script_code: str,
    progress: float = 0.5,
) -> List[Tuple[Image.Image, str]]:
    """Generates an instant visual storyboard gallery containing keyframe snapshots of every scene."""
    scenes = get_scene_names(script_code)
    if not scenes:
        return []

    storyboard = []
    try:
        mod = load_script_module(script_code)
    except Exception as e:
        return []

    for idx, scene_name in enumerate(scenes, start=1):
        try:
            func = getattr(mod, scene_name, None)
            if callable(func):
                import inspect
                sig = inspect.signature(func)
                time_s = idx * 3.0
                if len(sig.parameters) >= 2:
                    frame = func(float(progress), float(time_s))
                elif len(sig.parameters) == 1:
                    frame = func(float(progress))
                else:
                    frame = func()

                if isinstance(frame, Image.Image):
                    storyboard.append((frame, f"Scene {idx} ({scene_name}) • Climax (50%)"))
        except Exception:
            continue

    return storyboard
