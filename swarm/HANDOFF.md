# HANDOFF: हर session अपना खंड लिखे

> नियम: turn/session ख़त्म होने से पहले, अगर काम बीच में है, तो अपना खंड यहाँ लिखें और commit करें। हर session केवल अपना खंड बदले।

## निर्माण-session 1 (2026-11-14; शुरुआत claude-opus-5-5, फिर claude-fable-5-2)

**क्या हुआ**

- repo `E:\sanatan-granth` बना और GitHub पर public repo के रूप में push हुआ (मालिक की हाँ: `DECISIONS.md`)।
- ढाँचा: `CLAUDE.md`, `swarm/*`, `policy/*`, `schema/*`, `catalog/_taxonomy.json`, `canaries/` (3), `checks/` (R1–R14, A3/D11, D2/D3/D6/D7/D8 v0), workflows (`ci`, `daily-audit`, `foreman-job`, `foreman-deploy`), `foreman/` (Agents SDK 0.33.0 pinned, D1 migration, 12 unit tests), `drive/` (rclone `granth:` scripts)।
- स्थानीय नतीजे: `checks.run_all` FAIL=0; `checks.canary_test` canaries 3/3, D-आत्म-परीक्षा 8/8; Foreman `tsc` साफ़, 12/12 tests, `wrangler deploy --dry-run` बना (gzip ~425 KiB)।

- GitHub पर जाँचा गया (14 नवंबर): पहला CI पूरा हरा (checks, canaries, protected-paths, foreman)। `main` पर protection लगा: PR अनिवार्य, 3 required checks, `enforce_admins`, force-push बंद। परीक्षण-PR #1 (नक़ली बैज A) पर `checks` लाल हुआ, merge BLOCKED रहा, और `main` पर सीधा push अस्वीकार हुआ। PR #1 बिना merge के बंद है।
- repo-सेटिंग: auto-merge की अनुमति चालू, केवल squash-merge, merge पर branch हटे; labels बने (`owner-approved`, `needs-human`, `red-audit`, `audit`, `budget`, `licence`, `contradicted`, `data`); Actions को PR खोलने की अनुमति (दैनिक ऑडिट के PR के लिए)।
- commits में मालिक का निजी ईमेल नहीं जाता: इस repo का `user.email` GitHub का noreply पता है।

**क्या अभी नहीं हुआ / जाँचा नहीं गया**

- `daily-audit` workflow अभी एक बार भी नहीं चला (पहली बार 23:30 UTC पर चलेगा)। उसका PR → `ci` dispatch → auto-merge वाला रास्ता अपरीक्षित है; पहले run के बाद देखें।

- Foreman **deploy नहीं हुआ** (मालिक के Cloudflare secrets चाहिए)। D1, cron और असली dispatch-चक्कर अपरीक्षित।
- D1, D4, D5, D9, D10, D12 जाँचें `not_run` हैं (रूप-विश्लेषक P2 में)। ईशोपनिषद् पर जाँचें अभी नहीं चलीं, क्योंकि पाठ अभी आया नहीं।
- Drive पुल के scripts लिखे हैं, चले नहीं (क़दम 0.6–0.7 मालिक के)।
- P1 और P2 शुरू नहीं हुए।

**दोबारा मत करो**

- §10.2 के फ़ैसले #1–#6 दोबारा न पूछें (दर्ज हैं)।
- `agents` को 0.33.0 से न बदलें, जब तक कोई कारण `DECISIONS.md` में न हो।
- लैपटॉप पर `C:\Program Files
odejs
ode.exe` का नाम `node1.exe` है (किसी और ने बदला; इसे न छुएँ)। Node चाहिए तो scratch में प्रति बनाकर PATH में जोड़ें।
- इस session के बाद `main` पर सीधे push नहीं: हर बदलाव PR से। संरक्षित रास्तों के PR पर मालिक `owner-approved` label लगाते हैं।

**अगला क़दम**

1. मालिक: क़दम 0.2 (`docs/USER_STEPS_hi.md`)। उत्तर आने पर `policy/quotas.md` भरें (PR)।
2. साथ-साथ, बिना keys के: P1 1.1 (बीज-सूचियाँ) और P2 2.1 के लिए ईशोपनिषद् के गवाह खोजना।

### session 1, turn 2 (2026-11-14, claude-fable-5-2)

- मालिक का उत्तर (क़दम 0.2 का आधा): model picker में Fable 5.2 पर "Requires usage credits" **नहीं दिखता**। usage credits बंद हैं या नहीं, यह उत्तर अभी बाक़ी है। दोनों मिलने पर `policy/quotas.md` में एक साथ दर्ज करें (संरक्षित रास्ता: PR + `owner-approved`)।
- PR #3 खुला (`claude/p1-seed-lists`): P1 1.1 की तीन बीज-सूचियाँ + `tools/catalog/build_seeds.py`। `tools/` संरक्षित है, इसलिए मालिक का `owner-approved` label चाहिए।
- बाक़ी बीज-सूचियाँ: उपपुराण, 28 आगम, पाञ्चरात्र। ईशोपनिषद् के गवाह खोजना (P2 2.1) अभी शुरू नहीं हुआ।
- अगला मालिक-क़दम: 0.3 (Google AI Studio)।
