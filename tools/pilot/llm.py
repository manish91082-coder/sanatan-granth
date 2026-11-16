"""Pilot के लिए मुफ़्त मॉडल-providers (Google AI Studio, Groq)। keys केवल env से; कहीं छपती नहीं।

हर मॉडल का "परिवार" कंपनी से गिना जाता है (मास्टर योजना §3.3): Gemini और Gemma दोनों google; gpt-oss openai।
429 पर इंतज़ार और सीमित दोहराव; कभी दूसरी key या दूसरा खाता नहीं।
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
GROQ_BASE = "https://api.groq.com/openai/v1"
UA = "sanatan-granth-pilot/0.1 (open library project)"
MAX_RETRY = 5


@dataclass
class Usage:
    calls: int = 0
    retries: int = 0
    http_429: int = 0
    prompt_tokens: int = 0
    output_tokens: int = 0
    seconds: float = 0.0
    waited_s: float = 0.0
    errors: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"calls": self.calls, "retries": self.retries, "http_429": self.http_429, "prompt_tokens": self.prompt_tokens,
                "output_tokens": self.output_tokens, "seconds": round(self.seconds, 2), "waited_s": round(self.waited_s, 1),
                "errors": self.errors[:5]}


@dataclass(frozen=True)
class Model:
    provider: str  # google_ai_studio | groq | mock
    name: str
    family: str


def family_of(name: str) -> str:
    n = name.lower()
    if n.startswith("openai/") or "gpt-oss" in n:
        return "openai"
    if "qwen" in n:
        return "alibaba-qwen"
    if "llama" in n:
        return "meta"
    if "gemini" in n or "gemma" in n:
        return "google"
    if "kimi" in n or "moonshot" in n:
        return "moonshot"
    if "mistral" in n or "mixtral" in n:
        return "mistral"
    if "deepseek" in n:
        return "deepseek"
    return "other-" + re.sub(r"[^a-z0-9]+", "-", n.split("/")[0])[:20]


def scrub(s: object) -> str:
    s = re.sub(r"AIza[0-9A-Za-z_-]{10,}", "<key>", str(s))
    s = re.sub(r"gsk_[0-9A-Za-z]{10,}", "<key>", s)
    return s[:300]


def _http(method: str, url: str, headers: dict, body: dict | None, timeout: int = 180) -> tuple[int, dict, dict]:
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"content-type": "application/json", "user-agent": UA, **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}"), dict(r.headers)
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read() or b"{}")
        except Exception:
            err = {}
        return e.code, err, dict(e.headers or {})
    except Exception as e:  # noqa: BLE001
        return 0, {"error": {"message": type(e).__name__}}, {}


def _wait_hint(status: int, js: dict, headers: dict, attempt: int) -> float:
    for k in ("retry-after", "Retry-After"):
        if k in headers:
            try:
                return min(float(headers[k]) + 1, 90)
            except ValueError:
                pass
    m = re.search(r"(?:try again in|retry in)\s*([0-9.]+)\s*(ms|s|m)?", json.dumps(js), re.I)
    if m:
        v = float(m.group(1)) * {"ms": 0.001, "m": 60}.get((m.group(2) or "s").lower(), 1)
        return min(v + 1, 90)
    return min(10 * (attempt + 1), 60)


def extract_json(text: str) -> object:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(text)
    except Exception:
        i, j = text.find("{"), text.rfind("}")
        if i >= 0 and j > i:
            return json.loads(text[i:j + 1])
        raise


def list_groq_models() -> list[str]:
    st, js, _ = _http("GET", f"{GROQ_BASE}/models", {"authorization": "Bearer " + os.environ.get("GROQ_API_KEY", "")}, None, 60)
    return sorted(m["id"] for m in js.get("data", [])) if st == 200 else []


def chat_json(model: Model, system: str, user: str, usage: Usage) -> object:
    """एक JSON-उत्तर। विफल होने पर RuntimeError (संदेश में key नहीं)।"""
    last = "no attempt"
    for attempt in range(MAX_RETRY):
        t0 = time.time()
        if model.provider == "google_ai_studio":
            st, js, hd = _http("POST", f"{GEMINI_BASE}/models/{model.name}:generateContent",
                               {"x-goog-api-key": os.environ.get("GEMINI_API_KEY", "")},
                               {"systemInstruction": {"parts": [{"text": system}]},
                                "contents": [{"role": "user", "parts": [{"text": user}]}],
                                "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}})
            text = "".join(p.get("text", "") for p in (js.get("candidates") or [{}])[0].get("content", {}).get("parts", [])) if st == 200 else ""
            um = js.get("usageMetadata", {}) if st == 200 else {}
            ptok, otok = um.get("promptTokenCount", 0), um.get("candidatesTokenCount", 0) + um.get("thoughtsTokenCount", 0)
        elif model.provider == "groq":
            body = {"model": model.name, "temperature": 0, "response_format": {"type": "json_object"},
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
            st, js, hd = _http("POST", f"{GROQ_BASE}/chat/completions", {"authorization": "Bearer " + os.environ.get("GROQ_API_KEY", "")}, body)
            if st == 400 and "response_format" in json.dumps(js):
                body.pop("response_format")
                st, js, hd = _http("POST", f"{GROQ_BASE}/chat/completions", {"authorization": "Bearer " + os.environ.get("GROQ_API_KEY", "")}, body)
            text = ((js.get("choices") or [{}])[0].get("message", {}).get("content") or "") if st == 200 else ""
            um = js.get("usage", {}) if st == 200 else {}
            ptok, otok = um.get("prompt_tokens", 0), um.get("completion_tokens", 0)
        else:
            raise RuntimeError(f"अनजान provider {model.provider}")
        usage.calls += 1
        usage.seconds += time.time() - t0
        if st == 200:
            usage.prompt_tokens += ptok
            usage.output_tokens += otok
            try:
                return extract_json(text)
            except Exception:
                last = "JSON parse नहीं हुआ"
                usage.retries += 1
                continue
        last = f"HTTP {st}: {scrub((js.get('error') or {}).get('message', ''))}"
        if st == 429:
            usage.http_429 += 1
        if st in (429, 500, 502, 503, 504, 0):
            w = _wait_hint(st, js, hd, attempt)
            usage.retries += 1
            usage.waited_s += w
            time.sleep(w)
            continue
        break
    usage.errors.append(last)
    raise RuntimeError(f"{model.provider}/{model.name}: {last}")
