"""
Unified provider abstraction — Groq, Claude, Gemini all return the same shape.
"""
import time
import os
from google import genai
from google.genai import types as genai_types
from anthropic import Anthropic
from groq import Groq

GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "meta-llama/llama-4-scout-17b-16e-instruct",
]
CLAUDE_MODELS = [
    "claude-sonnet-4-6",
    "claude-haiku-4-5-20251001",
]
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-pro",
]

def call_groq(prompt: str, system: str = "", model: str = GROQ_MODELS[0]) -> dict:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    t0 = time.time()
    resp = client.chat.completions.create(model=model, messages=messages)
    latency = int((time.time() - t0) * 1000)
    return {
        "provider": "Groq",
        "model": model,
        "response": resp.choices[0].message.content,
        "latency_ms": latency,
        "input_tokens": resp.usage.prompt_tokens,
        "output_tokens": resp.usage.completion_tokens,
    }

def call_claude(prompt: str, system: str = "", model: str = CLAUDE_MODELS[0]) -> dict:
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    kwargs = {"model": model, "max_tokens": 2048,
              "messages": [{"role": "user", "content": prompt}]}
    if system:
        kwargs["system"] = system
    t0 = time.time()
    resp = client.messages.create(**kwargs)
    latency = int((time.time() - t0) * 1000)
    return {
        "provider": "Claude",
        "model": model,
        "response": resp.content[0].text,
        "latency_ms": latency,
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
    }

def call_gemini(prompt: str, system: str = "", model: str = GEMINI_MODELS[0],
                fallback_to_groq: bool = True) -> dict:
    import re
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    contents = f"{system}\n\n{prompt}" if system else prompt
    t0 = time.time()
    try:
        resp = client.models.generate_content(model=model, contents=contents)
        latency = int((time.time() - t0) * 1000)
        usage = resp.usage_metadata
        return {
            "provider": "Gemini",
            "model": model,
            "response": resp.text,
            "latency_ms": latency,
            "input_tokens": getattr(usage, "prompt_token_count", 0),
            "output_tokens": getattr(usage, "candidates_token_count", 0),
        }
    except Exception as e:
        err_str = str(e)
        # Rate limit — extract retry delay and optionally fall back to Groq
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            retry_match = re.search(r"retry.*?(\d+)[. ]", err_str, re.IGNORECASE)
            retry_secs = retry_match.group(1) if retry_match else "60"
            if fallback_to_groq and os.environ.get("GROQ_API_KEY"):
                result = call_groq(prompt=prompt, system=system)
                result["response"] = f"⚠️ *Gemini rate-limited (retry in {retry_secs}s) — using Groq as fallback.*\n\n" + result["response"]
                result["provider"] = "Gemini→Groq"
                return result
            raise RuntimeError(f"Gemini rate-limited. Retry in {retry_secs}s. Add GROQ_API_KEY for automatic fallback.") from e
        raise

PROVIDERS = {
    "Groq":   {"fn": call_groq,   "models": GROQ_MODELS,   "icon": "⚡"},
    "Claude": {"fn": call_claude, "models": CLAUDE_MODELS, "icon": "🧠"},
    "Gemini": {"fn": call_gemini, "models": GEMINI_MODELS, "icon": "✨"},
}
