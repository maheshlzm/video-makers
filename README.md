# Local AI Motion Script Studio (Pure Script Mode)

A focused, local-first Python engine for **Prompt $\rightarrow$ Procedural Python Script Synthesis** powered by **Local Ollama AI (`qwen2.5-coder`)**.

**Zero Render Overhead** — Dedicated 100% to generating, inspecting, validating, and saving standalone Python motion graphic scripts.

---

## ⚡ What This Studio Does

1. **User Prompt Input**:
   - Takes any topic (e.g. *What is Docker?*, *How HTTPS Works*) or multi-scene creative director brief.
2. **Local AI Script Generation**:
   - Sends the prompt to your local Ollama instance (`qwen2.5-coder`).
   - The AI writes a standalone procedural Python script defining modular scene functions:
     ```python
     def scene_1(progress: float, time_s: float) -> Image.Image:
         img = Image.new("RGBA", (WIDTH, HEIGHT), hex_to_rgba('#0F172A'))
         draw = ImageDraw.Draw(img)
         # Visual animation logic
         return img
     ```
3. **Live AST Code Analysis & Validation**:
   - Parses the generated Python script using Python's `ast` module.
   - Verifies 100% valid Python syntax.
   - Detects and lists all defined scene functions (`scene_1`, `scene_2`, ...) and their line numbers.
4. **Live Code Inspector & Disk Saver**:
   - Full-size code inspector with Python syntax highlighting and copy button.
   - Ability to save generated scripts into `scripts/` with custom filenames.

---

## 📁 Clean Architecture

```text
pythom cvideo editor/
├── run.py                 # One-command Web Studio launcher
├── app.py                 # Gradio Web Studio (Prompt -> Script -> AST Inspector)
├── core/
│   ├── ai_client.py       # Ollama connection and model queries
│   ├── generator.py       # Visual script synthesis engine & code cleaner
│   └── validator.py       # Pure AST syntax validator & scene analyzer (Zero render)
├── primitives/
│   ├── canvas.py          # 1080x1920 layout constants (CX=540, CY=960) & color math
│   ├── typography.py      # System font loader & dynamic multi-line text wrapping
│   └── shapes.py          # Visual components (draw_card, draw_device_frame, draw_badge, draw_node)
└── requirements.txt       # Minimal dependencies (no cv2 or ffmpeg)
```

---

## 🚀 Quick Start

Launch the Web Studio with:
```bash
python run.py
```
Open **[http://127.0.0.1:7860](http://127.0.0.1:7860)** in your browser.
