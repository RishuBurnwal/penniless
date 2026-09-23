"""
llm_client.py — Multi-provider LLM client with automatic fallback

Fallback order (configurable via .env):
  1. NVIDIA   — deepseek-ai/deepseek-v4.1-flash  (nvapi key)
  2. Groq     — qwen/qwen3.8-27b                  (groq key)   ← swapped before Gemini (faster)
  3. Gemini   — gemini-2.5-flash                  (Google key)
  4. OpenAI   — gpt-4o-mini                       (openai key)
  5. Perplexity — llama-3.1-sonar-large           (pplx key)

Timeouts (per provider):
  NVIDIA   → 35s  (thinking model, slow start)
  Groq     → 30s  (fast)
  Gemini   → 45s  (can be slow on first call)
  Others   → 30s

Session log (session_log.jsonl) — every call is appended so the next AI
picks up from where this one left off.
"""
from __future__ import annotations

import concurrent.futures
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import openai
from rich.console import Console

from src.config import cfg

console = Console()

# Session log path — shared across all LLM calls so any AI can resume context
_PROJECT_ROOT = Path(__file__).parent.parent
_SESSION_LOG = _PROJECT_ROOT / "session_log.jsonl"


# ─── Session logger ───────────────────────────────────────────────────────────

def _log_session(event: str, provider: str, model: str, success: bool,
                  prompt_preview: str = "", response_preview: str = "",
                  error: str = "") -> None:
    """Append one line to session_log.jsonl for cross-AI continuity."""
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "event": event,
        "provider": provider,
        "model": model,
        "success": success,
        "prompt_preview": prompt_preview[:200],
        "response_preview": response_preview[:300],
        "error": error[:300] if error else "",
    }
    try:
        with open(_SESSION_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def load_session_context(last_n: int = 10) -> str:
    """Load last N session log entries as human-readable context string."""
    if not _SESSION_LOG.exists():
        return ""
    lines = _SESSION_LOG.read_text(encoding="utf-8").strip().splitlines()
    recent = lines[-last_n:]
    entries = []
    for line in recent:
        try:
            e = json.loads(line)
            status = "✅" if e["success"] else "❌"
            entries.append(
                f"[{e['ts']}] {status} {e['provider']}/{e['model']} — {e['event']}: "
                f"{e.get('response_preview','')[:120]}"
            )
        except Exception:
            pass
    return "\n".join(entries)


# ─── Provider registry ────────────────────────────────────────────────────────

@dataclass
class Provider:
    name: str
    api_key: str
    base_url: str
    model: str
    timeout: int = 30                        # per-provider timeout (seconds)
    extra_params: dict = field(default_factory=dict)

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)


# Ordered list — first enabled provider is tried first.
# Groq is before Gemini because it's significantly faster.
_ALL_PROVIDERS: list[Provider] = [
    Provider(
        name="NVIDIA",
        api_key=cfg.NVIDIA_API_KEY,
        base_url="https://integrate.api.nvidia.com/v1",
        model="deepseek-ai/deepseek-v4.1-flash",
        timeout=35,   # thinking model needs a bit more time
    ),
    Provider(
        name="Groq",
        api_key=cfg.GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
        model="qwen/qwen3.8-27b",
        timeout=30,
    ),
    Provider(
        name="Gemini",
        api_key=cfg.GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        model=cfg.GEMINI_MODEL,
        timeout=45,
        extra_params={"reasoning_effort": cfg.GEMINI_REASONING_EFFORT},
    ),
    Provider(
        name="OpenAI",
        api_key=cfg.OPENAI_API_KEY,
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
        timeout=30,
    ),
    Provider(
        name="Perplexity",
        api_key=cfg.PERPLEXITY_API_KEY,
        base_url="https://api.perplexity.ai",
        model="llama-3.1-sonar-large-128k-online",
        timeout=30,
    ),
]


# ─── Client ───────────────────────────────────────────────────────────────────

class LLMClient:
    """
    Sends chat messages to the first available LLM provider.
    On any error OR timeout, automatically falls back to the next provider.

    Session log (session_log.jsonl) is updated after every call so the next
    AI process can pick up context seamlessly.
    """

    def __init__(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        """Re-evaluate which providers are enabled (call after config reload)."""
        _ALL_PROVIDERS[0].api_key = cfg.NVIDIA_API_KEY
        _ALL_PROVIDERS[1].api_key = cfg.GROQ_API_KEY
        _ALL_PROVIDERS[2].api_key = cfg.GEMINI_API_KEY
        _ALL_PROVIDERS[2].model = cfg.GEMINI_MODEL
        _ALL_PROVIDERS[2].extra_params = {"reasoning_effort": cfg.GEMINI_REASONING_EFFORT}
        _ALL_PROVIDERS[3].api_key = cfg.OPENAI_API_KEY
        _ALL_PROVIDERS[4].api_key = cfg.PERPLEXITY_API_KEY
        self.providers = [p for p in _ALL_PROVIDERS if p.enabled]

    # ── Public API ────────────────────────────────────────────────────────────

    def chat(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        silent: bool = False,
    ) -> str:
        """
        Send a chat request and return the assistant reply as a string.
        Falls back through providers on any error or timeout.
        Logs every attempt to session_log.jsonl.
        """
        if not self.providers:
            raise RuntimeError(
                "No LLM provider configured. "
                "Add at least one API key to .env (NVIDIA_API_KEY, GROQ_API_KEY, GEMINI_API_KEY, …)"
            )

        full_messages: list[dict] = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        prompt_preview = (messages[-1].get("content", "") if messages else "")[:200]
        last_error: Exception | None = None

        for provider in self.providers:
            if not silent:
                effort_tag = (
                    f" (effort: {provider.extra_params.get('reasoning_effort')})"
                    if provider.extra_params.get("reasoning_effort") else ""
                )
                console.print(f"  [dim]-> [{provider.name}] {provider.model}{effort_tag} (max {provider.timeout}s)[/dim]")

            try:
                client = openai.OpenAI(
                    api_key=provider.api_key,
                    base_url=provider.base_url,
                    timeout=provider.timeout,
                )
                create_kwargs: dict = {
                    "model": provider.model,
                    "messages": full_messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
                if provider.extra_params:
                    create_kwargs.update(provider.extra_params)

                # BUG-001 fix: capture loop vars as default args (not by reference)
                # BUG-010 fix: check reasoning_content for NVIDIA thinking model
                def _call(p=provider, c=client, kw=create_kwargs) -> str:
                    resp = self._call_with_gemini_fallback(c, p, kw)
                    content = resp.choices[0].message.content or ""
                    if not content.strip():
                        # NVIDIA deepseek thinking model puts output in reasoning_content
                        content = getattr(resp.choices[0].message, "reasoning_content", "") or ""
                    if not content.strip():
                        raise ValueError(f"{p.name} returned empty output")
                    return content

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    future = ex.submit(_call)
                    try:
                        content = future.result(timeout=provider.timeout)
                    except concurrent.futures.TimeoutError:
                        raise TimeoutError(f"{provider.name} exceeded {provider.timeout}s wall-clock limit")

                _log_session("chat_ok", provider.name, provider.model, True,
                             prompt_preview, content[:300])
                return content

            except (TimeoutError, openai.APITimeoutError) as e:
                msg = f"timeout after {provider.timeout}s — trying next provider"
                console.print(f"  [yellow]⏱ {provider.name}: {msg}[/yellow]")
                _log_session("chat_timeout", provider.name, provider.model, False,
                             prompt_preview, error=msg)
                last_error = e

            except openai.AuthenticationError as e:
                msg = "authentication failed — check API key"
                console.print(f"  [red]✗ {provider.name}: {msg}[/red]")
                _log_session("chat_auth_fail", provider.name, provider.model, False,
                             prompt_preview, error=str(e)[:200])
                last_error = e

            except openai.RateLimitError as e:
                msg = "rate limit / quota exhausted"
                console.print(f"  [yellow]⚠ {provider.name}: {msg} — trying next[/yellow]")
                _log_session("chat_rate_limit", provider.name, provider.model, False,
                             prompt_preview, error=str(e)[:200])
                last_error = e

            except openai.APIConnectionError as e:
                msg = "connection error"
                console.print(f"  [yellow]⚠ {provider.name}: {msg} — trying next[/yellow]")
                _log_session("chat_conn_error", provider.name, provider.model, False,
                             prompt_preview, error=str(e)[:200])
                last_error = e

            except ValueError as e:
                # Empty response
                console.print(f"  [yellow]⚠ {provider.name}: {e} — trying next[/yellow]")
                _log_session("chat_empty", provider.name, provider.model, False,
                             prompt_preview, error=str(e))
                last_error = e

            except Exception as e:
                console.print(f"  [yellow]⚠ {provider.name}: {type(e).__name__}: {e}[/yellow]")
                _log_session("chat_error", provider.name, provider.model, False,
                             prompt_preview, error=f"{type(e).__name__}: {e}")
                last_error = e

        raise RuntimeError(
            f"All LLM providers exhausted. Last error: {last_error}\n"
            "Check your API keys in .env"
        )

    def _call_with_gemini_fallback(self, client, provider: Provider, kwargs: dict):
        """Handle Gemini-specific model fallback and reasoning_effort stripping."""
        try:
            return client.chat.completions.create(**kwargs)
        except openai.RateLimitError as rle:
            if provider.name == "Gemini" and kwargs.get("model") != "gemini-2.5-flash":
                console.print(f"  [yellow]⚠ Gemini quota hit — falling back to gemini-2.5-flash[/yellow]")
                fb = dict(kwargs)
                fb["model"] = "gemini-2.5-flash"
                fb.pop("reasoning_effort", None)
                return client.chat.completions.create(**fb)
            raise rle
        except openai.BadRequestError as bre:
            if "reasoning_effort" in kwargs:
                fb = dict(kwargs)
                fb.pop("reasoning_effort", None)
                return client.chat.completions.create(**fb)
            raise bre

    # ── Utilities ─────────────────────────────────────────────────────────────

    def active_provider_names(self) -> list[str]:
        return [p.name for p in self.providers]

    def active_summary(self) -> str:
        if not self.providers:
            return "none"
        return " → ".join(f"{p.name}({p.model.split('/')[-1]})" for p in self.providers)

    def test_all(self) -> dict[str, bool]:
        """Quick smoke-test every configured provider."""
        results: dict[str, bool] = {}
        test_msg = [{"role": "user", "content": 'Reply with exactly: "OK"'}]
        for provider in self.providers:
            try:
                client = openai.OpenAI(
                    api_key=provider.api_key,
                    base_url=provider.base_url,
                    timeout=provider.timeout,
                )
                kwargs: dict = {
                    "model": provider.model,
                    "messages": test_msg,
                    "max_tokens": 200,
                    "temperature": 0.3,
                }
                if provider.extra_params:
                    kwargs.update(provider.extra_params)
                resp = self._call_with_gemini_fallback(client, provider, kwargs)
                results[provider.name] = bool((resp.choices[0].message.content or "").strip())
                _log_session("test_ok", provider.name, provider.model, results[provider.name])
            except Exception as e:
                results[provider.name] = False
                _log_session("test_fail", provider.name, provider.model, False,
                             error=f"{type(e).__name__}: {e}")
        return results


# ─── Singleton ────────────────────────────────────────────────────────────────
llm = LLMClient()
