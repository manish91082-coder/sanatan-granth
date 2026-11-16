"""Pilot के लिए मुफ़्त मॉडल-providers (Google AI Studio, Groq, Cloudflare Workers AI)। keys केवल env से; कहीं छपती नहीं।

हर मॉडल का "परिवार" कंपनी से गिना जाता है (मास्टर योजना §3.3): Gemini और Gemma दोनों google; gpt-oss openai।
429 पर इंतज़ार और सीमित दोहराव; कभी दूसरी key या दूसरा खाता नहीं।
Groq के rate-limit headers पढ़कर अगला अनुरोध पहले ही रोका जाता है (pacing), ताकि 429 तक बात न पहुँचे।
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
CF_BASE = "https://api.cloudflare.com/client/v4/accounts/{acct}/ai/v1"
UA = "sanatan-granth-pilot/0.3 (open library project)"
MAX_RETRY = 5
TIMEOUT_S = {"google_ai_studio": 300, "groq": 120, "cloudflare": 150}  # एक अनुरोध की सीमा; अटका मॉडल पूरे run को न रोके
MAX_RETRY_5XX = 3  #5xx या नेटवर्क-त्रुटि पर कम दोहराव: provider बंद हो तो मिनटों इंतज़ार बेकार है
PACE_MAX_WAIT_S = 62.0


@dataclass
class Usage:
    calls: int = 0
    retries: int = 0
    http_429: int = 0
    prompt_tokens: int = 0
    output_tokens: int = 0
    seconds: float = 0.0
    waited_s: float = 0.0
    paced_s: float = 0.0
    neurons: float = 0.0
    errors: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"calls": self.calls, "retries": self.retries, "http_429": self.http_429, "prompt_tokens": self.prompt_tokens,
                "output_tokens": self.output_tokens, "seconds": round(self.seconds, 2), "waited_s": round(self.waited_s, 1),
                "paced_s": round(self.paced_s, 1), "neurons": round(self.neurons, 1), "errors": self.errors[:5]}


@dataclass(frozen=True)
class Model:
    provider: str  # google_ai_studio | groq | cloudflare | mock
    name: str
    family: str

    @property
    def ref(self) -> str:
        return f"{self.provider}:{self.name}"


def family_of(name: str) -> str:
    n = name.lower()
    if "openai/" in n or "gpt-oss" in n:
        return "openai"
    if "qwen" in n or "qwq" in n:
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
    if "nemotron" in n or "nvidia" in n:
        return "nvidia"
    if "glm" in n or "zai-org" in n:
        return "zhipu"
    return "other-" + re.sub(r"[^a-z0-9]+", "-", n.replace("@cf/", "").split("/")[0])[:20]


def parse_model(ref: str) -> Model:
    """'groq:qwen/qwen3.8-27b' → Model। provider के बिना नाम अमान्य है।"""
    provider, _, name = ref.strip().partition(":")
    if provider not in ("google_ai_studio", "groq", "cloudflare") or not name:
        raise ValueError(f"मॉडल-संदर्भ अमान्य: {ref!r}")
    return Model(provider, name, family_of(name))


def scrub(s: object) -> str:
    s = str(s)
    for env in ("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN", "GROQ_API_KEY", "GEMINI_API_KEY"):
        v = os.environ.get(env)
        if v:
            s = s.replace(v, "<hidden>")
    s = re.sub(r"AIza[0-9A-Za-z_-]{10,}", "<key>", s)
    s = re.sub(r"gsk_[0-9A-Za-z]{10,}", "<key>", s)
    return s[:300]


def _http(method: str, url: str, headers: dict, body: dict | None, timeout: int = 240) -> tuple[int, dict, dict]:
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"content-type": "application/json", "user-agent": UA, **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}"), {k.lower(): v for k, v in r.headers.items()}
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read() or b"{}")
        except Exception:
            err = {}
        return e.code, err, {k.lower(): v for k, v in (e.headers or {}).items()}
    except Exception as e:  # noqa: BLE001
        return 0, {"error": {"message": type(e).__name__}}, {}


def _duration_s(text: str | None) -> float | None:
    """'2m59.56s', '7.66s', '120ms' → सेकंड।"""
    if not text:
        return None
    total, found = 0.0, False
    for num, unit in re.findall(r"([0-9.]+)\s*(ms|h|m|s)", text):
        total += float(num) * {"ms": 0.001, "s": 1, "m": 60, "h": 3600}[unit]
        found = True
    if not found:
        try:
            return float(text)
        except ValueError:
            return None
    return total


def _wait_hint(js: dict, headers: dict, attempt: int) -> float:
    v = _duration_s(headers.get("retry-after"))
    if v is not None:
        return min(v + 1, 90)
    m = re.search(r"(?:try again in|retry in)\s*([0-9.]+\s*(?:ms|s|m)?(?:[0-9.]+s)?)", json.dumps(js), re.I)
    if m:
        v = _duration_s(m.group(1)) or float(re.match(r"[0-9.]+", m.group(1)).group(0))
        return min(v + 1, 90)
    return min(10 * (attempt + 1), 60)


# ---- pacing: provider के बताए बचे tokens से अगला अनुरोध पहले ही रोकना (केवल Groq headers देता है)
_PACE: dict[str, dict] = {}


def estimate_tokens(system: str, user: str, est_out: int) -> int:
    return int((len(system) + len(user)) * 0.6) + est_out


def _pace_before(model: Model, est: int, usage: Usage) -> None:
    st = _PACE.get(model.ref)
    if not st:
        return
    elapsed = time.time() - st["at"]
    rate = st["limit"] / 60.0
    remaining = min(st["limit"], st["remaining"] + elapsed * rate)
    need = min(est, st["limit"]) - remaining
    if need > 0:
        w = min(need / rate + 0.5, PACE_MAX_WAIT_S)
        usage.paced_s += w
        time.sleep(w)


def _pace_after(model: Model, headers: dict) -> None:
    try:
        limit = float(headers["x-ratelimit-limit-tokens"])
        remaining = float(headers["x-ratelimit-remaining-tokens"])
    except (KeyError, ValueError):
        return
    if limit > 0:
        _PACE[model.ref] = {"limit": limit, "remaining": remaining, "at": time.time()}


def extract_json(text: object) -> object:
    if isinstance(text, (dict, list)):
        return text
    text = re.sub(r"<think>.*?</think>", "", str(text), flags=re.S).strip()
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


def available(model: Model) -> bool:
    """इस provider की key env में है या नहीं (key का मान कभी नहीं देखा जाता)।"""
    need = {"google_ai_studio": ["GEMINI_API_KEY"], "groq": ["GROQ_API_KEY"], "cloudflare": ["CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID"], "mock": []}
    return all(os.environ.get(k) for k in need.get(model.provider, ["__none__"]))


def _openai_style(model: Model, system: str, user: str, max_out: int) -> tuple[int, dict, dict, object, int, int, float]:
    if model.provider == "groq":
        url, token = f"{GROQ_BASE}/chat/completions", os.environ.get("GROQ_API_KEY", "")
        body: dict = {"model": model.name, "temperature": 0, "response_format": {"type": "json_object"}}
    else:
        url, token = CF_BASE.format(acct=os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")) + "/chat/completions", os.environ.get("CLOUDFLARE_API_TOKEN", "")
        body = {"model": model.name, "temperature": 0, "max_tokens": max_out, "response_format": {"type": "json_object"}}
    body["messages"] = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    st, js, hd = _http("POST", url, {"authorization": "Bearer " + token}, body, TIMEOUT_S[model.provider])
    if st == 400 and re.search(r"response_format|json_validate_failed|Failed to (generate|validate) JSON|json", json.dumps(js), re.I):
        body.pop("response_format")  # JSON-mode विफल: सादा उत्तर माँगें, JSON हम ख़ुद निकालेंगे
        st, js, hd = _http("POST", url, {"authorization": "Bearer " + token}, body, TIMEOUT_S[model.provider])
    content: object = ""
    if st == 200:
        msg = (js.get("choices") or [{}])[0].get("message") or {}
        content = msg.get("content") or ""
    um = js.get("usage", {}) if st == 200 else {}
    return st, js, hd, content, um.get("prompt_tokens", 0), um.get("completion_tokens", 0), float(um.get("neurons") or 0.0)


def chat_json(model: Model, system: str, user: str, usage: Usage, est_out: int = 1800) -> object:
    """एक JSON-उत्तर। विफल होने पर RuntimeError (संदेश में key नहीं)।"""
    last = "no attempt"
    hard_fails = 0
    for attempt in range(MAX_RETRY):
        _pace_before(model, estimate_tokens(system, user, est_out), usage)
        t0 = time.time()
        neurons = 0.0
        if model.provider == "google_ai_studio":
            plain = {"contents": [{"role": "user", "parts": [{"text": system + "\n\n" + user}]}], "generationConfig": {"temperature": 0}}
            url, key = f"{GEMINI_BASE}/models/{model.name}:generateContent", {"x-goog-api-key": os.environ.get("GEMINI_API_KEY", "")}
            if "gemma" in model.name.lower():
                # Gemma systemInstruction और JSON-mode नहीं लेता: निर्देश संदेश में जोड़कर सादा अनुरोध
                st, js, hd = _http("POST", url, key, plain, TIMEOUT_S[model.provider])
            else:
                st, js, hd = _http("POST", url, key, {"systemInstruction": {"parts": [{"text": system}]},
                                                     "contents": [{"role": "user", "parts": [{"text": user}]}],
                                                     "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}, TIMEOUT_S[model.provider])
                if st == 400 and re.search(r"system|developer instruction|json mode|mime", json.dumps(js), re.I):
                    st, js, hd = _http("POST", url, key, plain, TIMEOUT_S[model.provider])
            text: object = "".join(p.get("text", "") for p in (js.get("candidates") or [{}])[0].get("content", {}).get("parts", []) if not p.get("thought")) if st == 200 else ""
            um = js.get("usageMetadata", {}) if st == 200 else {}
            ptok, otok = um.get("promptTokenCount", 0), um.get("candidatesTokenCount", 0) + um.get("thoughtsTokenCount", 0)
        elif model.provider in ("groq", "cloudflare"):
            st, js, hd, text, ptok, otok, neurons = _openai_style(model, system, user, max(est_out * 2, 3000))
            _pace_after(model, hd)
        else:
            raise RuntimeError(f"अनजान provider {model.provider}")
        usage.calls += 1
        usage.seconds += time.time() - t0
        if st == 200:
            usage.prompt_tokens += ptok
            usage.output_tokens += otok
            usage.neurons += neurons
            try:
                return extract_json(text)
            except Exception:
                last = "JSON parse नहीं हुआ"
                usage.retries += 1
                continue
        err = js.get("error") or js.get("errors") or ""
        if isinstance(err, list):
            err = (err[0] if err else {})
        last = f"HTTP {st}: {scrub(err.get('message', '') if isinstance(err, dict) else err)}"
        if st == 429:
            usage.http_429 += 1
        if st in (429, 500, 502, 503, 504, 0):
            if st != 429:
                hard_fails += 1
                if hard_fails >= MAX_RETRY_5XX:
                    break
            w = _wait_hint(js, hd, attempt)
            usage.retries += 1
            usage.waited_s += w
            time.sleep(w)
            continue
        break
    usage.errors.append(last)
    raise RuntimeError(f"{model.ref}: {last}")
