"""मुफ़्त providers की जाँच (GitHub Actions में; keys केवल env से, कहीं छपती नहीं; खाते का ID रिपोर्ट में नहीं जाता)।

  1. Cloudflare Workers AI: पाठ-मॉडलों की सूची; कुछ परिवारों पर एक छोटा JSON-अनुरोध (मौजूदा token चलता है या नहीं)
  (17 नवंबर 2026 से workflow Cloudflare की key नहीं देता: वह खाता मालिक के दूसरे काम का है; यह हिस्सा तब चुपचाप छूट जाता है।)
  2. Groq: हर पाठ-मॉडल पर एक छोटा अनुरोध; rate-limit headers (असली मुफ़्त सीमाएँ)
रिपोर्ट में केवल नाम, गिनतियाँ, अवस्थाएँ, headers के मान और छँटे हुए त्रुटि-संदेश। मॉडल का लिखा पाठ नहीं जाता।
भेजा गया पाठ केवल सार्वजनिक है (मुण्डक 3.1.6 का अंश)।
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ACCT = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
CF_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "")
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
OR_KEY = os.environ.get("OPENROUTER_API_KEY", "")
# OpenRouter पर हर परीक्षण दिन के 50 मुफ़्त अनुरोधों में से एक लेता है, इसलिए गिने-चुने मॉडल ही
OR_PICKS = [r"nvidia/nemotron-3-ultra", r"nvidia/nemotron-3\.5-super", r"baidu/ernie", r"inclusionai/ling", r"thinkingmachines/inkling", r"google/gemma-4-31b"]
UA = "sanatan-granth-probe/0.1 (open library project)"
SYSTEM = 'Translate each Sanskrit segment into English. Output JSON only: {"items":[{"id":"<id>","en":"<English>"}]}. One item per given id.'
USER = "smoke:1: सत्यमेव जयते नानृतम्\nsmoke:2: सत्येन पन्था विततो देवयानः"
CF_FAMILIES = [("meta", r"llama-4|llama-3\.3-70b|llama.*70b|llama"), ("mistral", r"mistral-small|mistral"), ("openai", r"gpt-oss-120b|gpt-oss"),
               ("alibaba-qwen", r"qwen3|qwen"), ("google", r"gemma-4|gemma-3|gemma"), ("deepseek", r"deepseek"), ("moonshot", r"kimi")]


def scrub(s: object) -> str:
    s = str(s)
    for secret in (ACCT, CF_TOKEN, GROQ_KEY, OR_KEY):
        if secret:
            s = s.replace(secret, "<hidden>")
    s = re.sub(r"gsk_[0-9A-Za-z]{10,}", "<key>", s)
    s = re.sub(r"sk-or-[0-9A-Za-z_-]{10,}", "<key>", s)
    s = re.sub(r"user_[0-9A-Za-z]{10,}", "<user>", s)
    s = re.sub(r"\b[0-9a-f]{32}\b", "<id>", s)
    return s[:300]


def http(method: str, url: str, headers: dict, body: dict | None = None, timeout: int = 90) -> tuple[int, dict, dict, float]:
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"content-type": "application/json", "user-agent": UA, **headers})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}"), {k.lower(): v for k, v in r.headers.items()}, time.time() - t0
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read() or b"{}")
        except Exception:
            err = {}
        return e.code, err, {k.lower(): v for k, v in (e.headers or {}).items()}, time.time() - t0
    except Exception as e:  # noqa: BLE001
        return 0, {"error": type(e).__name__}, {}, time.time() - t0


def parse_ok(text: str) -> bool:
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        obj = json.loads(text[text.find("{"):text.rfind("}") + 1])
        return sorted(i.get("id") for i in obj.get("items", [])) == ["smoke:1", "smoke:2"]
    except Exception:
        return False


def chat(url: str, token: str, model: str, json_mode: bool, max_tokens: int = 400) -> dict:
    body = {"model": model, "temperature": 0, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": USER}]}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    st, js, hd, dt = http("POST", url, {"authorization": "Bearer " + token}, body)
    msg = ((js.get("choices") or [{}])[0].get("message") or {}) if st == 200 else {}
    out = {"model": model, "json_mode": json_mode, "http": st, "seconds": round(dt, 2), "ids_ok": parse_ok(msg.get("content") or "") if st == 200 else False,
           "usage": js.get("usage") if st == 200 else None,
           "ratelimit": {k: v for k, v in hd.items() if k.startswith("x-ratelimit") or k == "retry-after"}}
    if st != 200:
        out["error"] = scrub(json.dumps(js.get("errors") or js.get("error") or js, ensure_ascii=False))
    return out


def cloudflare() -> dict:
    rep: dict = {"token_present": bool(CF_TOKEN), "account_present": bool(ACCT)}
    if not (CF_TOKEN and ACCT):
        return rep
    base = f"https://api.cloudflare.com/client/v4/accounts/{ACCT}/ai"
    names: list[str] = []
    for page in range(1, 4):
        st, js, _, _ = http("GET", f"{base}/models/search?per_page=100&page={page}&task=" + urllib.parse.quote("Text Generation"), {"authorization": "Bearer " + CF_TOKEN})
        if st != 200:
            rep["models_http"] = st
            rep["models_error"] = scrub(json.dumps(js.get("errors") or js, ensure_ascii=False))
            break
        got = [m.get("name", "") for m in js.get("result", [])]
        names += got
        if len(got) < 100:
            break
    rep["text_models"] = sorted(set(names))
    tests = []
    for fam, rx in CF_FAMILIES:
        pick = None
        for alt in rx.split("|"):
            pick = next((n for n in sorted(names, reverse=True) if re.search(alt, n, re.I) and not re.search(r"guard|lora|vision|coder|embedding", n, re.I)), None)
            if pick:
                break
        if not pick:
            continue
        r = chat(f"{base}/v1/chat/completions", CF_TOKEN, pick, True)
        if r["http"] == 400:
            r2 = chat(f"{base}/v1/chat/completions", CF_TOKEN, pick, False)
            r2["json_mode_400"] = r.get("error")
            r = r2
        r["family"] = fam
        tests.append(r)
    rep["tests"] = tests
    return rep


def groq() -> dict:
    rep: dict = {"key_present": bool(GROQ_KEY)}
    if not GROQ_KEY:
        return rep
    st, js, _, _ = http("GET", "https://api.groq.com/openai/v1/models", {"authorization": "Bearer " + GROQ_KEY})
    ids = sorted(m["id"] for m in js.get("data", [])) if st == 200 else []
    rep["models"] = ids
    rep["tests"] = [chat("https://api.groq.com/openai/v1/chat/completions", GROQ_KEY, i, True)
                    for i in ids if not re.search(r"whisper|tts|guard|orpheus|allam", i, re.I)]
    return rep


def openrouter() -> dict:
    """मुफ़्त मॉडलों की सूची (सार्वजनिक), key की दिन-भर की गिनती, और कुछ परिवारों पर एक छोटा JSON-अनुरोध।"""
    rep: dict = {"key_present": bool(OR_KEY)}
    st, js, _, _ = http("GET", "https://openrouter.ai/api/v1/models", {})
    free = sorted(m["id"] for m in (js.get("data", []) if st == 200 else [])
                  if m.get("id", "").endswith(":free") and str((m.get("pricing") or {}).get("prompt")) == "0" and str((m.get("pricing") or {}).get("completion")) == "0")
    rep["free_models"] = free
    if not OR_KEY:
        return rep
    auth = {"authorization": "Bearer " + OR_KEY}

    def quota() -> dict:
        st2, j2, _, _ = http("GET", "https://openrouter.ai/api/v1/key", auth)
        d = j2.get("data", {}) if st2 == 200 else {}
        return {"http": st2, "is_free_tier": d.get("is_free_tier"), "free_model_daily_requests": d.get("free_model_daily_requests")}

    rep["key_before"] = quota()
    tests = []
    for rx in OR_PICKS:
        pick = next((i for i in free if re.search(rx, i)), None)
        if not pick:
            continue
        r = chat("https://openrouter.ai/api/v1/chat/completions", OR_KEY, pick, True, 1500)
        if r["http"] in (400, 404):
            r2 = chat("https://openrouter.ai/api/v1/chat/completions", OR_KEY, pick, False, 1500)
            r2["json_mode_error"] = r.get("error")
            r = r2
        tests.append(r)
        time.sleep(3.5)
    rep["tests"] = tests
    rep["key_after"] = quota()
    return rep


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    rep = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "cloudflare_workers_ai": cloudflare(), "groq": groq(), "openrouter": openrouter()}
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
