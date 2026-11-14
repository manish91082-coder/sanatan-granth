"""पूरे repo पर R1–R14 (+A3/D11) चलाएँ।

    python -m checks.run_all                 # इंसान के पढ़ने लायक़
    python -m checks.run_all --json          # मशीन के लिए
    python -m checks.run_all --out audit/daily/2026-11-15.json
    python -m checks.run_all --root canaries/c1_fake_verified   # किसी छोटे पेड़ पर

exit code: 0 = कोई FAIL नहीं; 1 = कम-से-कम एक FAIL।
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from .common import REPO, Ctx
from .r_checks import ALL


def run(data_root: Path, policy_root: Path = REPO) -> Ctx:
    ctx = Ctx(data_root=data_root, policy_root=policy_root)
    for name, fn in ALL:
        try:
            fn(ctx)
        except Exception as e:  # noqa: BLE001  जाँच का ख़ुद टूटना भी FAIL है
            ctx.add(name, "FAIL", ".", f"जाँच ख़ुद टूट गई: {type(e).__name__}: {e}")
    return ctx


def report(ctx: Ctx) -> dict:
    by_check: dict[str, dict] = {}
    for name, _ in ALL:
        by_check[name] = {"fail": 0, "warn": 0}
    for f in ctx.findings:
        d = by_check.setdefault(f.check, {"fail": 0, "warn": 0})
        d["fail" if f.level == "FAIL" else "warn"] += 1
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_root": ctx.data_root.as_posix() if ctx.data_root != REPO else ".",
        "summary": {"fail": sum(1 for f in ctx.findings if f.level == "FAIL"),
                    "warn": sum(1 for f in ctx.findings if f.level == "WARN")},
        "by_check": by_check,
        "kpi": ctx.kpi,
        "findings": [f.as_dict() for f in ctx.findings],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    root = (Path(a.root).resolve() if a.root else REPO)
    rep = report(run(root))
    if a.out:
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        for name, c in rep["by_check"].items():
            mark = "FAIL" if c["fail"] else ("warn" if c["warn"] else "ok")
            print(f"{name:7} {mark:5} fail={c['fail']} warn={c['warn']}")
        for f in rep["findings"]:
            print(f"  [{f['level']}] {f['check']} {f['path']}{' ' + f['segment'] if f.get('segment') else ''}: {f['msg']}")
        print(f"कुल: FAIL={rep['summary']['fail']} WARN={rep['summary']['warn']}")
    return 1 if rep["summary"]["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
