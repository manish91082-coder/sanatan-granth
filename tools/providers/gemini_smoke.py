"""क़दम 0.3: Gemini की मुफ़्त key की जाँच (GitHub Actions में; key केवल env से, कहीं छपती नहीं)।

कुल 3–4 अनुरोध ख़र्च होते हैं:
  1. models की सूची (कौन-से नाम generateContent देते हैं)
  2. एक छोटा strict-JSON अनुरोध (ID-enum के साथ) → latency, token-गिनती, ID लौटे या नहीं
  3. मुफ़्त Batch API का एक छोटा job → स्वीकार हुआ या नहीं, और अवस्था
नतीजा JSON में: केवल गिनतियाँ, अवस्थाएँ और त्रुटि-संदेश। मॉडल का लिखा पाठ रिपोर्ट में नहीं जाता।
भेजा गया पाठ केवल सार्वजनिक है (मुण्डक 3.1.6 का एक अंश), जैसा फ़ैसला #5 कहता है।
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://generativelanguage.googleapis.com/v1beta"
KEY = os.environ.get("GEMINI_API_KEY", "")
PREFER = [r"3\.5.*flash.*lite", r"3\.1.*flash.*lite", r"flash.*lite"]
SA = {"smoke:1": "सत्यमेव जयते नानृतम्", "smoke:2": "सत्येन पन्था विततो देवयानः"}


def call(method: str, path: str, body: dict | None = None, timeout: int = 120) -> tuple[int, dict, float]:
    req = urllib.request.Request(f"{BASE}/{path}", method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"x-goog-api-key": KEY, "content-type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}"), time.time() - t0
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read() or b"{}")
        except Exception:
            err = {}
        return e.code, err, time.time() - t0


def scrub(s: str) -> str:
    return re.sub(r"AIza[0-9A-Za-z_-]{10,}", "<key>", str(s))[:400]


def request_body() -> dict:
    prompt = ("Translate each Sanskrit segment into English and Hindi. Return one item per id; use only the given ids.\n"
              + "\n".join(f"{k}: {v}" for k, v in SA.items()))
    return {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json",
                                 "responseSchema": {"type": "ARRAY", "items": {"type": "OBJECT", "required": ["id", "en", "hi"], "properties": {
                                     "id": {"type": "STRING", "enum": list(SA)}, "en": {"type": "STRING"}, "hi": {"type": "STRING"}}}}}}


def main() -> int:
    rep: dict = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "provider": "google_ai_studio", "requests_spent": 0}
    if not KEY:
        rep["error"] = "GEMINI_API_KEY secret नहीं मिला"
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 1

    st, js, dt = call("GET", "models?pageSize=200")
    rep["requests_spent"] += 1
    models = [m for m in js.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
    rep["list_models"] = {"http": st, "count": len(models), "error": scrub(js.get("error", {}).get("message", "")) if st != 200 else None,
                          "flash_lite": sorted(m["name"] for m in models if re.search(r"flash.*lite", m["name"])),
                          "gemma": sorted(m["name"] for m in models if "gemma" in m["name"]),
                          "batch_capable": sorted(m["name"] for m in js.get("models", []) if "batchGenerateContent" in m.get("supportedGenerationMethods", []))[:40]}
    if st != 200 or not models:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 1
    model = os.environ.get("GEMINI_MODEL") or next((m["name"] for rx in PREFER for m in sorted(models, key=lambda x: x["name"], reverse=True)
                                                    if re.search(rx, m["name"]) and not re.search(r"tts|image|live|audio", m["name"])), models[0]["name"])
    rep["model"] = model

    st, js, dt = call("POST", f"{model}:generateContent", request_body())
    rep["requests_spent"] += 1
    g: dict = {"http": st, "latency_s": round(dt, 2)}
    if st == 200:
        text = "".join(p.get("text", "") for p in js.get("candidates", [{}])[0].get("content", {}).get("parts", []))
        try:
            items = json.loads(text)
            ids = [i.get("id") for i in items]
            g.update(json_parsed=True, ids_exact=sorted(ids) == sorted(SA), items=len(items),
                     all_fields_nonempty=all(i.get("en") and i.get("hi") for i in items))
        except Exception:
            g.update(json_parsed=False)
        g["usage"] = {k: v for k, v in js.get("usageMetadata", {}).items() if isinstance(v, int)}
        g["model_version"] = js.get("modelVersion")
    else:
        g["error"] = scrub(js.get("error", {}).get("message", ""))
    rep["generate"] = g

    b: dict = {}
    body = {"batch": {"display_name": "sanatan-granth-smoke", "input_config": {"requests": {"requests": [
        {"request": {k: v for k, v in request_body().items()}, "metadata": {"key": "smoke-1"}}]}}}}
    st, js, dt = call("POST", f"{model}:batchGenerateContent", body)
    rep["requests_spent"] += 1
    b.update(http=st, accepted=st == 200)
    if st == 200:
        name = js.get("name", "")
        b["operation"] = re.sub(r"[^A-Za-z0-9/_-]", "", name)[:80]
        state, waited = None, 0
        while waited < 600 and name:
            time.sleep(30)
            waited += 30
            st2, js2, _ = call("GET", name)
            state = (js2.get("metadata", {}) or {}).get("state") or ("DONE" if js2.get("done") else None)
            if js2.get("done") or (state and state.endswith(("SUCCEEDED", "FAILED", "CANCELLED", "EXPIRED"))):
                b["final_http"] = st2
                b["result_error"] = scrub(js2.get("error", {}).get("message", "")) if js2.get("error") else None
                break
        b.update(state=state, waited_s=waited)
    else:
        b["error"] = scrub(js.get("error", {}).get("message", ""))
    rep["batch"] = b

    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0 if rep["generate"].get("http") == 200 else 1


if __name__ == "__main__":
    sys.exit(main())
