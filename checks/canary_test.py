"""Canary-परीक्षा: तीन जानबूझकर ग़लत पेड़, जिन्हें जाँचें हर बार पकड़ें (मास्टर योजना §3.2)।

    python -m checks.canary_test

हर canary का अपना छोटा पेड़ canaries/<नाम>/ में है और canaries/expected.json बताता है कि
कौन-सी जाँच उसे पकड़े। एक भी canary छूटे तो exit code 2: पूरा स्वार्म रुकना चाहिए।
साथ में D-जाँचों की नियतात्मक आत्म-परीक्षा भी चलती है (निषेध, संख्या, नाम, वक्ता)।
"""
from __future__ import annotations

import json
import sys

from . import d_checks
from .common import REPO, load_json
from .run_all import run


def repo_canaries() -> tuple[int, int, list[str]]:
    exp = load_json(REPO / "canaries" / "expected.json")["canaries"]
    caught, lines = 0, []
    for c in exp:
        ctx = run(REPO / "canaries" / c["dir"])
        hits = [f for f in ctx.findings if f.level == "FAIL" and f.check == c["must_fail"]]
        ok = bool(hits)
        caught += ok
        lines.append(f"{'पकड़ा' if ok else 'छूटा!'}  {c['dir']}  (जाँच {c['must_fail']}; {len(hits)} FAIL)  — {c['what']}")
    return caught, len(exp), lines


# D-जाँचों के कृत्रिम canaries: (नाम, संस्कृत, भाषा, सही अनुवाद, बिगाड़ा अनुवाद, पकड़ने वाली जाँच)
D_SELF = [
    ("निषेध उलटा", "न जायते म्रियते वा कदाचित्", "en", "It is never born, nor does it ever die.", "It is born and it dies at some time.", "D2"),
    ("निषेध उलटा (हि)", "न जायते म्रियते वा कदाचित्", "hi", "यह न कभी जन्म लेता है, न मरता है।", "यह कभी जन्म लेता है और मरता है।", "D2"),
    ("संख्या बदली", "पञ्च एतानि महाबाहो कारणानि निबोध मे", "en", "Learn from me, O mighty-armed, these five causes.", "Learn from me, O mighty-armed, these causes.", "D3"),
    ("संख्या बदली (हि)", "पञ्च एतानि महाबाहो कारणानि निबोध मे", "hi", "हे महाबाहो, इन पाँच कारणों को मुझसे जानो।", "हे महाबाहो, इन कारणों को मुझसे जानो।", "D3"),
    ("विशेषण → ग़लत व्यक्ति", "तस्मादुत्तिष्ठ कौन्तेय युद्धाय कृतनिश्चयः", "en", "Therefore arise, O son of Kunti, resolved to fight.", "Therefore arise, O Sanjaya, resolved to fight.", "D6"),
    ("वक्ता बदला", "अर्जुन उवाच", "en", "Arjuna said:", "Sanjaya said:", "D7"),
    ("वक्ता बदला (हि)", "श्रीभगवानुवाच", "hi", "श्रीभगवान ने कहा:", "अर्जुन ने कहा:", "D7"),
    ("वर्जित शब्द", "पुराणं पञ्चलक्षणम्", "en", "A Purana has five marks.", "A Purana, a five-part myth.", "D8"),
    # सादी वर्तनी पर झूठी घंटी नहीं (गीता 1.28, 1.31, 1.41, 2.10, 2.54 का सबक़), पर ग़लत व्यक्ति अब भी पकड़ा जाए
    ("सादी वर्तनी: Krishna", "दृष्ट्वेमं स्वजनं कृष्ण युयुत्सुं समुपस्थितम्", "en", "O Krishna, seeing these kinsmen eager to fight.", "O Arjuna, seeing these kinsmen eager to fight.", "D6"),
    ("सादी वर्तनी: Keshava", "निमित्तानि च पश्यामि विपरीतानि केशव", "en", "And I see adverse omens, O Keshava.", "And I see adverse omens, O Partha.", "D6"),
    ("सादी वर्तनी: Hrishikesha", "तमुवाच हृषीकेशः प्रहसन्निव भारत", "en", "To him Hrishikesha, as if smiling, spoke, O Bharata.", "To him Arjuna, as if smiling, spoke, O Bharata.", "D6"),
    ("सादी वर्तनी: Varshneya", "स्त्रीषु दुष्टासु वार्ष्णेय जायते वर्णसङ्करः", "en", "When women are corrupted, O Varshneya, intermixture arises.", "When women are corrupted, O Dhananjaya, intermixture arises.", "D6"),
    # 'नो' = नः (हमें): निषेध नहीं (गीता 1.33)
    ("'नो' = हमें, निषेध उलटा अब भी पकड़ा", "येषामर्थे काङ्क्षितं नो राज्यं भोगाः सुखानि च । न जायते", "en", "For whose sake kingdom is desired by us; it is not born.", "For whose sake kingdom is desired by us; it is born.", "D2"),
]


def d_self_test() -> tuple[int, int, list[str]]:
    ok_n, lines = 0, []
    for name, sa, lang, good, bad, chk in D_SELF:
        good_flags = [f for f in d_checks.run_segment(sa, good, lang) if f.veto]
        bad_flags = [f for f in d_checks.run_segment(sa, bad, lang) if f.check == chk and f.veto]
        ok = (not good_flags) and bool(bad_flags)
        ok_n += ok
        why = "" if ok else f"  सही पर झूठी घंटी={[f.check for f in good_flags]} · बिगाड़े पर पकड़={bool(bad_flags)}"
        lines.append(f"{'ठीक' if ok else 'विफल!'}  {chk}  {name}{why}")
    return ok_n, len(D_SELF), lines


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    c, n, lines = repo_canaries()
    print(f"Repo-canaries: {c}/{n} पकड़े गए")
    print("\n".join("  " + x for x in lines))
    dc, dn, dlines = d_self_test()
    print(f"D-जाँचों की आत्म-परीक्षा: {dc}/{dn}")
    print("\n".join("  " + x for x in dlines))
    result = {"repo_canaries": {"caught": c, "total": n}, "d_self_test": {"ok": dc, "total": dn}}
    print(json.dumps(result, ensure_ascii=False))
    if c != n:
        print("CANARY छूटा: स्वार्म रुकना चाहिए (swarm/STOP)।")
        return 2
    return 0 if dc == dn else 1


if __name__ == "__main__":
    raise SystemExit(main())
