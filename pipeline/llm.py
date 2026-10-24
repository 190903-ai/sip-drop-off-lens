"""Thin Gemini wrapper: JSON-mode calls with retry on rate limits.

Usage as a check: python pipeline/llm.py   (tests which models the key can call)
"""
import json
import os
import threading
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

_client = None
_lock = threading.Lock()


def client() -> genai.Client:
    # Locked: threads racing here create extra clients that get GC'd and closed mid-request
    global _client
    with _lock:
        if _client is None:
            _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def generate_json(prompt: str, model: str, system: str | None = None, retries: int = 6):
    """Call Gemini in JSON mode and return the parsed object."""
    config = {"response_mime_type": "application/json", "temperature": 0}
    if system:
        config["system_instruction"] = system
    for attempt in range(retries):
        try:
            resp = client().models.generate_content(model=model, contents=prompt, config=config)
            if not resp.text:  # Gemma occasionally returns an empty candidate on long outputs
                raise json.JSONDecodeError("empty response", "", 0)
            return json.loads(resp.text.strip().removeprefix("```json").removesuffix("```"))
        except json.JSONDecodeError:
            if attempt == retries - 1:
                raise
        except Exception as e:
            msg = str(e)
            # rate limits, overload, transient server errors and dropped connections are retryable
            retryable = ("429", "RESOURCE_EXHAUSTED", "500", "INTERNAL", "503", "UNAVAILABLE",
                         "disconnected", "timed out", "Connection")
            if any(s in msg for s in retryable):
                time.sleep(min(60, 10 * (attempt + 1)))
                continue
            raise
    raise RuntimeError("Gemini call failed after retries")


if __name__ == "__main__":
    for m in ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-flash-lite"]:
        t = time.time()
        try:
            resp = client().models.generate_content(
                model=m, contents='Reply with this JSON exactly: {"ok": true}',
                config={"response_mime_type": "application/json"})
            print(f"{m}: OK {time.time() - t:.1f}s {resp.text.strip()[:40]}")
        except Exception as e:
            print(f"{m}: FAIL {str(e)[:160]}")
