"""साझा औज़ार: फ़ाइल-खोज, schema, hash, Finding।

दो जड़ें होती हैं:
  data_root   = जिस पेड़ की जाँच हो रही है (पूरा repo, या canaries/<नाम>/ का छोटा पेड़)
  policy_root = असली repo, जहाँ से schema/ और policy/ पढ़े जाते हैं
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field, asdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator

REPO = Path(__file__).resolve().parent.parent

# जाँच से बाहर के रास्ते (data_root के सापेक्ष, पहला हिस्सा)
SKIP_TOP = {".git", "node_modules", "canaries", ".cache", "_cache", "_raw", "exports", ".wrangler", "__pycache__"}

SEGMENT_ID_RE = re.compile(r"^[a-z][a-z0-9_]*:[0-9]+(\.[0-9]+)*[a-d]?$")


@dataclass
class Finding:
    check: str
    level: str  # FAIL | WARN | INFO
    path: str
    msg: str
    segment: str | None = None

    def as_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class Ctx:
    data_root: Path
    policy_root: Path = REPO
    findings: list[Finding] = field(default_factory=list)
    kpi: dict = field(default_factory=dict)

    def rel(self, p: Path) -> str:
        try:
            return p.resolve().relative_to(self.data_root.resolve()).as_posix()
        except ValueError:
            return p.as_posix()

    def add(self, check: str, level: str, path: Path | str, msg: str, segment: str | None = None) -> None:
        self.findings.append(Finding(check, level, self.rel(path) if isinstance(path, Path) else path, msg, segment))

    # ---- policy ----
    def policy(self, name: str) -> Any:
        return load_json(self.policy_root / "policy" / name)

    # ---- फ़ाइल-खोज ----
    def walk(self, *suffixes: str) -> Iterator[Path]:
        root = self.data_root
        for p in sorted(root.rglob("*")):
            if not p.is_file():
                continue
            parts = p.relative_to(root).parts
            if parts and parts[0] in SKIP_TOP:
                continue
            if any(part in ("node_modules", "__pycache__", ".wrangler") for part in parts):
                continue
            if suffixes and p.suffix not in suffixes:
                continue
            yield p

    def layer_files(self) -> Iterator[tuple[Path, dict]]:
        """texts/ के नीचे की हर परत-फ़ाइल (जिसमें _meta और segments हों)।"""
        base = self.data_root / "texts"
        if not base.exists():
            return
        for p in sorted(base.rglob("*.json")):
            if p.name in ("_text.json", "text_lock.json", "concordance.json"):
                continue
            try:
                obj = load_json(p)
            except Exception:
                continue  # R1 इसे पकड़ती है
            if isinstance(obj, dict) and "_meta" in obj and "segments" in obj:
                yield p, obj

    def text_dirs(self) -> Iterator[Path]:
        base = self.data_root / "texts"
        if base.exists():
            for d in sorted(base.iterdir()):
                if d.is_dir():
                    yield d


def load_json(p: Path) -> Any:
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(p: Path) -> list[tuple[int, Any]]:
    out = []
    with open(p, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if line:
                out.append((i, json.loads(line)))
    return out


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def canonical_segments_hash(segments: dict[str, str]) -> str:
    """text-lock का hash: segments का canonical JSON (कुंजी-क्रम स्थिर, NFC, कच्चा UTF-8)।"""
    canon = json.dumps({k: nfc(v) for k, v in sorted(segments.items())}, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def job_key(corpus: str, batch_id: str, step: str, prompt_hash: str, model: str) -> str:
    """idempotency-कुंजी (मास्टर योजना §5.4 रेलिंग 5)।"""
    return hashlib.sha256("\x1f".join([corpus, batch_id, step, prompt_hash, model]).encode("utf-8")).hexdigest()


def segment_sort_key(seg_id: str) -> tuple:
    text, _, num = seg_id.partition(":")
    m = re.match(r"^([0-9.]+)([a-d]?)$", num)
    nums = tuple(int(x) for x in m.group(1).split(".")) if m else ()
    return (text, nums, m.group(2) if m else "")


@lru_cache(maxsize=None)
def _schema_store(policy_root: str) -> dict:
    store = {}
    for p in (Path(policy_root) / "schema").glob("*.schema.json"):
        s = load_json(p)
        store[s["$id"]] = s
        store[p.name] = s
    return store


def validator(policy_root: Path, schema_file: str, pointer: str | None = None):
    """jsonschema validator, स्थानीय $ref के साथ (नेटवर्क कभी नहीं)।"""
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource

    store = _schema_store(str(policy_root))
    resources = [(s["$id"], Resource.from_contents(s)) for k, s in store.items() if k.startswith("http")]
    registry = Registry().with_resources(resources)
    base = store[schema_file]
    schema = base if pointer is None else {"$ref": f"{base['$id']}#{pointer}"}
    return Draft202012Validator(schema, registry=registry, format_checker=Draft202012Validator.FORMAT_CHECKER)


def iter_strings(obj: Any, path: str = "") -> Iterator[tuple[str, str]]:
    """JSON के हर string-मान पर (json-path, मान)।"""
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from iter_strings(v, f"{path}/{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_strings(v, f"{path}/{i}")
