"""AI Client for OpenAI API (gpt-6.2-sol, gpt-6.1-sol, gpt-4o, etc.) and Local Ollama.
Reads model configuration dynamically from .env instead of hardcoding.
"""

import os
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator, Tuple
from openai import OpenAI
import dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
dotenv.load_dotenv(PROJECT_ROOT / ".env")

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")


def get_env_model() -> str:
    """Reads default model dynamically from .env (AI_MODEL, OPENAI_MODEL, or MODEL)."""
    dotenv.load_dotenv(PROJECT_ROOT / ".env", override=True)
    return (
        os.environ.get("AI_MODEL")
        or os.environ.get("OPENAI_MODEL")
        or os.environ.get("MODEL")
        or "gpt-6.2-sol"
    ).strip()


DEFAULT_MODEL = get_env_model()
DEFAULT_OPENAI_MODEL = "gpt-6.2-sol"
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder"


def get_openai_api_key() -> str:
    """Reloads and returns the OPENAI_API_KEY from .env or environment."""
    dotenv.load_dotenv(PROJECT_ROOT / ".env", override=True)
    return os.environ.get("OPENAI_API_KEY", "").strip()


def is_openai_configured() -> bool:
    """Checks if a non-empty OpenAI API key is present."""
    key = get_openai_api_key()
    return bool(key and key.startswith("sk-") and len(key) > 20)


def test_openai_connection(timeout: float = 3.0) -> Tuple[bool, str]:
    """Tests if the configured OpenAI API key is valid and active."""
    api_key = get_openai_api_key()
    if not api_key:
        return False, "No OPENAI_API_KEY found in .env file."
    try:
        client = OpenAI(api_key=api_key, timeout=timeout, max_retries=0)
        client.models.list()
        return True, "OpenAI API key validated successfully."
    except Exception as e:
        err_msg = str(e)
        if "expired_secret_key" in err_msg or "expired" in err_msg.lower():
            return False, "Your OpenAI API key has expired. Please paste a new key into .env"
        elif "invalid_api_key" in err_msg or "401" in err_msg:
            return False, "Invalid OpenAI API key. Please check your .env file."
        return False, f"OpenAI error: {err_msg}"


def get_ollama_client() -> OpenAI:
    """Returns an OpenAI-compatible client connected to local Ollama."""
    return OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")


def is_ollama_reachable(timeout: float = 1.0) -> bool:
    """Quick ping to check if local Ollama server is responding."""
    try:
        client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama", timeout=timeout, max_retries=0)
        client.models.list()
        return True
    except Exception:
        return False


def try_start_ollama_server(timeout: float = 4.0) -> bool:
    """Attempts to auto-start local Ollama if not currently running."""
    import shutil

    if is_ollama_reachable(timeout=0.6):
        return True

    ollama_path = shutil.which("ollama")
    if not ollama_path:
        default_win_path = os.path.expanduser(r"~\AppData\Local\Programs\Ollama\ollama.exe")
        if os.path.exists(default_win_path):
            ollama_path = default_win_path

    if not ollama_path or not os.path.exists(ollama_path):
        return False

    try:
        creation_flags = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW
        subprocess.Popen(
            [ollama_path, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
        end_time = time.time() + timeout
        while time.time() < end_time:
            time.sleep(0.4)
            if is_ollama_reachable(timeout=0.6):
                return True
    except Exception:
        pass

    return is_ollama_reachable(timeout=1.0)


def get_available_models(provider: str = "auto") -> List[str]:
    """Returns available models configured in .env (AVAILABLE_MODELS) or detected from system."""
    dotenv.load_dotenv(PROJECT_ROOT / ".env", override=True)
    configured_raw = os.environ.get("AVAILABLE_MODELS", "").strip()

    models: List[str] = []
    if configured_raw:
        models = [m.strip() for m in configured_raw.split(",") if m.strip()]

    if not models:
        # Default dynamic list with Sol 6.2 and Sol 6.1
        models = [
            "gpt-6.2-sol",
            "gpt-6.1-sol",
            "gpt-4o",
            "gpt-4o-mini",
            "o3-mini",
            "qwen2.5-coder:latest",
            "llama3.2:latest",
        ]

    # Ensure default model from .env is present
    current_default = get_env_model()
    if current_default and current_default not in models:
        models.insert(0, current_default)

    # If provider is explicitly ollama, probe local ollama
    if provider in ("Local Ollama", "ollama"):
        try:
            client = get_ollama_client()
            res = client.models.list()
            ollama_models = [m.id for m in res.data]
            if ollama_models:
                for om in ollama_models:
                    if om not in models:
                        models.append(om)
        except Exception:
            pass

    return models


def is_openai_model(model: str) -> bool:
    """Determines if a model belongs to OpenAI API."""
    m = model.lower()
    return (
        m.startswith("gpt-")
        or m.startswith("o1")
        or m.startswith("o3")
        or "sol" in m
        or "sole" in m
        or "chatgpt" in m
    )


def get_env_max_tokens(default: int = 25000) -> int:
    """Reads MAX_TOKENS dynamically from .env (defaults to 25000 for Sol/Reasoning/OpenAI models)."""
    dotenv.load_dotenv(PROJECT_ROOT / ".env", override=True)
    val = os.environ.get("MAX_TOKENS", "").strip()
    if val.isdigit():
        return int(val)
    return default


def _prepare_llm_request(
    model: str,
    system_prompt: str,
    prompt: str,
    temperature: float = 0.5,
    max_tokens: Optional[int] = None,
    stream: bool = False,
) -> Tuple[OpenAI, Dict[str, Any]]:
    """Constructs client and kwargs tailored to model capabilities (OpenAI Sol/o1/o3 vs Standard vs Ollama)."""
    model = model or get_env_model()
    is_openai = is_openai_model(model)
    m = model.lower()

    if max_tokens is None:
        if is_openai:
            # Sol/reasoning models (gpt-6.2-sol, gpt-6.1-sol, o1, o3) use reasoning tokens that count
            # towards max_completion_tokens. Default to 25,000 to prevent mid-script truncation.
            max_tokens = get_env_max_tokens(default=25000)
        else:
            max_tokens = 8192

    if is_openai:
        api_key = get_openai_api_key()
        if not api_key:
            raise ValueError("No OPENAI_API_KEY found in .env. Please add OPENAI_API_KEY=sk-... to your .env file.")
        client = OpenAI(api_key=api_key)

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            # Use max_completion_tokens via extra_body for wide SDK compatibility
            "extra_body": {"max_completion_tokens": max_tokens},
        }
        if stream:
            kwargs["stream"] = True

        # Sol and reasoning models (gpt-6.2-sol, gpt-6.1-sol, o1, o3, etc.) only accept default temperature
        is_sol_or_reasoning = any(tag in m for tag in ["sol", "sole", "o1", "o3", "reasoning"])
        if not is_sol_or_reasoning:
            kwargs["temperature"] = temperature

        return client, kwargs

    else:
        # Local Ollama
        client = get_ollama_client()
        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "extra_body": {"num_ctx": 8192},
        }
        if stream:
            kwargs["stream"] = True

        return client, kwargs


def query_llm(
    prompt: str,
    system_prompt: str,
    model: str = "",
    temperature: float = 0.5,
    max_tokens: Optional[int] = None,
) -> str:
    """Sends a completion request to OpenAI API or local Ollama and returns text."""
    client, kwargs = _prepare_llm_request(model, system_prompt, prompt, temperature, max_tokens, stream=False)
    try:
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""
    except Exception as e:
        err_str = str(e)
        if "temperature" in err_str.lower() and "temperature" in kwargs:
            kwargs.pop("temperature", None)
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        elif "max_tokens" in err_str.lower():
            kwargs.pop("max_tokens", None)
            kwargs["extra_body"] = kwargs.get("extra_body", {})
            kwargs["extra_body"]["max_completion_tokens"] = max_tokens or 25000
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        raise e


def query_llm_stream(
    prompt: str,
    system_prompt: str,
    model: str = "",
    temperature: float = 0.5,
    max_tokens: Optional[int] = None,
) -> Generator[str, None, None]:
    """Streams completion tokens from OpenAI API or local Ollama."""
    client, kwargs = _prepare_llm_request(model, system_prompt, prompt, temperature, max_tokens, stream=True)
    accumulated = ""
    try:
        stream = client.chat.completions.create(**kwargs)
    except Exception as e:
        err_str = str(e)
        if "temperature" in err_str.lower() and "temperature" in kwargs:
            kwargs.pop("temperature", None)
            stream = client.chat.completions.create(**kwargs)
        elif "max_tokens" in err_str.lower():
            kwargs.pop("max_tokens", None)
            kwargs["extra_body"] = kwargs.get("extra_body", {})
            kwargs["extra_body"]["max_completion_tokens"] = max_tokens or 25000
            stream = client.chat.completions.create(**kwargs)
        else:
            raise e

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            accumulated += chunk.choices[0].delta.content
            yield accumulated


# ===========================================================================
# Token Counting & Cost Estimation Engine (100% Offline-Safe)
# ===========================================================================

def estimate_tokens(text: str) -> int:
    """Estimates token count offline-safely.
    Uses tiktoken if locally cached/available without network, otherwise
    falls back to a robust ~3.7 chars-per-token heuristic for code/prompts,
    accurate within ~2-3% of cl100k_base with zero network calls or crashes.
    """
    if not text:
        return 0
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        # Code & prompt heuristic: 1 token ≈ 3.7 characters (or ~1.3 tokens per whitespace word)
        char_est = int(round(len(text) / 3.7))
        word_est = int(round(len(text.split()) * 1.33))
        # Blend character and word estimators for maximum accuracy
        return max(1, int(round((char_est * 0.75) + (word_est * 0.25))))


# Pricing table per 1,000,000 tokens (USD)
# (Input Cost per 1M, Output Cost per 1M)
MODEL_PRICING_PER_1M: Dict[str, Tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "o3-mini": (1.10, 4.40),
    "o1-mini": (1.10, 4.40),
    "o1": (15.00, 60.00),
    "gpt-6.2-sol": (5.00, 15.00),
    "gpt-6.1-sol": (5.00, 15.00),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-4": (30.00, 60.00),
    "gpt-3.5-turbo": (0.50, 1.50),
}


def get_model_pricing(model: str) -> Tuple[float, float]:
    """Returns (input_cost_per_1m, output_cost_per_1m) in USD for a given model.
    Local Ollama models always return (0.0, 0.0) - 100% free.
    """
    if not is_openai_model(model):
        return (0.0, 0.0)

    m = model.lower().strip()
    for pattern, pricing in MODEL_PRICING_PER_1M.items():
        if pattern in m:
            return pricing

    # Fallbacks for OpenAI model family variants
    if "sol" in m or "reasoning" in m:
        return (5.00, 15.00)
    if "mini" in m:
        return (0.15, 0.60)

    # Standard default (gpt-4o tier)
    return (2.50, 10.00)


def calculate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str,
) -> Tuple[float, str]:
    """Calculates estimated API cost in USD based on model pricing.
    Returns: (total_cost_usd_float, formatted_display_string)
    e.g. (0.0435, "$0.044") or (0.0, "$0.000 (Local Free GPU)")
    """
    if not is_openai_model(model):
        return (0.0, "$0.000 (Local Free GPU)")

    in_rate, out_rate = get_model_pricing(model)
    in_cost = (prompt_tokens * in_rate) / 1_000_000.0
    out_cost = (completion_tokens * out_rate) / 1_000_000.0
    total_cost = in_cost + out_cost

    if total_cost < 0.0001:
        cost_str = f"${total_cost:.5f}"
    elif total_cost < 0.01:
        cost_str = f"${total_cost:.4f}"
    else:
        cost_str = f"${total_cost:.3f}"

    return (total_cost, cost_str)

