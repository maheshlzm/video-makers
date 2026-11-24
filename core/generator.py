"""Local AI Motion Graphics Script Generator.
Synthesizes clean, modular Python animation scripts defining procedural scene functions.
Exposes the actual prompt text, streaming generation, and code-cleaning pipeline.
"""

import re
import time
from pathlib import Path
from typing import Dict, Any, Tuple, Generator
from core.ai_client import query_llm, query_llm_stream, DEFAULT_MODEL

VISUAL_SCRIPT_SYSTEM_PROMPT = """You are an expert Python motion graphics director. You write clean, standalone, executable Python scripts that procedurally render custom 1080x1920 YouTube Shorts at 30 FPS.
You output ONLY valid, executable Python code with no markdown formatting and no conversational preamble.

AUDIO & NARRATION RULES:
1. ZERO AUDIO IN PYTHON:
   - NEVER write audio synthesis, sound generation, wave files, array manipulation, or text-to-speech code in Python.
   - Do NOT import wave, array, tempfile audio, or write synthetic sound generators.
   - The creator records their own voiceover; the Python script must focus 100% strictly on procedural PIL visual rendering (1080x1920 30FPS).

2. SPOKEN ENGLISH VOICEOVER SCRIPT (Top Docstring):
   - At the very top of your Python file, write a natural, smooth, conversational English voiceover narration script inside a top-level docstring:
     \"\"\"
     VOICEOVER NARRATION SCRIPT:
     [Write 2 to 4 smooth, continuous flowing paragraphs in clean, engaging English that fully explain the video topic.
      Do NOT use choppy scene tags, timestamps, or tone labels. Write it as natural, spoken prose that a creator can read directly into their microphone in one take.]
     \"\"\"

CORE SCRIPT ARCHITECTURE:
1. Every scene in the video is a dedicated procedural render function:
   def scene_N(progress: float, time_s: float) -> Image.Image:
   - `progress` runs from 0.0 to 1.0 during that scene (use it for reveals, scaling, translation).
   - `time_s` is the global video time in seconds (use it for continuous ambient pulsing, rotating, breathing).
   - Returns a PIL Image in 'RGBA' mode (1080 width, 1920 height).

2. Canvas & Visual Design Rules (1080x1920 Vertical Screen):
   - Background canvas: `img = Image.new("RGBA", (1080, 1920), hex_to_rgba('#0F172A'))`
   - Draw context: `draw = ImageDraw.Draw(img)`
   - Center Anchor: Screen center is (CX=540, CY=960). Never leave 70% of the screen as empty black space.
   - Use the visual primitives imported from `primitives`:
     * draw_card(draw, cx=540, cy=960, w=840, h=540, fill=..., outline=...)
     * draw_device_frame(draw, cx=540, cy=960, w=740, h=1180, outline=...)
     * draw_badge(draw, cx=540, cy=400, text="STEP 1", font=badge_font, bg_color=...)
     * draw_node(draw, cx, cy, radius=40, label="DNS", font=font, color=...)
   - BOLD, CLEAR ON-SCREEN WORDS & LABELS (Easy to Read on Mobile):
     Every scene MUST display prominent, high-contrast on-screen text words:
     * Place big bold headlines near top (y=260-380, size 52-60, bright white '#FFFFFF'):
       title_font = get_font("title", size=54, bold=True)
       lines = wrap_text(headline_text, title_font, max_width=860)
       for line in lines:
           w, h = get_text_dimensions(draw, line, title_font)
           draw.text((int(round(540 - w / 2)), y), line, font=title_font, fill=hex_to_rgba('#FFFFFF'))
           y += h + 16
     * Subtitle, metric, or highlight badge with clear descriptive words.
     * Text labels on all cards, nodes, and device frames so the viewer can easily read every key word and follow the concept.
   - Smooth Animation Math:
     Always use `progress` (0.0 to 1.0):
     smooth_y = int(round(start_y + (target_y - start_y) * min(1.0, progress * 1.3)))
     pulse = int(round(math.sin(time_s * 4.0) * 8.0))
     Always round coordinates to integers using int(round(...)).

3. CRITICAL RESTRICTIONS (ZERO SYNTAX ERRORS):
   - ZERO CLI BOILERPLATE: Output ONLY `def scene_1(progress, time_s)`, `def scene_2(...)`, etc. NEVER write `def main()`, `argparse`, `shutil`, `subprocess`, or CLI runner loops. The studio executes scene functions directly in memory.
   - CLEAN MATH & BALANCED PARENTHESES: Avoid deeply nested math formulas inside tuples. Compute coordinates on separate lines:
     CORRECT:
       rx = reach + 18 * (1.0 - amount)
       line(draw, [(x + dx * reach, y + dy * reach), (x + dx * rx, y + dy * rx)], color)
     WRONG:
       line(draw, [(x+dx*reach, y+dy*reach), (x+dx*(reach+18*(1-amount)), y+dy*(reach+18*(1-amount))], color)
   - ZERO EXTERNAL ASSETS: NEVER call Image.open(). Never assume image or audio files exist on disk (such as 'assets/phone.png'). Draw all visual elements procedurally.
   - NEVER call draw.scene(). Pillow ImageDraw has no such function.
   - Do NOT redefine get_font, wrap_text, hex_to_rgba, or draw_card. Use the ones imported from `primitives`.

EXACT CODE STRUCTURE TO FOLLOW:
\"\"\"
VOICEOVER NARRATION SCRIPT:
[2 to 4 smooth, continuous spoken English paragraphs explaining the concept, ready to read into a mic.]
\"\"\"

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import math
from PIL import Image, ImageDraw, ImageFont
from primitives import (
    WIDTH, HEIGHT, CX, CY,
    hex_to_rgba, hex_to_rgb, bg_rgba,
    get_font, wrap_text, get_text_dimensions,
    draw_card, draw_device_frame, draw_badge, draw_node
)

# def scene_1(progress: float, time_s: float) -> Image.Image:
# def scene_2(progress: float, time_s: float) -> Image.Image:
# etc...
"""


def clean_script_code(raw_text: str) -> str:
    """Strips markdown code blocks, backticks, rogue calls, ensures standard imports, and repairs any mid-sentence truncation."""
    text = raw_text.strip()
    match = re.search(r"```(?:python)?(.*?)```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    text = re.sub(r"^```[a-zA-Z]*", "", text).strip()
    text = re.sub(r"```$", "", text).strip()

    # Strip rogue calls
    text = re.sub(r"draw\.scene\([^\)]*\)", "# draw.scene removed", text)
    text = re.sub(r"\b\w+\.show\(\)", "# img.show removed", text)

    # Strip top-level execution test calls outside functions
    text = re.sub(r"^[ \t]*img\s*=\s*scene_\w+\([^)]*\).*", "# top-level scene call removed", text, flags=re.MULTILINE)

    # Strip any accidental wave, array, or robotic audio synthesis
    text = re.sub(r"^[ \t]*import\s+wave.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[ \t]*from\s+array\s+import\s+array.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[ \t]*import\s+tempfile.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[ \t]*def\s+synth_audio\b.*?(?=\ndef\s|\n[a-zA-Z]|\Z)", "", text, flags=re.DOTALL)

    # Strip broken LLM redefinitions of engine primitives so real implementations are used
    text = re.sub(r"def get_font\([^)]*\):(?:\n[ \t]+[^\n]+)+", "", text)
    text = re.sub(r"def hex_to_rgba\([^)]*\):(?:\n[ \t]+[^\n]+)+", "", text)
    text = re.sub(r"def bg_rgba\([^)]*\):(?:\n[ \t]+[^\n]+)+", "", text)

    # Ensure sys.path.insert is present
    if "sys.path.insert" not in text:
        header = "import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).resolve().parent.parent))\n"
        # Preserve top docstring if present
        doc_match = re.match(r'^(?:"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')\s*', text)
        if doc_match:
            doc_str = doc_match.group(0)
            rest = text[len(doc_str):]
            text = doc_str + "\n" + header + rest
        else:
            text = header + text

    # Ensure PIL imports include ImageFont
    if "from PIL import" in text:
        text = re.sub(r"from PIL import [^\n]+", "from PIL import Image, ImageDraw, ImageFont", text)
    else:
        text = "from PIL import Image, ImageDraw, ImageFont\n" + text

    # Ensure primitive imports are present
    if "from primitives import" not in text:
        text = (
            "from primitives import (\n"
            "    WIDTH, HEIGHT, CX, CY,\n"
            "    hex_to_rgba, hex_to_rgb, bg_rgba,\n"
            "    get_font, wrap_text, get_text_dimensions,\n"
            "    draw_card, draw_device_frame, draw_badge, draw_node\n"
            ")\n" + text
        )

    # Strip rogue def main() CLI boilerplates so they never cause trailing syntax errors
    text = re.sub(r"\n\s*def main\(\):[\s\S]*?(?=\n[a-zA-Z]|\Z)", "\n", text)
    text = re.sub(r"\n\s*if __name__\s*==\s*['\"]__main__['\"]:\s*main\(\)\s*", "\n", text)

    # Automatically heal internal syntax errors (unclosed parens, mismatched brackets, bad math lines)
    text = auto_heal_syntax_errors(text)

    # Automatically repair any trailing incomplete expressions or unclosed brackets
    text = repair_truncated_code(text)

    return text


def auto_heal_syntax_errors(code: str, max_passes: int = 15) -> str:
    """Iteratively analyzes and heals Python syntax errors (such as unclosed parentheses,
    mismatched brackets in math expressions, or malformed decorative drawing lines) using AST feedback.
    """
    import ast

    for _ in range(max_passes):
        try:
            ast.parse(code)
            return code  # Code is 100% valid Python!
        except SyntaxError as e:
            if not e.lineno:
                break

            lines = code.splitlines()
            line_idx = e.lineno - 1
            if line_idx >= len(lines):
                break

            err_line = lines[line_idx]
            msg = str(e.msg).lower()
            repaired = False

            # Case A: Closing bracket does not match opening parenthesis (e.g. missing ')' before ']')
            if "does not match opening parenthesis" in msg or "unmatched" in msg:
                for pos in range(len(err_line) - 1, -1, -1):
                    if err_line[pos] in ("]", "}", ")"):
                        for add_parens in (")", "))", ")))"):
                            candidate_line = err_line[:pos] + add_parens + err_line[pos:]
                            test_lines = list(lines)
                            test_lines[line_idx] = candidate_line
                            try:
                                ast.parse("\n".join(test_lines))
                                lines[line_idx] = candidate_line
                                code = "\n".join(lines)
                                repaired = True
                                break
                            except SyntaxError as e2:
                                if e2.lineno and e2.lineno > e.lineno:
                                    lines[line_idx] = candidate_line
                                    code = "\n".join(lines)
                                    repaired = True
                                    break
                        if repaired:
                            break

            # Case B: Parenthesis/bracket was never closed
            elif "was never closed" in msg:
                diff_p = err_line.count("(") - err_line.count(")")
                diff_b = err_line.count("[") - err_line.count("]")
                diff_c = err_line.count("{") - err_line.count("}")
                closing = ")" * max(0, diff_p) + "]" * max(0, diff_b) + "}" * max(0, diff_c)
                if closing:
                    candidate_line = err_line + closing
                    test_lines = list(lines)
                    test_lines[line_idx] = candidate_line
                    try:
                        ast.parse("\n".join(test_lines))
                        lines[line_idx] = candidate_line
                        code = "\n".join(lines)
                        repaired = True
                    except SyntaxError as e2:
                        if e2.lineno and e2.lineno > e.lineno:
                            lines[line_idx] = candidate_line
                            code = "\n".join(lines)
                            repaired = True

            # Case C: Fallback heal for malformed decorative lines
            if not repaired and any(kw in err_line for kw in ("line(", "rect(", "dot(", "draw.", "burst(", "book(", "wrench(")):
                indent = len(err_line) - len(err_line.lstrip())
                fallback = " " * indent + "pass  # auto-healed syntax line"
                test_lines = list(lines)
                test_lines[line_idx] = fallback
                try:
                    ast.parse("\n".join(test_lines))
                    lines[line_idx] = fallback
                    code = "\n".join(lines)
                    repaired = True
                except SyntaxError as e2:
                    if e2.lineno and e2.lineno > e.lineno:
                        lines[line_idx] = fallback
                        code = "\n".join(lines)
                        repaired = True

            if not repaired:
                break

    return code


def repair_truncated_code(code: str) -> str:
    """If code was cut off mid-expression (e.g. hitting token limits), safely trims back
    to the last complete Python statement and ensures scene functions close cleanly.
    """
    import ast

    try:
        ast.parse(code)
        return code
    except SyntaxError:
        pass

    lines = code.splitlines()
    # Attempt to trim up to 25 trailing broken lines
    for trim in range(1, min(25, len(lines))):
        candidate = "\n".join(lines[:-trim]).rstrip()
        if not candidate:
            continue

        # Try parsing candidate directly
        try:
            ast.parse(candidate)
            return candidate
        except SyntaxError:
            pass

        # Try completing scene function with 'return img'
        for indent in ("    ", "        ", "  "):
            try:
                candidate_ret = candidate + f"\n{indent}return img\n"
                ast.parse(candidate_ret)
                return candidate_ret
            except SyntaxError:
                pass

    return code


def extract_voiceover_script(code: str) -> str:
    """Extracts the English voiceover narration script from the script docstring or cues.
    Returns clean, smooth, flowing paragraphs ready for microphone recording.
    """
    # 1. Look for explicit VOICEOVER NARRATION SCRIPT docstring
    match = re.search(r'"""\s*VOICEOVER(?:\s*NARRATION)?\s*SCRIPT:?\s*([\s\S]*?)\s*"""', code, re.IGNORECASE)
    if match:
        raw_script = match.group(1).strip()
        # Clean any accidental labels or bullets
        cleaned = re.sub(r'^(?:🎙️|Scene \d+:?|Paragraph \d+:?|Spoken Script:?)\s*', '', raw_script, flags=re.MULTILINE)
        return cleaned.strip()

    # 2. Look for top-level triple-quoted docstring
    match_doc = re.search(r'^"""\s*([\s\S]*?)\s*"""', code.strip())
    if match_doc:
        doc_text = match_doc.group(1).strip()
        if len(doc_text) > 40 and not doc_text.startswith("Local AI") and not doc_text.startswith("Standalone"):
            return doc_text

    # 3. Check for narration cues array (e.g. CUES = ((start, end, "text"), ...))
    cue_matches = re.findall(r'\(\s*[\d\.]+\s*,\s*[\d\.]+\s*,\s*["\']([^"\']{4,})["\']', code)
    if cue_matches and len(cue_matches) >= 3:
        cleaned_cues = [re.sub(r"\[|\]", "", c).strip() for c in cue_matches]
        # Form smooth paragraphs
        paragraphs = []
        chunk = []
        for c in cleaned_cues:
            chunk.append(c)
            if len(chunk) >= 4 or c.endswith((".", "!", "?")):
                paragraphs.append(" ".join(chunk))
                chunk = []
        if chunk:
            paragraphs.append(" ".join(chunk))
        return "\n\n".join(paragraphs)

    return (
        "Voiceover script not detected in code docstring.\n"
        "You can read your creative brief directly as your narration, or generate with the new template."
    )


def build_user_prompt(user_input: str, style_theme: str = "Modern Tech Dark") -> str:
    """Builds the exact user prompt sent to the LLM. Returned as-is so the UI can show it."""
    clean_input = user_input.strip()
    return f"""Write a complete Python procedural motion graphics script for the following request:

--- USER REQUEST ---
{clean_input}
--------------------

STYLE THEME: {style_theme}

REQUIREMENTS:
1. SPOKEN EN-VOICEOVER SCRIPT: In the top docstring, write a natural spoken English voiceover script formatted as smooth, continuous flowing paragraphs (NO choppy scene labels, NO tone metadata). Make it ready to speak directly into a microphone.
2. ZERO AUDIO IN PYTHON: Do NOT write any audio synthesis, wave, or text-to-speech code in Python. All voice is recorded separately by the creator.
3. Target vertical format 1080x1920 (9:16 Shorts) at 30 FPS.
4. Create dedicated procedural scene functions:
   - def scene_1(progress: float, time_s: float) -> Image.Image:
   - def scene_2(progress: float, time_s: float) -> Image.Image:
   - etc.
5. Every scene MUST have a unique, centered visual composition (e.g. device frames, cards, badges, connected nodes, animated arrows).
6. CLEAR READABLE ON-SCREEN WORDS: Every scene MUST feature large, high-contrast on-screen text words (bold title, explanatory subtitles, and labeled graphic nodes) so viewers can easily read the words and follow the concept on mobile vertical screens.
7. Smooth animations using `progress` (0.0 to 1.0) and pulsing with `math.sin(time_s * 4.0)`.

Output ONLY valid, executable Python code with no markdown formatting and no conversational preamble.
"""


def generate_motion_script_stream(
    user_input: str,
    model: str = DEFAULT_MODEL,
    style_theme: str = "Modern Tech Dark",
) -> Generator[Dict[str, Any], None, None]:
    """Streams script generation, yielding intermediate states with cumulative raw response text.
    Each yield is a dict with keys: status, raw_response, elapsed.
    Final yield adds: code, line_count, saved_path, generation_time.
    """
    prompt = build_user_prompt(user_input, style_theme)
    t0 = time.time()
    last_raw = ""

    for cumulative_text in query_llm_stream(prompt, VISUAL_SCRIPT_SYSTEM_PROMPT, model=model):
        last_raw = cumulative_text
        yield {
            "status": "streaming",
            "raw_response": cumulative_text,
            "elapsed": time.time() - t0,
        }

    # Streaming finished — clean and save
    cleaned_code = clean_script_code(last_raw)
    duration = time.time() - t0
    clean_input = user_input.strip()

    slug = re.sub(r"[^\w\s-]", "", clean_input).strip().lower()
    slug = re.sub(r"[-\s]+", "_", slug)[:30] or "motion_script"
    ts = int(time.time())
    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)
    saved_path = scripts_dir / f"{slug}_{ts}.py"
    with open(saved_path, "w", encoding="utf-8") as f:
        f.write(cleaned_code)

    yield {
        "status": "complete",
        "raw_response": last_raw,
        "code": cleaned_code,
        "line_count": len(cleaned_code.splitlines()),
        "saved_path": str(saved_path),
        "generation_time": duration,
        "elapsed": duration,
    }


def generate_motion_script(
    user_input: str,
    model: str = DEFAULT_MODEL,
    style_theme: str = "Modern Tech Dark",
) -> Dict[str, Any]:
    """Generates a standalone procedural Python motion graphics script from user prompt."""
    clean_input = user_input.strip()
    t0 = time.time()

    prompt = build_user_prompt(clean_input, style_theme)

    raw_output = query_llm(prompt, VISUAL_SCRIPT_SYSTEM_PROMPT, model=model)
    cleaned_code = clean_script_code(raw_output)
    duration = time.time() - t0

    # Auto-save script to scripts/ folder
    slug = re.sub(r"[^\w\s-]", "", clean_input).strip().lower()
    slug = re.sub(r"[-\s]+", "_", slug)[:30] or "motion_script"
    ts = int(time.time())

    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)
    saved_path = scripts_dir / f"{slug}_{ts}.py"

    with open(saved_path, "w", encoding="utf-8") as f:
        f.write(cleaned_code)

    return {
        "user_input": clean_input,
        "model": model,
        "style_theme": style_theme,
        "generation_time": duration,
        "code": cleaned_code,
        "line_count": len(cleaned_code.splitlines()),
        "saved_path": str(saved_path),
    }
