"""Local AI Motion Script Studio — n8n Node Workflow Interface.
Features an interactive visual node-based workflow canvas inspired by n8n.
Every node represents a real stage in the generation pipeline:
  [ Creative Brief ] -> [ Local Ollama ] -> [ Code Generator ] -> [ AST Validator ] -> [ Python Script ]

Connected with glowing SVG cables, real-time pulse animations, and execution states.
Framework: Gradio 6.0+ (100% Dark Theme, Zero White Boxes, 100% Offline, Pure n8n Studio)
"""

import html as html_mod
import os
import re
import sys
import time
from pathlib import Path
from typing import Generator, Tuple, Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import gradio as gr
from core.ai_client import (
    is_ollama_reachable,
    try_start_ollama_server,
    get_available_models,
    get_env_model,
    query_llm_stream,
    test_openai_connection,
    is_openai_configured,
    is_openai_model,
    get_openai_api_key,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_OLLAMA_MODEL,
    OLLAMA_BASE_URL,
    estimate_tokens,
    calculate_cost,
    get_model_pricing,
)
from core.generator import (
    build_user_prompt,
    clean_script_code,
    extract_voiceover_script,
    VISUAL_SCRIPT_SYSTEM_PROMPT,
)
from core.validator import validate_script_ast
from core.preview import (
    load_script_module,
    get_scene_names,
    render_scene_keyframe,
    generate_storyboard,
)
from core.renderer import render_video_stream

SCRIPTS_DIR = PROJECT_ROOT / "scripts"
SCRIPTS_DIR.mkdir(exist_ok=True)


def _esc(text: str) -> str:
    return html_mod.escape(str(text))


# ---------------------------------------------------------------------------
# n8n Node Canvas Renderer (100% Fit to Screen • Pro n8n Connected Workflow)
# ---------------------------------------------------------------------------

NODE_DEFS = [
    {
        "id": 1,
        "name": "Creative Brief",
        "category": "Trigger",
        "icon": "⚡",
        "badge_color": "#f59e0b",
        "default_sub": "1080x1920 Short Directives",
    },
    {
        "id": 2,
        "name": "Ollama Engine",
        "category": "Model",
        "icon": "🧠",
        "badge_color": "#ec4899",
        "default_sub": "Local GPU (127.0.0.1)",
    },
    {
        "id": 3,
        "name": "Code Synthesizer",
        "category": "Generator",
        "icon": "✨",
        "badge_color": "#8b5cf6",
        "default_sub": "Procedural Scenes & Words",
    },
    {
        "id": 4,
        "name": "AST Validator",
        "category": "Inspector",
        "icon": "🛡️",
        "badge_color": "#06b6d4",
        "default_sub": "Syntax & Scene Verifier",
    },
    {
        "id": 5,
        "name": "Python Output",
        "category": "Export",
        "icon": "💾",
        "badge_color": "#10b981",
        "default_sub": "Standalone Script File",
    },
    {
        "id": 6,
        "name": "Visual Preview",
        "category": "Storyboard",
        "icon": "🖼️",
        "badge_color": "#38bdf8",
        "default_sub": "Keyframe Scrubber",
    },
    {
        "id": 7,
        "name": "Video Renderer",
        "category": "MP4 Output",
        "icon": "🎬",
        "badge_color": "#a855f7",
        "default_sub": "1080x1920 30FPS MP4",
    },
]


def render_n8n_workflow_canvas(
    active_node: int = 0,
    status: str = "idle",
    custom_details: Dict[int, str] = None,
    error_msg: str = "",
    model: str = "",
) -> str:
    """Renders an interactive n8n-style node workflow canvas with connected SVG wires."""
    custom_details = custom_details or {}

    nodes_html = []
    num_nodes = len(NODE_DEFS)

    # Dynamic adaptation for Node 2 based on selected model
    is_openai = is_openai_model(model) if model else True

    for idx, raw_node in enumerate(NODE_DEFS, 1):
        node = dict(raw_node)
        nid = node["id"]

        if nid == 2:
            if is_openai:
                node["name"] = "OpenAI Engine"
                node["category"] = "Cloud API"
                node["icon"] = "🌐"
                node["badge_color"] = "#10b981"
                if nid not in custom_details:
                    node["default_sub"] = f"{model or 'gpt-4o'} (OpenAI)"
            else:
                node["name"] = "Ollama Engine"
                node["category"] = "Local GPU"
                node["icon"] = "🧠"
                node["badge_color"] = "#ec4899"
                if nid not in custom_details:
                    node["default_sub"] = f"{model or 'qwen2.5-coder'} (127.0.0.1)"

        # Determine node state
        if status == "error" and nid == active_node:
            state_class = "node-error"
            status_text = "Failed"
            status_badge_class = "status-tag-error"
        elif nid < active_node or (active_node >= 5 and status == "success" and nid <= active_node):
            state_class = "node-success"
            status_text = "Completed"
            status_badge_class = "status-tag-success"
        elif nid == active_node and status in ("running", "streaming"):
            state_class = "node-active"
            status_text = "Executing..."
            status_badge_class = "status-tag-active"
        else:
            state_class = "node-idle"
            status_text = "Waiting"
            status_badge_class = "status-tag-idle"

        sub_detail = custom_details.get(nid, node["default_sub"])

        # Ports on left and right edges
        in_port = '<div class="node-port port-in"></div>' if idx > 1 else ""
        out_port = '<div class="node-port port-out"></div>' if idx < num_nodes else ""

        # Connecting SVG Cable between nodes
        cable_html = ""
        if idx < num_nodes:
            wire_class = "wire-idle"
            if status == "error" and nid == active_node:
                wire_class = "wire-error"
            elif nid < active_node or (active_node >= 5 and status == "success" and nid < active_node):
                wire_class = "wire-done"
            elif nid == active_node and status in ("running", "streaming"):
                wire_class = "wire-active"

            cable_html = f"""
            <div class="wire-wrapper">
                <svg class="wire-svg" viewBox="0 0 36 24" preserveAspectRatio="none">
                    <path class="wire-bg" d="M 0 12 L 36 12" />
                    <path class="wire-line {wire_class}" d="M 0 12 L 36 12" />
                </svg>
            </div>
            """

        node_card = f"""
        <div class="workflow-node {state_class}">
            {in_port}
            {out_port}
            <div class="node-header">
                <span class="node-icon-badge" style="background:{node['badge_color']}20; color:{node['badge_color']}; border-color:{node['badge_color']}50;">
                    {node['icon']}
                </span>
                <div class="node-title-group">
                    <span class="node-category" style="color:{node['badge_color']};">{node['category']}</span>
                    <span class="node-title">{node['name']}</span>
                </div>
            </div>
            <div class="node-body">
                <span class="node-sub">{_esc(sub_detail)}</span>
            </div>
            <div class="node-footer">
                <span class="node-status-badge {status_badge_class}">{status_text}</span>
            </div>
        </div>
        {cable_html}
        """
        nodes_html.append(node_card)

    error_banner_html = ""
    if status == "error" and error_msg:
        error_banner_html = f'<div class="workflow-alert-bar">⚠️ Node Error: {_esc(error_msg)}</div>'

    status_badge_text = (
        '● Pipeline Running' if status in ('running', 'streaming')
        else ('✓ Workflow Completed' if status == 'success'
        else ('✕ Execution Failed' if status == 'error'
        else '○ Workflow Ready'))
    )

    return f"""
    <div class="n8n-canvas-container">
        <div class="n8n-canvas-header">
            <div class="canvas-title-group">
                <span class="workflow-tag">N8N ANIMATION WORKFLOW GRAPH</span>
                <span class="workflow-status">{status_badge_text}</span>
            </div>
            <span class="workflow-meta">7 Connected Animation Pipeline Nodes</span>
        </div>
        <div class="n8n-nodes-row">
            {"".join(nodes_html)}
        </div>
        {error_banner_html}
    </div>
    """


# ---------------------------------------------------------------------------
# High-End n8n Studio CSS (Zero White Boxes • Full Width • Glowing Wires)
# ---------------------------------------------------------------------------
N8N_STUDIO_CSS = """
/* =========================================================================
   Base Canvas & Theme Reset (Eradicate all white frames & low contrast)
   ========================================================================= */
:root, .dark, html, body {
    --n8n-bg: #090e17;
    --n8n-surface: #101826;
    --n8n-panel: #162032;
    --n8n-border: #223249;
    --n8n-text: #f8fafc;
    --n8n-muted: #94a3b8;
    --n8n-accent: #f97316;
    --n8n-blue: #38bdf8;
    --n8n-green: #10b981;
    --n8n-red: #ef4444;

    /* Gradio Theme Variable Overrides */
    --body-background-fill: #090e17 !important;
    --background-fill-primary: #090e17 !important;
    --background-fill-secondary: #101826 !important;
    --block-background-fill: #101826 !important;
    --block-border-color: #223249 !important;
    --border-color-primary: #223249 !important;
    --border-color-accent: #38bdf8 !important;
    --input-background-fill: #0d1422 !important;
    --input-border-color: #223249 !important;
    --block-label-text-color: #94a3b8 !important;
    --body-text-color: #f8fafc !important;
    --block-title-text-color: #f8fafc !important;
    --input-placeholder-color: #64748b !important;
    --button-primary-background-fill: #f97316 !important;
    --button-primary-text-color: #ffffff !important;
    --shadow-drop: none !important;
}

body, html, .gradio-container {
    background-color: #090e17 !important;
    color: #f8fafc !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    max-width: 100% !important;
    width: 100% !important;
    padding: 12px 18px !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
}

/* Eradicate any white outer boxes from Gradio containers */
.block, .gr-block, .gr-box, fieldset.block, div.block, .form, .gr-form, .gr-panel,
div[class*="block"], div[class*="gr-box"], div[class*="form"] {
    background: #101826 !important;
    background-color: #101826 !important;
    border: 1px solid #223249 !important;
    color: #f8fafc !important;
    box-shadow: none !important;
}

/* Textarea in Creative Brief: Seamless Dark Input */
textarea, .gr-textbox textarea {
    background: #0d1422 !important;
    background-color: #0d1422 !important;
    border: 1px solid #223249 !important;
    color: #f8fafc !important;
    font-size: 13.5px !important;
    line-height: 1.5 !important;
    border-radius: 8px !important;
    box-shadow: none !important;
}

textarea:focus, .gr-textbox textarea:focus {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25) !important;
    outline: none !important;
}

/* Labels: High Contrast & Professional */
label, .label, span.label-text, span.text-gray-500, label span, .gr-input-label {
    color: #94a3b8 !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.6px !important;
    background: transparent !important;
}

/* =========================================================================
   Dropdowns: High-Contrast, Pure White Text across all engines
   ========================================================================= */
.gr-dropdown,
.gr-dropdown *,
select,
.wrap,
.wrap-inner,
div[data-testid*="dropdown"],
div[class*="dropdown"],
div[class*="select"] {
    background-color: #0d1422 !important;
    border-color: #223249 !important;
}

.gr-dropdown input,
.gr-dropdown input[type="text"],
.gr-dropdown input[readonly],
.gr-dropdown .single-select,
.gr-dropdown span,
.gr-dropdown div,
div[data-testid*="dropdown"] span,
div[data-testid*="dropdown"] input,
div[data-testid*="dropdown"] .single-select {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    opacity: 1 !important;
    background: transparent !important;
}

.gr-dropdown svg,
div[data-testid*="dropdown"] svg {
    fill: #94a3b8 !important;
    stroke: #94a3b8 !important;
}

/* Dropdown Options Menu */
.options, .item, ul[role="listbox"], li[role="option"] {
    background-color: #101826 !important;
    color: #f8fafc !important;
    border-color: #223249 !important;
}

.options .item:hover,
li[role="option"]:hover,
.options .item.selected,
li[role="option"][aria-selected="true"] {
    background-color: #1e293b !important;
    color: #38bdf8 !important;
}

/* =========================================================================
   n8n Top Navigation Bar
   ========================================================================= */
.n8n-navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 18px;
    background: #101826;
    border: 1px solid #223249;
    border-radius: 10px;
    margin-bottom: 12px;
}

.nav-left h1 {
    font-size: 17px;
    font-weight: 700;
    color: #f8fafc;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
}

.nav-left p {
    font-size: 12px;
    color: #94a3b8;
    margin: 2px 0 0 0;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 11.5px;
    font-weight: 600;
}
.status-pill.online {
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #34d399;
}
.status-pill.offline {
    background: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.35);
    color: #f87171;
}

/* =========================================================================
   n8n Workflow Canvas (100% Fit to Screen • Zero Horizontal Scrollbar)
   ========================================================================= */
.n8n-canvas-container {
    background-color: #0b111c;
    background-image: radial-gradient(rgba(255, 255, 255, 0.08) 1.2px, transparent 1.2px);
    background-size: 18px 18px;
    border: 1px solid #223249;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 14px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    overflow-x: hidden;
    width: 100%;
    box-sizing: border-box;
}

.n8n-canvas-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.workflow-tag {
    font-size: 10.5px;
    font-weight: 700;
    color: #f97316;
    background: rgba(249, 115, 22, 0.15);
    border: 1px solid rgba(249, 115, 22, 0.3);
    padding: 3px 8px;
    border-radius: 4px;
    margin-right: 10px;
    letter-spacing: 0.5px;
}

.workflow-status {
    font-size: 12px;
    color: #f8fafc;
    font-weight: 500;
}

.workflow-meta {
    font-size: 11.5px;
    color: #94a3b8;
}

.n8n-nodes-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    min-width: 0;
    padding: 4px 0;
    box-sizing: border-box;
}

/* Individual n8n Node Card (Fluid & Responsive) */
.workflow-node {
    flex: 1 1 0;
    min-width: 90px;
    max-width: 175px;
    background: #141d2c;
    border: 1.5px solid #24354a;
    border-radius: 9px;
    padding: 7px 8px;
    position: relative;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
    transition: all 0.25s ease-in-out;
    box-sizing: border-box;
}

.workflow-node.node-active {
    border-color: #38bdf8;
    box-shadow: 0 0 16px rgba(56, 189, 248, 0.35);
    background: #152336;
}

.workflow-node.node-success {
    border-color: #10b981;
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.25);
}

.workflow-node.node-error {
    border-color: #ef4444;
    box-shadow: 0 0 16px rgba(239, 68, 68, 0.35);
}

/* Ports on node edges */
.node-port {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #0b111c;
    border: 2px solid #475569;
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    z-index: 5;
    transition: all 0.2s ease;
}
.port-in { left: -5px; }
.port-out { right: -5px; }

.node-active .node-port, .node-success .node-port {
    border-color: #38bdf8;
    background: #0284c7;
}

/* Node Contents */
.node-header {
    display: flex;
    align-items: center;
    gap: 7px;
    margin-bottom: 5px;
}

.node-icon-badge {
    width: 25px;
    height: 25px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    border: 1px solid;
    flex-shrink: 0;
}

.node-title-group {
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.node-category {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.node-title {
    font-size: 11.5px;
    font-weight: 700;
    color: #ffffff;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.node-body {
    margin-bottom: 5px;
    min-height: 24px;
}

.node-sub {
    font-size: 10.5px;
    color: #cbd5e1;
    font-weight: 500;
    line-height: 1.35;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.node-active .node-sub {
    color: #bae6fd;
}

.node-footer {
    display: flex;
    justify-content: flex-end;
}

.node-status-badge {
    font-size: 9.5px;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 12px;
}

.status-tag-idle {
    background: rgba(148, 163, 184, 0.12);
    color: #64748b;
}

.status-tag-active {
    background: rgba(56, 189, 248, 0.2);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.4);
    animation: pulseGlow 1.2s infinite;
}

.status-tag-success {
    background: rgba(16, 185, 129, 0.2);
    color: #34d399;
}

.status-tag-error {
    background: rgba(239, 68, 68, 0.2);
    color: #f87171;
}

/* Connecting Wires & Pulse Animation */
.wire-wrapper {
    flex: 0 1 18px;
    min-width: 6px;
    height: 24px;
    display: flex;
    align-items: center;
}

.wire-svg {
    width: 100%;
    height: 24px;
    overflow: visible;
}

.wire-bg {
    stroke: #223249;
    stroke-width: 2.5;
    fill: none;
}

.wire-line {
    stroke-width: 2.5;
    fill: none;
    transition: all 0.3s ease;
}

.wire-idle { stroke: #223249; }
.wire-done { stroke: #10b981; }
.wire-error { stroke: #ef4444; }

@keyframes dashFlow {
    from { stroke-dashoffset: 24; }
    to { stroke-dashoffset: 0; }
}

.wire-active {
    stroke: #38bdf8;
    stroke-dasharray: 6, 4;
    animation: dashFlow 0.8s linear infinite;
}

@keyframes pulseGlow {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

.workflow-alert-bar {
    margin-top: 10px;
    padding: 8px 12px;
    border-radius: 6px;
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.4);
    color: #fca5a5;
    font-size: 12px;
}

/* =========================================================================
   n8n Node Inspector Tabs (Replaces generic 2-column workbench!)
   ========================================================================= */
.n8n-inspector-container {
    background: #101826 !important;
    border: 1px solid #223249 !important;
    border-radius: 12px !important;
    padding: 14px 18px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    margin-top: 10px !important;
}

/* Tabs Navigation Styling */
div.tab-nav {
    border-bottom: 1px solid #223249 !important;
    margin-bottom: 14px !important;
}

button.tab-nav {
    color: #94a3b8 !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    border-bottom: 2px solid transparent !important;
    padding: 9px 16px !important;
    transition: all 0.2s ease !important;
}

button.tab-nav.selected {
    color: #f97316 !important;
    border-bottom: 2px solid #f97316 !important;
    background: rgba(249, 115, 22, 0.08) !important;
    border-radius: 6px 6px 0 0 !important;
}

/* Execute Button */
.btn-execute-workflow {
    background: linear-gradient(135deg, #f97316 0%, #ea580c 100%) !important;
    color: #ffffff !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px 20px !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 3px 12px rgba(234, 88, 12, 0.35) !important;
    width: 100% !important;
    margin-top: 10px !important;
}

.btn-execute-workflow:hover:not(:disabled) {
    background: linear-gradient(135deg, #fb923c 0%, #f97316 100%) !important;
    transform: translateY(-1px) !important;
}

.btn-execute-workflow:disabled {
    opacity: 0.55 !important;
    cursor: not-allowed !important;
}

/* 1-Click Download Button (Clean, Modern, No Giant White Box!) */
.btn-download-script {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    color: #ffffff !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px 18px !important;
    margin-top: 12px !important;
    box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3) !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
    text-align: center !important;
    cursor: pointer !important;
}

.btn-download-script:hover {
    background: linear-gradient(135deg, #34d399 0%, #10b981 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(16, 185, 129, 0.4) !important;
}

/* Detailed Inspection View (What We Send vs What We Receive) */
.detailed-exchange-wrapper {
    width: 100%;
    margin-top: 4px;
}
.exchange-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}
@media (max-width: 960px) {
    .exchange-grid {
        grid-template-columns: 1fr;
    }
}
.exchange-card {
    background: #141d2c;
    border: 1px solid #223249;
    border-radius: 10px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}
.exchange-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.card-badge {
    font-size: 11px;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 6px;
    letter-spacing: 0.5px;
}
.send-badge {
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.35);
}
.recv-badge {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.35);
}
.streaming-badge {
    background: rgba(56, 189, 248, 0.2);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.5);
    animation: pulseGlow 1.2s infinite;
}
.idle-badge {
    background: rgba(148, 163, 184, 0.12);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.25);
}
.err-badge {
    background: rgba(239, 68, 68, 0.2);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.5);
}
.card-meta {
    font-size: 11.5px;
    color: #94a3b8;
}
.card-meta code {
    background: #090e17;
    color: #38bdf8;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
}
.exchange-meta-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 10px;
}
.tag-pill {
    font-size: 10.5px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 6px;
}
.pill-info {
    background: rgba(56, 189, 248, 0.1);
    color: #7dd3fc;
    border: 1px solid rgba(56, 189, 248, 0.25);
}
.pill-success {
    background: rgba(16, 185, 129, 0.1);
    color: #6ee7b7;
    border: 1px solid rgba(16, 185, 129, 0.25);
}
.pill-warning {
    background: rgba(245, 158, 11, 0.1);
    color: #fcd34d;
    border: 1px solid rgba(245, 158, 11, 0.25);
}
.pill-neutral {
    background: rgba(148, 163, 184, 0.1);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.2);
}
.exchange-section-title {
    font-size: 11px;
    font-weight: 700;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 8px 0 5px 0;
}
.exchange-code-box {
    background: #090e17;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 10px 12px;
    color: #cbd5e1;
    font-family: "JetBrains Mono", Consolas, monospace;
    font-size: 11.5px;
    line-height: 1.5;
    max-height: 260px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-word;
    margin: 0;
}
.user-prompt-box {
    max-height: 220px;
}
.response-box {
    max-height: 380px;
    color: #e2e8f0;
}
.system-prompt-details {
    margin-top: 10px;
    border: 1px solid #223249;
    border-radius: 6px;
    background: #090e17;
    overflow: hidden;
}
.system-prompt-summary {
    cursor: pointer;
    padding: 8px 12px;
    font-size: 11px;
    font-weight: 700;
    color: #94a3b8;
    background: #111a28;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    user-select: none;
}
.system-prompt-summary:hover {
    color: #38bdf8;
    background: #142236;
}
.system-prompt-box {
    max-height: 200px;
    border: none;
    border-top: 1px solid #1e293b;
    border-radius: 0;
}
.scenes-breakdown-box {
    margin-top: 10px;
    padding: 10px 12px;
    background: #090e17;
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 6px;
}
.scenes-title {
    font-size: 11px;
    font-weight: 700;
    color: #6ee7b7;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    display: block;
    margin-bottom: 6px;
}
.scenes-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}
.scene-pill {
    background: rgba(16, 185, 129, 0.15);
    color: #a7f3d0;
    border: 1px solid rgba(16, 185, 129, 0.35);
    font-size: 11px;
    font-family: "JetBrains Mono", Consolas, monospace;
    padding: 2px 8px;
    border-radius: 4px;
}

/* Token Counting & OpenAI Cost Breakdown Card */
.token-cost-card {
    margin-top: 10px;
    padding: 10px 14px;
    background: #090e17;
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 8px;
}
.token-cost-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    font-weight: 700;
    color: #38bdf8;
    margin-bottom: 8px;
    letter-spacing: 0.5px;
}
.token-cost-model {
    font-size: 10.5px;
    color: #94a3b8;
    background: #131d2e;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: "JetBrains Mono", Consolas, monospace;
}
.token-cost-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
}
@media (max-width: 768px) {
    .token-cost-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}
.token-stat-item {
    background: #111a28;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 6px 10px;
    display: flex;
    flex-direction: column;
}
.token-stat-label {
    font-size: 10px;
    color: #94a3b8;
    text-transform: uppercase;
    font-weight: 600;
}
.token-stat-val {
    font-size: 12.5px;
    color: #f1f5f9;
    font-weight: 600;
    font-family: "JetBrains Mono", Consolas, monospace;
    margin-top: 2px;
}
.token-stat-cost {
    font-size: 12.5px;
    color: #34d399;
    font-weight: 700;
    font-family: "JetBrains Mono", Consolas, monospace;
    margin-top: 2px;
}
.token-cost-highlight {
    border-color: rgba(16, 185, 129, 0.35);
    background: rgba(16, 185, 129, 0.08);
}

/* Output Code Styling */
.gr-code {
    background: #080d16 !important;
    border: 1px solid #223249 !important;
    border-radius: 8px !important;
    font-family: "JetBrains Mono", Consolas, monospace !important;
}

.status-hud-banner {
    padding: 9px 14px;
    border-radius: 6px;
    font-size: 12.5px;
    line-height: 1.4;
    margin-bottom: 12px;
}
.hud-info {
    background: rgba(56, 189, 248, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.25);
    color: #7dd3fc;
}
.hud-success {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.25);
    color: #6ee7b7;
}
.hud-error {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.25);
    color: #fca5a5;
}

/* Voiceover Teleprompter Box Styling */
.voiceover-highlight-box {
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.35);
    border-radius: 8px;
    padding: 12px 14px;
    margin: 10px 0;
}
.voiceover-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    font-weight: 700;
    color: #6ee7b7;
    margin-bottom: 8px;
}
.voiceover-meta {
    font-size: 10.5px;
    color: #94a3b8;
}
.voiceover-content {
    font-size: 12.5px;
    line-height: 1.6;
    color: #f1f5f9;
    white-space: pre-wrap;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

/* Render Video Button */
.btn-render-video {
    background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%) !important;
    color: #ffffff !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px 20px !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 3px 12px rgba(99, 102, 241, 0.35) !important;
    width: 100% !important;
}

.btn-render-video:hover:not(:disabled) {
    background: linear-gradient(135deg, #a78bfa 0%, #818cf8 100%) !important;
    transform: translateY(-1px) !important;
}

.btn-render-video:disabled {
    opacity: 0.55 !important;
    cursor: not-allowed !important;
}

/* Secondary Action Button */
.btn-secondary-action {
    background: #1e293b !important;
    color: #e2e8f0 !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 8px 16px !important;
    transition: all 0.15s ease !important;
}

.btn-secondary-action:hover {
    background: #334155 !important;
    color: #38bdf8 !important;
    border-color: #38bdf8 !important;
}

/* Storyboard Gallery & Inspector */
.storyboard-gallery {
    background: #090e17 !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
    padding: 10px !important;
}

/* Proceed to Render Button */
.btn-proceed-render {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    color: #ffffff !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 13px 20px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4) !important;
    width: 100% !important;
    margin-top: 10px !important;
    text-align: center !important;
}

.btn-proceed-render:hover {
    background: linear-gradient(135deg, #34d399 0%, #10b981 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(16, 185, 129, 0.5) !important;
}

/* Real-time Render Progress Card */
.render-progress-card {
    background: #0d1522;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 14px 16px;
    margin: 12px 0 8px 0;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}
.render-card-complete {
    border-color: rgba(16, 185, 129, 0.5);
    background: rgba(16, 185, 129, 0.08);
}
.render-card-error {
    border-color: rgba(239, 68, 68, 0.5);
    background: rgba(239, 68, 68, 0.08);
}
.render-progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}
.render-progress-title {
    font-size: 13px;
    font-weight: 700;
    color: #38bdf8;
    display: flex;
    align-items: center;
    gap: 6px;
}
.render-progress-pct {
    font-size: 14px;
    font-weight: 800;
    color: #38bdf8;
    font-family: "JetBrains Mono", Consolas, monospace;
}
.progress-track {
    width: 100%;
    height: 10px;
    background: #1e293b;
    border-radius: 6px;
    overflow: hidden;
    margin-bottom: 8px;
    border: 1px solid #334155;
}
.progress-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
    border-radius: 6px;
    transition: width 0.25s ease;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
}
.progress-fill-complete {
    background: linear-gradient(90deg, #10b981 0%, #34d399 100%) !important;
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.5) !important;
}
.render-progress-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11.5px;
    color: #94a3b8;
}
.render-progress-msg {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #cbd5e1;
}
.render-progress-fps {
    font-family: "JetBrains Mono", Consolas, monospace;
    font-weight: 600;
    color: #38bdf8;
}

input[type="range"] {
    accent-color: #38bdf8 !important;
}
"""


# ---------------------------------------------------------------------------
# Detailed Inspection View Renderer (What We Send vs What We Receive)
# ---------------------------------------------------------------------------

def render_detailed_exchange_view(
    model: str = "",
    style_theme: str = "",
    actual_prompt: str = "",
    response_text: str = "",
    line_count: int = 0,
    elapsed: float = 0.0,
    is_streaming: bool = False,
    is_completed: bool = False,
    scenes: List[Dict[str, Any]] = None,
    ast_msg: str = "",
    error_msg: str = "",
    voiceover_text: str = "",
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cost_str: str = "",
) -> str:
    """Renders a comprehensive, high-transparency side-by-side view:
    Card 1: WHAT WE SEND (Model, Provider, Styles, User Prompt, Prompt Tokens, Full System Architecture Rules)
    Card 2: WHAT WE GET (Streaming/Complete status, Line counts, Output Tokens, Cost ($), Latency, AST scenes, Generated Code, Voiceover)
    """
    model = model or get_env_model()
    is_openai = is_openai_model(model)
    provider_str = "🌐 OpenAI Cloud API" if is_openai else "🧠 Local Ollama GPU (127.0.0.1)"
    prompt_len = len(actual_prompt) if actual_prompt else 0
    sys_prompt_len = len(VISUAL_SCRIPT_SYSTEM_PROMPT)

    # Right Card Status Badge
    if error_msg:
        recv_badge_class = "err-badge"
        recv_badge_text = "❌ GENERATION FAILED"
        meta_status = f"Error: {_esc(error_msg[:35])}..."
    elif is_streaming:
        recv_badge_class = "streaming-badge"
        recv_badge_text = "⚡ LIVE STREAMING RESPONSE..."
        meta_status = f"⏱️ {elapsed:.1f}s · {line_count} lines received · ~{completion_tokens:,} tokens ({cost_str or '$0.00'})"
    elif is_completed:
        recv_badge_class = "recv-badge"
        recv_badge_text = "✓ RESPONSE COMPLETE & VERIFIED"
        total_tok = prompt_tokens + completion_tokens
        meta_status = f"⏱️ {elapsed:.1f}s · {line_count} lines · {total_tok:,} tokens ({cost_str or '$0.00'})"
    else:
        recv_badge_class = "idle-badge"
        recv_badge_text = "○ AWAITING WORKFLOW EXECUTION"
        meta_status = "Standing by for Node 1 trigger"

    # AST Status Pill
    if scenes and len(scenes) > 0:
        ast_pill_class = "pill-success"
        ast_pill_text = f"🛡️ AST: {len(scenes)} Scenes Verified"
    elif is_streaming:
        ast_pill_class = "pill-info"
        ast_pill_text = "🛡️ AST: Streaming code..."
    elif ast_msg:
        ast_pill_class = "pill-warning"
        ast_pill_text = f"🛡️ AST: {_esc(ast_msg)}"
    else:
        ast_pill_class = "pill-neutral"
        ast_pill_text = "🛡️ AST: Ready to parse"

    # Token & Cost Pills for Left & Right Cards
    prompt_token_pill = f'<span class="tag-pill pill-info">📥 Prompt: ~{prompt_tokens:,} tokens</span>' if prompt_tokens > 0 else ""
    out_token_pill = f'<span class="tag-pill pill-info">📤 Output: ~{completion_tokens:,} tokens</span>' if completion_tokens > 0 else ""
    cost_pill = f'<span class="tag-pill pill-success">💰 Cost: {_esc(cost_str)}</span>' if cost_str else ""

    # Scene Breakdown Tags
    scene_tags_html = ""
    scene_breakdown_html = ""
    if scenes and len(scenes) > 0:
        scene_pills = "".join(
            f'<span class="scene-pill">🎬 {_esc(s.get("name", "scene"))} ({s.get("duration", "auto")}s)</span>'
            for s in scenes
        )
        scene_tags_html = f'<span class="tag-pill pill-success">🎬 {len(scenes)} Scenes Detected</span>'
        scene_breakdown_html = f"""
        <div class="scenes-breakdown-box">
            <span class="scenes-title">🎬 AST Verified Procedural Scene Functions:</span>
            <div class="scenes-list">
                {scene_pills}
            </div>
        </div>
        """

    # Spoken Voiceover Narration Box
    voiceover_html = ""
    if voiceover_text and len(voiceover_text.strip()) > 10:
        voiceover_html = f"""
        <div class="voiceover-highlight-box">
            <div class="voiceover-header">
                <span>🎙️ SPOKEN VOICEOVER NARRATION (Continuous English Paragraphs)</span>
                <span class="voiceover-meta">Ready to record with your mic</span>
            </div>
            <div class="voiceover-content">{_esc(voiceover_text)}</div>
        </div>
        """

    # Dedicated Token & Cost Card
    token_cost_card_html = ""
    if completion_tokens > 0 or is_completed:
        total_tokens = prompt_tokens + completion_tokens
        token_cost_card_html = f"""
        <div class="token-cost-card">
            <div class="token-cost-header">
                <span>💰 TOKEN USAGE & API COST BREAKDOWN</span>
                <span class="token-cost-model">{_esc(model)}</span>
            </div>
            <div class="token-cost-grid">
                <div class="token-stat-item">
                    <span class="token-stat-label">Prompt Tokens</span>
                    <span class="token-stat-val">~{prompt_tokens:,}</span>
                </div>
                <div class="token-stat-item">
                    <span class="token-stat-label">Generated Code</span>
                    <span class="token-stat-val">~{completion_tokens:,}</span>
                </div>
                <div class="token-stat-item">
                    <span class="token-stat-label">Total Billed</span>
                    <span class="token-stat-val font-bold">~{total_tokens:,}</span>
                </div>
                <div class="token-stat-item token-cost-highlight">
                    <span class="token-stat-label">Estimated Cost</span>
                    <span class="token-stat-cost">{_esc(cost_str or "$0.00")}</span>
                </div>
            </div>
        </div>
        """

    display_prompt = _esc(actual_prompt) if actual_prompt else '<span style="color:#64748b; font-style:italic;">No creative brief submitted yet. Configure Node 1 and click Execute Workflow.</span>'
    display_response = _esc(response_text) if response_text else '<span style="color:#64748b; font-style:italic;">Awaiting model response stream... Python animation code will render here line-by-line.</span>'

    return f"""
    <div class="detailed-exchange-wrapper">
        <div class="exchange-grid">
            <!-- LEFT CARD: WHAT WE SEND -->
            <div class="exchange-card send-card">
                <div class="exchange-card-header">
                    <span class="card-badge send-badge">📤 WHAT WE SEND TO AI</span>
                    <span class="card-meta">Model: <code>{_esc(model)}</code></span>
                </div>

                <div class="exchange-meta-tags">
                    <span class="tag-pill pill-info">{provider_str}</span>
                    <span class="tag-pill pill-info">🎨 Theme: {_esc(style_theme or "Modern Tech Dark")}</span>
                    <span class="tag-pill pill-info">📐 1080x1920 (9:16 Shorts)</span>
                    <span class="tag-pill pill-info">📊 Prompt: {prompt_len} chars</span>
                    {prompt_token_pill}
                </div>

                <div class="exchange-section-title">1. Formatted User Animation Brief</div>
                <pre class="exchange-code-box user-prompt-box">{display_prompt}</pre>

                <details class="system-prompt-details">
                    <summary class="system-prompt-summary">⚙️ Full System Prompt & Visual Architecture Rules ({sys_prompt_len} chars)</summary>
                    <pre class="exchange-code-box system-prompt-box">{_esc(VISUAL_SCRIPT_SYSTEM_PROMPT)}</pre>
                </details>
            </div>

            <!-- RIGHT CARD: WHAT WE GET -->
            <div class="exchange-card recv-card">
                <div class="exchange-card-header">
                    <span class="card-badge {recv_badge_class}">{recv_badge_text}</span>
                    <span class="card-meta">{meta_status}</span>
                </div>

                <div class="exchange-meta-tags">
                    <span class="tag-pill {ast_pill_class}">{ast_pill_text}</span>
                    <span class="tag-pill pill-info">⏱️ {elapsed:.1f}s</span>
                    <span class="tag-pill pill-info">📝 {line_count} lines</span>
                    {out_token_pill}
                    {cost_pill}
                    {scene_tags_html}
                </div>

                {token_cost_card_html}
                {voiceover_html}

                <div class="exchange-section-title">2. Generated Python Script (Pure Visual PIL Code)</div>
                <pre class="exchange-code-box response-box">{display_response}</pre>

                {scene_breakdown_html}
            </div>
        </div>
    </div>
    """


# ---------------------------------------------------------------------------
# Real n8n Workflow Streaming Execution
# ---------------------------------------------------------------------------

def run_n8n_workflow_stream(
    prompt: str,
    model: str,
    style_theme: str,
) -> Generator[Tuple[Any, ...], None, None]:
    """Executes the 5 real n8n workflow nodes and streams execution state to the canvas."""

    node_details = {
        1: "Prompt ready",
        2: f"{model} (Ready)",
        3: "Streaming engine ready",
        4: "AST syntax analyzer",
        5: "Save & download",
        6: "Keyframe storyboard",
        7: "1080x1920 MP4 video",
    }

    clean_prompt = prompt.strip() if prompt else ""

    logs: List[str] = []

    def _log(msg: str):
        print(msg, flush=True)
        logs.append(msg)

    # STAGE 0: Validation of Node 1
    if not clean_prompt:
        error_hud = '<div class="status-hud-banner hud-error">⚠️ <strong>Workflow Stopped at Node 1:</strong> Please enter a creative brief to execute the workflow.</div>'
        canvas_html = render_n8n_workflow_canvas(
            active_node=1,
            status="error",
            custom_details={1: "Error: Brief is empty"},
            error_msg="Creative brief is empty. Please describe what you want to animate.",
        )
        _log(f"[{time.strftime('%H:%M:%S')}] ❌ Validation Error: Creative brief is empty.")
        empty_exchange = render_detailed_exchange_view(
            model=model,
            style_theme=style_theme,
            error_msg="Creative brief is empty. Please describe what you want to animate.",
        )
        yield (
            "# Enter a creative brief on the left to execute the n8n workflow.",
            canvas_html,
            error_hud,
            empty_exchange,
            "\n".join(logs),
            gr.update(visible=False, value=None),
            gr.update(interactive=True, value="⚡ Execute Workflow"),
            "0 lines",
            gr.update(selected="tab-node1"),
            "",
            gr.update(),
            gr.update(),
            gr.update(),
        )
        return

    _log(f"[{time.strftime('%H:%M:%S')}] ⚡ Triggering n8n motion script synthesis pipeline...")

    # NODE 1: Creative Brief formatting
    actual_prompt = build_user_prompt(clean_prompt, style_theme)
    prompt_tokens = estimate_tokens(actual_prompt) + estimate_tokens(VISUAL_SCRIPT_SYSTEM_PROMPT)
    _log(f"[{time.strftime('%H:%M:%S')}] ✔ Node 1 (Creative Brief): Formatted prompt ({len(actual_prompt)} chars · ~{prompt_tokens:,} prompt tokens).")
    _log("\n" + "=" * 70)
    _log(f"📝 FORMATTED USER PROMPT SENT TO AI (Model: {model}, Theme: {style_theme}):")
    _log("=" * 70)
    _log(actual_prompt)
    _log("=" * 70 + "\n")

    node_details[1] = f"{len(clean_prompt)} chars · ~{prompt_tokens:,} tok"
    canvas_html = render_n8n_workflow_canvas(
        active_node=1,
        status="running",
        custom_details=node_details,
        model=model,
    )

    exchange_view = render_detailed_exchange_view(
        model=model,
        style_theme=style_theme,
        actual_prompt=actual_prompt,
        response_text="",
        line_count=0,
        elapsed=0.0,
        is_streaming=False,
        prompt_tokens=prompt_tokens,
    )

    hud = '<div class="status-hud-banner hud-info">⚡ <strong>Node 1 (Brief):</strong> Formatted procedural animation constraints. Moving to Node 2...</div>'

    yield (
        "# Node 1 executed. Passing data to Node 2...",
        canvas_html,
        hud,
        exchange_view,
        "\n".join(logs),
        gr.update(visible=False, value=None),
        gr.update(interactive=False, value="⏳ Node 1 -> Node 2..."),
        "0 lines",
        gr.update(selected="tab-node1"),
        "",
        gr.update(),
        gr.update(),
        gr.update(),
    )
    time.sleep(0.3)

    # NODE 2: Connection & Model Check (OpenAI Cloud API or Local Ollama)
    if is_openai_model(model):
        _log(f"[{time.strftime('%H:%M:%S')}] 🌐 Node 2 (OpenAI Engine): Checking OpenAI API for model '{model}'...")
        node_details[2] = f"{model} (Connecting...)"
        canvas_html = render_n8n_workflow_canvas(
            active_node=2,
            status="running",
            custom_details=node_details,
            model=model,
        )
        hud = f'<div class="status-hud-banner hud-info">🌐 <strong>Node 2 (OpenAI Engine):</strong> Authenticating API key for <code>{_esc(model)}</code>...</div>'

        yield (
            f"# Authenticating OpenAI API for {model}...",
            canvas_html,
            hud,
            exchange_view,
            "\n".join(logs),
            gr.update(visible=False, value=None),
            gr.update(interactive=False, value=f"⏳ Node 2 ({model})..."),
            "0 lines",
            gr.update(selected="tab-node1"),
            "",
            gr.update(),
            gr.update(),
            gr.update(),
        )

        ok, msg = test_openai_connection(timeout=3.5)
        if not ok:
            _log(f"[{time.strftime('%H:%M:%S')}] ❌ Node 2 OpenAI Key Error: {msg}")
            _log(f"[{time.strftime('%H:%M:%S')}] 💡 Fix: Open your .env file and paste a valid OPENAI_API_KEY=sk-...")
            node_details[2] = "Key Error"
            canvas_html = render_n8n_workflow_canvas(
                active_node=2,
                status="error",
                custom_details=node_details,
                error_msg=msg,
                model=model,
            )
            err_hud = f'<div class="status-hud-banner hud-error">❌ <strong>Node 2 (OpenAI Error):</strong> {msg}</div>'
            err_exchange = render_detailed_exchange_view(
                model=model,
                style_theme=style_theme,
                actual_prompt=actual_prompt,
                error_msg=msg,
            )
            yield (
                f"# Node 2 Error:\n# {msg}\n# Update your OPENAI_API_KEY in .env and click Execute Workflow again.",
                canvas_html,
                err_hud,
                err_exchange,
                "\n".join(logs),
                gr.update(visible=False, value=None),
                gr.update(interactive=True, value="⚡ Execute Workflow"),
                "0 lines",
                gr.update(selected="tab-logs"),
                "",
                gr.update(),
                gr.update(),
                gr.update(),
            )
            return

        _log(f"[{time.strftime('%H:%M:%S')}] ✔ Node 2: OpenAI API authenticated successfully! Model '{model}' ready.")
        node_details[2] = f"{model} (OpenAI Cloud)"

    else:
        _log(f"[{time.strftime('%H:%M:%S')}] 🔌 Node 2 (Ollama Engine): Checking server at {OLLAMA_BASE_URL}...")
        canvas_html = render_n8n_workflow_canvas(
            active_node=2,
            status="running",
            custom_details=node_details,
            model=model,
        )
        hud = f'<div class="status-hud-banner hud-info">🧠 <strong>Node 2 (Ollama Engine):</strong> Connecting to local model <code>{_esc(model)}</code>...</div>'

        yield (
            "# Connecting to local model in Node 2...",
            canvas_html,
            hud,
            exchange_view,
            "\n".join(logs),
            gr.update(visible=False, value=None),
            gr.update(interactive=False, value=f"⏳ Node 2 ({model})..."),
            "0 lines",
            gr.update(selected="tab-node1"),
            "",
            gr.update(),
            gr.update(),
            gr.update(),
        )

        # If offline, attempt to auto-start the local Ollama background daemon
        if not is_ollama_reachable(timeout=0.8):
            _log(f"[{time.strftime('%H:%M:%S')}] ⚙ Node 2: Ollama is offline. Attempting to auto-start Ollama service...")
            started = try_start_ollama_server(timeout=4.0)
            if started:
                _log(f"[{time.strftime('%H:%M:%S')}] 🚀 Auto-started Ollama background process successfully!")
            else:
                _log(f"[{time.strftime('%H:%M:%S')}] ⚠ Could not auto-start Ollama daemon.")

        if not is_ollama_reachable(timeout=1.2):
            err = f"Could not connect to Ollama at {OLLAMA_BASE_URL}. Ensure 'ollama serve' is running."
            _log(f"[{time.strftime('%H:%M:%S')}] ❌ Node 2 Connection Error: {err}")
            _log(f"[{time.strftime('%H:%M:%S')}] 💡 Fix: Open terminal or PowerShell and run: ollama serve")
            node_details[2] = "Offline error"
            canvas_html = render_n8n_workflow_canvas(
                active_node=2,
                status="error",
                custom_details=node_details,
                error_msg=err,
                model=model,
            )
            err_hud = f'<div class="status-hud-banner hud-error">❌ <strong>Node 2 Error:</strong> {err} Open terminal and run <code>ollama serve</code>.</div>'
            err_exchange = render_detailed_exchange_view(
                model=model,
                style_theme=style_theme,
                actual_prompt=actual_prompt,
                error_msg=err,
            )
            yield (
                f"# Node 2 Error:\n# {err}\n# Start Ollama and click Execute Workflow again.",
                canvas_html,
                err_hud,
                err_exchange,
                "\n".join(logs),
                gr.update(visible=False, value=None),
                gr.update(interactive=True, value="⚡ Execute Workflow"),
                "0 lines",
                gr.update(selected="tab-logs"),
                "",
                gr.update(),
                gr.update(),
                gr.update(),
            )
            return

        _log(f"[{time.strftime('%H:%M:%S')}] ✔ Node 2: Ollama connection verified. Model '{model}' ready.")
        node_details[2] = f"{model} (Connected)"

    # NODE 3: Code Synthesizer (Streaming LLM inference)
    _log(f"[{time.strftime('%H:%M:%S')}] ✨ Node 3 (Code Synthesizer): Starting streaming token synthesis with model '{model}'...")
    node_details[3] = "Streaming tokens..."
    canvas_html = render_n8n_workflow_canvas(
        active_node=3,
        status="streaming",
        custom_details=node_details,
        model=model,
    )
    hud = f'<div class="status-hud-banner hud-info">✨ <strong>Node 3 (Code Synthesizer):</strong> Streaming procedural scene functions from {model}...</div>'

    streaming_init_exchange = render_detailed_exchange_view(
        model=model,
        style_theme=style_theme,
        actual_prompt=actual_prompt,
        response_text="",
        line_count=0,
        elapsed=0.0,
        is_streaming=True,
    )

    yield (
        "# Streaming code in Node 3...",
        canvas_html,
        hud,
        streaming_init_exchange,
        "\n".join(logs),
        gr.update(visible=False, value=None),
        gr.update(interactive=False, value="⏳ Node 3 Streaming..."),
        "0 lines",
        gr.update(selected="tab-exchange"),
        "",
        gr.update(),
        gr.update(),
        gr.update(),
    )

    t0 = time.time()
    raw_response = ""
    last_update = 0

    try:
        print(f"\n[Streaming from {model}] Synthesizing Python motion script...", flush=True)
        for chunk in query_llm_stream(actual_prompt, VISUAL_SCRIPT_SYSTEM_PROMPT, model=model):
            raw_response = chunk
            now = time.time()
            if now - last_update > 0.45:
                last_update = now
                elapsed = now - t0
                line_count = len(chunk.splitlines())
                vo_live = extract_voiceover_script(chunk)
                out_tok_live = estimate_tokens(chunk)
                _, cost_live_str = calculate_cost(prompt_tokens, out_tok_live, model)

                # Live progress in console terminal
                print(f"\r  --> Streaming {model}: {line_count} lines (~{out_tok_live:,} tok · {cost_live_str}) ({elapsed:.1f}s)...", end="", flush=True)

                node_details[3] = f"{line_count} lines · ~{out_tok_live:,} tok ({cost_live_str})"
                canvas_html = render_n8n_workflow_canvas(
                    active_node=3,
                    status="streaming",
                    custom_details=node_details,
                    model=model,
                )

                stream_exchange = render_detailed_exchange_view(
                    model=model,
                    style_theme=style_theme,
                    actual_prompt=actual_prompt,
                    response_text=chunk,
                    line_count=line_count,
                    elapsed=elapsed,
                    is_streaming=True,
                    voiceover_text=vo_live,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=out_tok_live,
                    cost_str=cost_live_str,
                )

                yield (
                    f"# Streaming from Node 3... ({line_count} lines, ~{out_tok_live:,} tok, {cost_live_str}, {elapsed:.1f}s)",
                    canvas_html,
                    f'<div class="status-hud-banner hud-info">✨ <strong>Node 3:</strong> Synthesizing procedural script ({line_count} lines · ~{out_tok_live:,} tokens · {cost_live_str} · {elapsed:.1f}s)...</div>',
                    stream_exchange,
                    "\n".join(logs),
                    gr.update(visible=False, value=None),
                    gr.update(interactive=False, value=f"⏳ Node 3 ({line_count} lines · {cost_live_str})..."),
                    f"{line_count} lines · ~{out_tok_live:,} tok ({cost_live_str})",
                    gr.update(selected="tab-exchange"),
                    vo_live if len(vo_live) > 20 else gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                )
    except Exception as e:
        err = str(e)
        _log(f"\n[{time.strftime('%H:%M:%S')}] ❌ Node 3 Inference Error: {err}")
        node_details[3] = "Inference failed"
        canvas_html = render_n8n_workflow_canvas(
            active_node=3,
            status="error",
            custom_details=node_details,
            error_msg=err,
            model=model,
        )
        err_exchange = render_detailed_exchange_view(
            model=model,
            style_theme=style_theme,
            actual_prompt=actual_prompt,
            response_text=raw_response,
            line_count=len(raw_response.splitlines()) if raw_response else 0,
            elapsed=time.time() - t0,
            error_msg=err,
        )
        yield (
            f"# Node 3 Error:\n# {err}",
            canvas_html,
            f'<div class="status-hud-banner hud-error">❌ <strong>Node 3 Error:</strong> {_esc(err)}</div>',
            err_exchange,
            "\n".join(logs),
            gr.update(visible=False, value=None),
            gr.update(interactive=True, value="⚡ Execute Workflow"),
            "0 lines",
            gr.update(selected="tab-logs"),
            "",
            gr.update(),
            gr.update(),
            gr.update(),
        )
        return

    duration = time.time() - t0
    cleaned_code = clean_script_code(raw_response)
    line_count = len(cleaned_code.splitlines())
    voiceover_text = extract_voiceover_script(cleaned_code)
    words = len(voiceover_text.split())
    est_sec = max(5, round(words / 2.3))

    print() # New line after stream counter
    _log(f"[{time.strftime('%H:%M:%S')}] ✔ Node 3: Synthesized {line_count} lines of Python in {duration:.2f}s.")

    # Token & OpenAI Cost Calculation for the generated script
    completion_tokens = estimate_tokens(cleaned_code)
    total_tokens = prompt_tokens + completion_tokens
    cost_val, cost_str = calculate_cost(prompt_tokens, completion_tokens, model)

    _log(f"[{time.strftime('%H:%M:%S')}] 💰 Token Usage & API Cost Breakdown ({model}):")
    _log(f"[{time.strftime('%H:%M:%S')}]    • Prompt Tokens    : {prompt_tokens:,} tokens")
    _log(f"[{time.strftime('%H:%M:%S')}]    • Generated Code   : {completion_tokens:,} tokens ({line_count} lines)")
    _log(f"[{time.strftime('%H:%M:%S')}]    • Total Tokens     : {total_tokens:,} tokens")
    _log(f"[{time.strftime('%H:%M:%S')}]    • Estimated Cost   : {cost_str}")

    _log(f"[{time.strftime('%H:%M:%S')}] 🎙️ English Voiceover Script ({words} words, ~{est_sec}s speaking time):")
    _log("\n" + "=" * 70)
    _log(voiceover_text)
    _log("=" * 70 + "\n")
    _log(f"📥 FULL AI MODEL RESPONSE ({model} · {line_count} lines · {duration:.2f}s):")
    _log("=" * 70)
    _log(cleaned_code)
    _log("=" * 70 + "\n")
    node_details[3] = f"{line_count} lines · {total_tokens:,} tok ({cost_str})"

    final_exchange = render_detailed_exchange_view(
        model=model,
        style_theme=style_theme,
        actual_prompt=actual_prompt,
        response_text=cleaned_code,
        line_count=line_count,
        elapsed=duration,
        is_streaming=False,
        is_completed=True,
        voiceover_text=voiceover_text,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_str=cost_str,
    )

    # NODE 4: AST Validator Check
    _log(f"[{time.strftime('%H:%M:%S')}] 🛡️ Node 4 (AST Validator): Parsing abstract syntax tree for {line_count} lines...")
    node_details[4] = "Validating AST..."
    canvas_html = render_n8n_workflow_canvas(
        active_node=4,
        status="running",
        custom_details=node_details,
        model=model,
    )
    hud = f'<div class="status-hud-banner hud-info">🛡️ <strong>Node 4 (AST Validator):</strong> Verifying Python syntax tree for {line_count} lines ({total_tokens:,} tokens · {cost_str})...</div>'

    yield (
        cleaned_code,
        canvas_html,
        hud,
        final_exchange,
        "\n".join(logs),
        gr.update(visible=False, value=None),
        gr.update(interactive=False, value="⏳ Node 4 Checking..."),
        f"{line_count} lines · {total_tokens:,} tok ({cost_str})",
        gr.update(selected="tab-exchange"),
        voiceover_text,
        gr.update(),
        gr.update(),
        gr.update(),
    )
    time.sleep(0.3)

    is_valid, val_msg, scenes = validate_script_ast(cleaned_code)
    scene_names = [s["name"] for s in scenes] if scenes else []

    _log(f"[{time.strftime('%H:%M:%S')}] 🔍 Node 4 Verification: {val_msg}")
    if scenes:
        _log(f"[{time.strftime('%H:%M:%S')}] 🎬 Detected {len(scenes)} procedural scene functions: {', '.join(scene_names)}")

    # Auto-save script file
    slug = re.sub(r"[^\w\s-]", "", clean_prompt).strip().lower()
    slug = re.sub(r"[-\s]+", "_", slug)[:30] or "motion_script"
    ts = int(time.time())
    saved_path = SCRIPTS_DIR / f"{slug}_{ts}.py"
    with open(saved_path, "w", encoding="utf-8") as f:
        f.write(cleaned_code)
    saved_full_path = str(saved_path.resolve())

    _log(f"[{time.strftime('%H:%M:%S')}] 💾 Node 5 (Export): Script written to {saved_full_path}")

    # Build finalized rich exchange view with scenes and AST report
    verified_exchange = render_detailed_exchange_view(
        model=model,
        style_theme=style_theme,
        actual_prompt=actual_prompt,
        response_text=cleaned_code,
        line_count=line_count,
        elapsed=duration,
        is_streaming=False,
        is_completed=True,
        scenes=scenes,
        ast_msg=val_msg,
        voiceover_text=voiceover_text,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_str=cost_str,
    )

    # Generate visual storyboards and initial keyframe
    storyboard_items = []
    default_scene = scene_names[0] if scene_names else None
    first_frame = None
    try:
        storyboard_items = generate_storyboard(cleaned_code, progress=0.5)
        if default_scene:
            first_frame = render_scene_keyframe(cleaned_code, default_scene, 0.5)
    except Exception as e:
        _log(f"[{time.strftime('%H:%M:%S')}] ⚠ Storyboard generation error: {e}")

    # NODE 5 & NODE 6: Final Output, Storyboards & Download
    if is_valid:
        node_details[4] = f"✔ {len(scenes)} scenes verified"
        node_details[5] = saved_path.name
        node_details[6] = f"✔ {len(scenes)} scenes storyboarded"
        node_details[7] = "Ready to render MP4"

        canvas_html = render_n8n_workflow_canvas(
            active_node=6,
            status="success",
            custom_details=node_details,
            model=model,
        )

        hud = (
            f'<div class="status-hud-banner hud-success">'
            f'✓ <strong>Workflow Executed Successfully:</strong> Generated {line_count} lines with {len(scenes)} scenes '
            f'({", ".join(scene_names)}) in {duration:.1f}s | <strong>{total_tokens:,} tokens ({cost_str})</strong>. Saved to <code>{saved_path.name}</code>.'
            f'</div>'
        )
        _log(f"[{time.strftime('%H:%M:%S')}] 🎉 Workflow Completed Successfully in {duration:.1f}s | {total_tokens:,} tokens ({cost_str})!")

        yield (
            cleaned_code,
            canvas_html,
            hud,
            verified_exchange,
            "\n".join(logs),
            gr.update(value=saved_full_path, visible=True),
            gr.update(interactive=True, value="⚡ Execute Workflow"),
            f"{line_count} lines · {len(scenes)} scenes · {total_tokens:,} tok ({cost_str}) · {duration:.1f}s",
            gr.update(selected="tab-preview"),
            voiceover_text,
            storyboard_items,
            gr.update(choices=scene_names, value=default_scene),
            first_frame,
        )
    else:
        node_details[4] = "Syntax warning"
        node_details[5] = saved_path.name

        canvas_html = render_n8n_workflow_canvas(
            active_node=4,
            status="error",
            custom_details=node_details,
            error_msg=val_msg,
            model=model,
        )

        hud = (
            f'<div class="status-hud-banner hud-error">'
            f'⚠️ <strong>Node 4 Warning:</strong> {val_msg} '
            f'Script is saved to <code>{saved_path.name}</code> for review. | {total_tokens:,} tokens ({cost_str})'
            f'</div>'
        )
        _log(f"[{time.strftime('%H:%M:%S')}] ⚠️ Node 4 Warning: {val_msg}")

        yield (
            cleaned_code,
            canvas_html,
            hud,
            verified_exchange,
            "\n".join(logs),
            gr.update(value=saved_full_path, visible=True),
            gr.update(interactive=True, value="⚡ Execute Workflow"),
            f"{line_count} lines · {total_tokens:,} tok ({cost_str}) · Warning",
            gr.update(selected="tab-preview"),
            voiceover_text,
            storyboard_items,
            gr.update(choices=scene_names, value=default_scene),
            first_frame,
        )



# ---------------------------------------------------------------------------
# Visual Preview & Video Render Controller Callbacks
# ---------------------------------------------------------------------------

def on_scrub_change(code: str, scene_name: str, progress: float):
    """Renders a single scene keyframe on-demand when scrubbing progress (0.0 to 1.0)."""
    if not code or not scene_name:
        return None
    try:
        return render_scene_keyframe(
            code, scene_name, progress=float(progress), time_s=float(progress) * 4.0
        )
    except Exception as e:
        print(f"Scrub preview error: {e}", flush=True)
        return None


def on_refresh_storyboard(code: str):
    """Refreshes the full storyboard gallery from the current script code in the editor."""
    if not code or not code.strip():
        return [], gr.update(choices=[], value=None), None, '<div class="status-hud-banner hud-error">⚠️ No Python code found to preview.</div>'

    scenes = get_scene_names(code)
    if not scenes:
        return [], gr.update(choices=[], value=None), None, '<div class="status-hud-banner hud-error">⚠️ No <code>def scene_N()</code> functions found in script.</div>'

    try:
        gallery = generate_storyboard(code, progress=0.5)
        default_scene = scenes[0]
        frame = render_scene_keyframe(code, default_scene, 0.5)
        msg = f'<div class="status-hud-banner hud-success">✔ Generated instant storyboard for {len(scenes)} scenes ({", ".join(scenes)}).</div>'
        return gallery, gr.update(choices=scenes, value=default_scene), frame, msg
    except Exception as e:
        return [], gr.update(choices=[], value=None), None, f'<div class="status-hud-banner hud-error">⚠️ Preview Error: {_esc(str(e))}</div>'


def render_progress_bar_html(
    pct: int,
    cur: int,
    total: int,
    fps_rate: float,
    msg: str,
    status: str = "rendering",
    error_msg: str = "",
    complete_info: Optional[Dict[str, Any]] = None,
) -> str:
    """Renders a high-tech animated progress bar or completion card for backend video synthesis."""
    if status == "error":
        return f"""
        <div class="render-progress-card render-card-error">
            <div class="render-progress-header">
                <span class="render-progress-title" style="color:#f87171;">❌ Video Rendering Error</span>
            </div>
            <div style="font-size:12.5px; color:#fca5a5; margin-top:6px; line-height:1.4;">
                {_esc(error_msg)}
            </div>
        </div>
        """

    if status == "complete":
        c = complete_info or {}
        duration_sec = c.get("duration_sec", 0.0)
        render_sec = c.get("render_sec", 0.0)
        size_mb = c.get("size_mb", 0.0)
        has_audio = c.get("has_audio", False)
        audio_text = " • Muxed with Audio" if has_audio else " • Silent Video"
        return f"""
        <div class="render-progress-card render-card-complete">
            <div class="render-progress-header">
                <span class="render-progress-title" style="color:#34d399;">🎉 Video Synthesis 100% Completed!</span>
                <span class="render-progress-pct" style="color:#34d399;">100%</span>
            </div>
            <div class="progress-track">
                <div class="progress-bar-fill progress-fill-complete" style="width: 100%;"></div>
            </div>
            <div class="render-progress-footer">
                <span class="render-progress-msg" style="color:#a7f3d0;">✓ Duration: {duration_sec:.1f}s · Render Time: {render_sec:.1f}s · Size: {size_mb:.2f} MB{audio_text}</span>
                <span class="render-progress-fps" style="color:#6ee7b7;">Ready to Play & Download Below 👇</span>
            </div>
        </div>
        """

    clamped_pct = max(0, min(100, int(round(pct))))
    return f"""
    <div class="render-progress-card">
        <div class="render-progress-header">
            <span class="render-progress-title">⚡ Rendering High-Res 1080x1920 Video (Backend In-Memory)...</span>
            <span class="render-progress-pct">{clamped_pct}%</span>
        </div>
        <div class="progress-track">
            <div class="progress-bar-fill" style="width: {clamped_pct}%;"></div>
        </div>
        <div class="render-progress-footer">
            <span class="render-progress-msg">🎬 Frame {cur}/{total} · {_esc(msg)}</span>
            <span class="render-progress-fps">{fps_rate:.1f} FPS</span>
        </div>
    </div>
    """


def run_video_render(
    code: str,
    scene_duration: float,
    audio_path: Optional[str] = None,
    model: str = "",
):
    """Streams in-memory FFmpeg frame-by-frame video synthesis directly to MP4 output with live progress bar and n8n canvas updates."""
    if not code or not code.strip():
        err_hud = render_progress_bar_html(
            0, 0, 0, 0, "", status="error", error_msg="No Python script code to render. Generate or paste a script first."
        )
        yield (
            err_hud,
            gr.update(visible=False, value=None),
            gr.update(visible=False, value=None),
            gr.update(interactive=True, value="🎬 Preview Looks Good! Render Video Now (.mp4)"),
            gr.update(),
        )
        return

    scenes = get_scene_names(code)
    if not scenes:
        err_hud = render_progress_bar_html(
            0, 0, 0, 0, "", status="error", error_msg="No 'def scene_N()' functions found in the script."
        )
        yield (
            err_hud,
            gr.update(visible=False, value=None),
            gr.update(visible=False, value=None),
            gr.update(interactive=True, value="🎬 Preview Looks Good! Render Video Now (.mp4)"),
            gr.update(),
        )
        return

    node_details = {
        1: "Prompt ready",
        2: f"{model or 'AI Model'} (Completed)",
        3: "Code synthesized",
        4: f"✔ {len(scenes)} scenes verified",
        5: "Script exported",
        6: f"✔ {len(scenes)} scenes storyboarded",
        7: "Starting render...",
    }

    init_canvas = render_n8n_workflow_canvas(
        active_node=7,
        status="running",
        custom_details=node_details,
        model=model,
    )

    total_est_frames = len(scenes) * max(1, int(round(float(scene_duration) * 30)))
    init_hud = render_progress_bar_html(
        0, 0, total_est_frames, 0.0,
        f"Initializing in-memory FFmpeg pipeline for {len(scenes)} scenes ({scene_duration}s/scene)..."
    )

    yield (
        init_hud,
        gr.update(visible=False, value=None),
        gr.update(visible=False, value=None),
        gr.update(interactive=False, value="⏳ Rendering Video in Backend..."),
        init_canvas,
    )

    for update in render_video_stream(
        script_code=code,
        duration_per_scene=float(scene_duration),
        fps=30,
        voiceover_audio_path=audio_path,
    ):
        status = update.get("status")
        if status == "rendering":
            pct = update.get("progress_pct", 0)
            cur = update.get("current_frame", 0)
            total = update.get("total_frames", 1)
            fps_rate = update.get("fps_rate", 0.0)
            msg = update.get("message", "")

            progress_hud = render_progress_bar_html(
                pct, cur, total, fps_rate, msg, status="rendering"
            )
            node_details[7] = f"Frame {cur}/{total} ({pct}%)"
            active_canvas = render_n8n_workflow_canvas(
                active_node=7,
                status="running",
                custom_details=node_details,
                model=model,
            )
            yield (
                progress_hud,
                gr.update(visible=False, value=None),
                gr.update(visible=False, value=None),
                gr.update(interactive=False, value=f"⏳ Rendering ({pct}%)..."),
                active_canvas,
            )
        elif status == "complete":
            video_path = update.get("video_path")
            total_sec = update.get("duration_sec", 0)
            render_sec = update.get("render_time", 0)
            size_mb = update.get("file_size_mb", 0)
            has_audio = update.get("has_audio", False)

            complete_info = {
                "duration_sec": total_sec,
                "render_sec": render_sec,
                "size_mb": size_mb,
                "has_audio": has_audio,
            }
            complete_hud = render_progress_bar_html(
                100, update.get("total_frames", 0), update.get("total_frames", 0),
                0.0, "Render completed", status="complete", complete_info=complete_info
            )

            node_details[7] = f"✔ {size_mb:.1f} MB MP4"
            done_canvas = render_n8n_workflow_canvas(
                active_node=7,
                status="success",
                custom_details=node_details,
                model=model,
            )
            yield (
                complete_hud,
                gr.update(visible=True, value=video_path),
                gr.update(visible=True, value=video_path),
                gr.update(interactive=True, value="🎬 Preview Looks Good! Render Video Now (.mp4)"),
                done_canvas,
            )
            return
        elif status == "error":
            err_msg = update.get("error", "Unknown render error")
            err_hud = render_progress_bar_html(
                0, 0, 0, 0, "", status="error", error_msg=err_msg
            )
            node_details[7] = "Render error"
            err_canvas = render_n8n_workflow_canvas(
                active_node=7,
                status="error",
                custom_details=node_details,
                error_msg=err_msg,
                model=model,
            )
            yield (
                err_hud,
                gr.update(visible=False, value=None),
                gr.update(visible=False, value=None),
                gr.update(interactive=True, value="🎬 Preview Looks Good! Render Video Now (.mp4)"),
                err_canvas,
            )
            return


# ---------------------------------------------------------------------------
# Studio Application Construction (Pure n8n Workflow Studio)
# ---------------------------------------------------------------------------

def build_studio():
    openai_ok, openai_msg = test_openai_connection(timeout=1.0)
    ollama_ok = is_ollama_reachable(timeout=0.5)

    models = get_available_models()
    default_model = get_env_model()
    if default_model not in models:
        models.insert(0, default_model)

    if openai_ok:
        status_pill = f'<div class="status-pill online">● OpenAI API Active ({default_model})</div>'
    elif is_openai_configured():
        status_pill = f'<div class="status-pill offline" title="Update OPENAI_API_KEY in .env">⚠ OpenAI Key Expired (Check .env)</div>'
    elif ollama_ok:
        status_pill = '<div class="status-pill online">● Ollama Online (Local GPU)</div>'
    else:
        status_pill = '<div class="status-pill offline">○ AI Offline (Configure .env or Ollama)</div>'

    head_scripts = """
    <script>
    (function() {
        function enforceDark() {
            document.documentElement.classList.add('dark');
            document.body.classList.add('dark');
            try {
                localStorage.setItem('gradio_theme', 'dark');
            } catch(e) {}
        }
        enforceDark();
        document.addEventListener('DOMContentLoaded', enforceDark);
        window.addEventListener('load', enforceDark);
    })();
    </script>
    """

    with gr.Blocks(title="Motion Script Studio — n8n Workflow") as demo:
        # Top Navigation Bar
        gr.HTML(f"""
        <div class="n8n-navbar">
            <div class="nav-left">
                <h1>🔀 Motion Script Studio</h1>
                <p>Node-based AI animation workflow • Configured via .env ({default_model}) • Standalone Python Output</p>
            </div>
            <div>
                {status_pill}
            </div>
        </div>
        """)

        # n8n Workflow Canvas (Interactive connected nodes with glowing wires, 100% fit to screen)
        workflow_canvas = gr.HTML(render_n8n_workflow_canvas(0, "idle", model=default_model))

        # Real-time Execution Status HUD Banner
        status_hud = gr.HTML(
            '<div class="status-hud-banner hud-info">Workflow Ready. Configure your Creative Brief on Node 1 and click <strong>Execute Workflow</strong>.</div>'
        )

        # UNIFIED N8N NODE INSPECTOR (Zero generic 2-column workbench!)
        with gr.Tabs(selected="tab-node1", elem_classes=["n8n-inspector-container"]) as inspector_tabs:
            # TAB 1: NODE 1 CONFIGURATION (Creative Brief & Model Settings)
            with gr.Tab("⚡ Node 1: Creative Brief & Model", id="tab-node1"):
                with gr.Row():
                    with gr.Column(scale=7):
                        prompt_input = gr.Textbox(
                            label="Creative Brief",
                            placeholder=(
                                "Example:\n"
                                "Explain how Redis in-memory caching works in 3 scenes:\n"
                                "Scene 1: High latency bottleneck with slow disk database queries.\n"
                                "Scene 2: Introducing an in-memory Redis cache layer in front of the database.\n"
                                "Scene 3: Sub-millisecond instant data retrieval directly from RAM."
                            ),
                            lines=8,
                            value="",
                        )
                    with gr.Column(scale=5):
                        model_selector = gr.Dropdown(
                            choices=models,
                            value=default_model,
                            label="AI Model (OpenAI API / Local Ollama)",
                        )
                        style_selector = gr.Dropdown(
                            choices=[
                                "Modern Tech Dark",
                                "Clean Minimal",
                                "Cyberpunk Neon",
                                "Gradient Flow",
                            ],
                            value="Modern Tech Dark",
                            label="Visual Style",
                        )
                        execute_btn = gr.Button(
                            "⚡ Execute Workflow",
                            variant="primary",
                            elem_classes=["btn-execute-workflow"],
                        )

            # TAB 2: VISUAL PREVIEW & VIDEO RENDER (.mp4)
            with gr.Tab("🖼️ Visual Preview & Render Video (.mp4)", id="tab-preview"):
                with gr.Row():
                    with gr.Column(scale=5):
                        scene_dropdown = gr.Dropdown(
                            choices=[],
                            value=None,
                            label="Select Scene Function to Inspect",
                        )
                        scrub_slider = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=0.5,
                            step=0.02,
                            label="Scrub Scene Progress (0.00 = Start ➔ 1.00 = End)",
                        )
                        with gr.Row():
                            scrub_refresh_btn = gr.Button(
                                "🔄 Refresh Frame",
                                variant="secondary",
                                elem_classes=["btn-secondary-action"],
                            )
                            refresh_storyboard_btn = gr.Button(
                                "📑 Refresh Storyboard",
                                variant="secondary",
                                elem_classes=["btn-secondary-action"],
                            )
                        scrub_image = gr.Image(
                            label="Live 1080x1920 Keyframe Inspector",
                            type="pil",
                            height=430,
                        )
                    with gr.Column(scale=7):
                        storyboard_gallery = gr.Gallery(
                            label="Instant Storyboard Keyframes (All Scenes Side-by-Side)",
                            columns=3,
                            height=360,
                            object_fit="contain",
                            elem_classes=["storyboard-gallery"],
                        )

                        # In-Place Video Render Controls & Live Progress
                        with gr.Accordion("⚙️ Render Settings (Duration & Optional Voiceover)", open=False):
                            with gr.Row():
                                with gr.Column(scale=5):
                                    scene_duration_slider = gr.Slider(
                                        minimum=2.0,
                                        maximum=10.0,
                                        value=4.0,
                                        step=0.5,
                                        label="Duration per Scene (seconds)",
                                    )
                                with gr.Column(scale=7):
                                    voiceover_input = gr.Audio(
                                        type="filepath",
                                        label="Optional Voiceover Audio (.mp3, .wav) — Auto Muxed",
                                    )

                        render_video_btn = gr.Button(
                            "🎬 Preview Looks Good! Render Video Now (.mp4)",
                            variant="primary",
                            elem_classes=["btn-proceed-render"],
                        )

                        # Real-Time Visual Progress Bar HUD
                        render_progress_hud = gr.HTML(
                            '<div class="render-idle-notice" style="padding:10px 14px; color:#94a3b8; font-size:12px; background:#0d1522; border:1px solid #1e293b; border-radius:8px; margin-top:8px;">'
                            '✨ When the preview looks good, click <strong>Preview Looks Good! Render Video Now (.mp4)</strong> to render directly in the backend.'
                            '</div>'
                        )

                        # In-Place Video Player & 1-Click Download
                        video_player = gr.Video(
                            label="🎬 Rendered 1080x1920 Short (.mp4)",
                            format="mp4",
                            interactive=False,
                            visible=False,
                            height=480,
                        )
                        download_video_btn = gr.DownloadButton(
                            label="📥 Download High-Resolution MP4 Video",
                            value=None,
                            visible=False,
                            elem_classes=["btn-download-script"],
                        )

            # TAB 3: VOICE-OVER SCRIPT (Continuous English Paragraphs)
            with gr.Tab("🎙️ Voiceover Script", id="tab-voiceover"):
                voiceover_box = gr.Textbox(
                    label="🎙️ Spoken English Narration Script (Continuous Paragraphs — Read into Mic)",
                    lines=12,
                    interactive=False,
                    value="Spoken English voiceover script will appear here as smooth, continuous paragraphs once generated...",
                )

            # TAB 5: NODE 5 OUTPUT (Generated Python Script & 1-Click Download)
            with gr.Tab("💾 Node 5: Python Script Output", id="tab-node5"):
                with gr.Row():
                    meta_indicator = gr.HTML('<span style="font-size:12.5px; color:#94a3b8; font-weight:600;">0 lines generated</span>')

                code_editor = gr.Code(
                    label="Standalone Procedural Script",
                    language="python",
                    value="# Generated Python script will appear here once the workflow executes...",
                    lines=20,
                )

                download_btn = gr.DownloadButton(
                    label="📥 Download Standalone Python Script (.py)",
                    value=None,
                    visible=False,
                    elem_classes=["btn-download-script"],
                )

            # TAB 6: DETAILED INSPECTION (Sent vs Received side-by-side)
            with gr.Tab("🔍 Details: Sent vs Received", id="tab-exchange"):
                exchange_display = gr.HTML(
                    render_detailed_exchange_view(
                        model=default_model,
                        style_theme="Modern Tech Dark",
                    )
                )

            # TAB 7: AST VALIDATOR & NODE LOGS
            with gr.Tab("📜 AST Validation & Node Logs", id="tab-logs"):
                console_terminal = gr.Textbox(
                    label="Execution Terminal & AST Scene Checker",
                    lines=10,
                    interactive=False,
                    value="Workflow execution logs will display here...",
                )

        # Wire workflow streaming execution (Updates 13 components smoothly)
        execute_btn.click(
            fn=run_n8n_workflow_stream,
            inputs=[prompt_input, model_selector, style_selector],
            outputs=[
                code_editor,
                workflow_canvas,
                status_hud,
                exchange_display,
                console_terminal,
                download_btn,
                execute_btn,
                meta_indicator,
                inspector_tabs,
                voiceover_box,
                storyboard_gallery,
                scene_dropdown,
                scrub_image,
            ],
        )

        # Wire interactive scrubber & storyboard refresh callbacks
        scrub_slider.change(
            fn=on_scrub_change,
            inputs=[code_editor, scene_dropdown, scrub_slider],
            outputs=[scrub_image],
        )
        scene_dropdown.change(
            fn=on_scrub_change,
            inputs=[code_editor, scene_dropdown, scrub_slider],
            outputs=[scrub_image],
        )
        scrub_refresh_btn.click(
            fn=on_scrub_change,
            inputs=[code_editor, scene_dropdown, scrub_slider],
            outputs=[scrub_image],
        )
        refresh_storyboard_btn.click(
            fn=on_refresh_storyboard,
            inputs=[code_editor],
            outputs=[storyboard_gallery, scene_dropdown, scrub_image, status_hud],
        )

        # Wire High-Resolution Video Rendering (Runs in background, shows live progress bar & in-place video player)
        render_video_btn.click(
            fn=run_video_render,
            inputs=[code_editor, scene_duration_slider, voiceover_input, model_selector],
            outputs=[render_progress_hud, video_player, download_video_btn, render_video_btn, workflow_canvas],
        )

    return demo, head_scripts


def main():
    print("\n" + "=" * 65)
    print("🎬 STARTING MOTION SCRIPT STUDIO — N8N WORKFLOW INTERFACE")
    print("=" * 65)
    print("• Style       : Interactive n8n Node Workflow Graph")
    print("• Nodes       : Brief -> Ollama -> Synthesizer -> AST -> Python File")
    print("• Engine      : Local Ollama (qwen2.5-coder streaming)")
    print("• Theme       : 100% Dark Studio (Zero White Boxes, High Contrast)")
    print("• Web Studio  : http://127.0.0.1:7860")
    print("=" * 65 + "\n")

    demo, head_scripts = build_studio()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        css=N8N_STUDIO_CSS,
        head=head_scripts,
        allowed_paths=[str(PROJECT_ROOT)],
    )


if __name__ == "__main__":
    main()
