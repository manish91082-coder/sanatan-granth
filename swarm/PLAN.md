# PLAN: यहाँ से फिर शुरू करें

> एक पन्ना। एक समय में एक ही session इसे बदले (पहले `git pull`)। बदलने के बाद अंतिम पंक्ति अपडेट करें।

## वर्तमान चरण

**P0 नींव** (मास्टर योजना §9.1)। P1 और P2 इसके बाद; P2-gate पर रुककर मालिक को रिपोर्ट।

## P0 की हालत

| क़दम | क्या | हालत |
|---|---|---|
| 0.1 | फ़ैसले #1–#6 | ✅ `swarm/DECISIONS.md` में दर्ज |
| 0.2 | usage credits बंद; Fable picker | ✅ credits बंद; Fable पर credits नहीं माँगता (`policy/quotas.md`) |
| 0.3 | AI Studio: एक project, एक key; RPD/RPM; Batch परीक्षण | ✅ सीमाएँ दर्ज; key Actions से चली (Flash-Lite, strict JSON ठीक); मुफ़्त Batch ने HTTP 400 दिया, इसलिए Batch क्षमता में नहीं गिना। फ़ैसला: एक project, एक key (`DECISIONS.md`) |
| 0.4 | Kaggle API token; quota, reset-दिन | ⏳ मालिक |
| 0.5 | Groq key; Workers AI | ⏳ मालिक |
| 0.6 | Google Cloud project → Drive API → OAuth "In production" → `drive.file` → Desktop client | ⏳ मालिक |
| 0.7 | rclone remote `granth:`; `Sanatan_Library/` tree; token Kaggle Secret में | ⏳ मालिक + Claude |
| 0.8 | public repo, branch protection, required checks, CODEOWNERS, `CLAUDE.md` | ✅ protection लगा; परीक्षण-PR #1 पर लाल check ने merge रोका |
| 0.9 | schemas, ID-नियम, SPDX allow-list, `swarm/*`, `policy/*`, 3 canaries | ✅ CI में canaries 3/3 |
| 0.10 | जाँचें v0: R1–R14, A3/D11, D2/D3/D6/D7/D8 | ✅ v0। D1, D4, D5, D9, D10, D12 अभी `not_run` (रूप-विश्लेषक P2 में); ईश पर चलाना बाक़ी |
| 0.11 | Cloudflare D1 + Foreman Agent + dead-man cron + status-पन्ना | 🔨 code `foreman/` में; deploy मालिक की keys के बाद |
| 0.12 | Escalation: GitHub mobile सूचना + Cloudflare status-पन्ना | ⏳ मालिक (परीक्षण-issue) |
| 0.13 | साप्ताहिक meta-audit cloud task | ⏳ मालिक (prompt: `policy/audit_prompt.md`) |
| 0.14 | दिन-8 की Drive-token जाँच | ⏳ 0.7 के 8 दिन बाद |

**P0-gate:** किसी मंच ने card/phone नहीं माँगा · CI हरा · canaries 3/3 · Foreman का एक पूरा dispatch-चक्कर · Drive में test-फ़ाइल · पहला audit-issue।

## Lanes

| Lane | हालत |
|---|---|
| सूची (P1) | 1.1 आंशिक: 18 विद्याएँ, 18 महापुराण, मुक्तिका 108 (`catalog/seed/`)। बाक़ी: उपपुराण, 28 आगम, पाञ्चरात्र; फिर 1.2 ACC parse |
| स्रोत/गवाह | ईश: 4 गवाह दर्ज (केवल तुलना), पहला मिलान `audit/witness/isha_collation_v0.json`। बाक़ी: दूसरा काण्व गवाह, PD छपे संस्करण का OCR, तब text-lock |
| ड्राफ़्ट/जूरी | Gemini key तैयार (Draft B / जज-पैर 1 चल सकता है)। दूसरा परिवार (Groq gpt-oss या Kaggle Qwen) अभी नहीं: 0.4–0.5 बाक़ी। ड्राफ़्ट text-lock के बाद ही |
| Kaggle | रुका: token (0.4) चाहिए। फ़िल्म का backup पहले (फ़ैसला #9 खुला) |
| Claude audit | रुका: 0.13 |

## काम का ढंग (14 नवंबर का फ़ैसला)

मालिक के interactive session में Claude अपने PR पर label लगाकर, checks हरे होने पर ख़ुद merge करता है (`swarm/DECISIONS.md`)। keys/logins मालिक के ही रहते हैं।

## खुले फ़ैसले (मालिक)

- #7 P4-मंच कब · #8 Opus/Fable भूमिकाएँ · #9 Kaggle पर फ़िल्म बनाम पुस्तकालय · #10 अनुमति-पत्र · #11–#15 (मास्टर योजना §10.2)।
- **नया:** इस परियोजना के AI-मसौदों का खुला लाइसेंस (अभी `LicenseRef-sanatan-granth-draft`; `LICENSES.md`)।
- **नया:** मास्टर योजना की प्रति इस public repo में रखें या नहीं (`docs/MASTER_PLAN_POINTER.md`)।

## अगले 3 काम

1. मालिक के क़दम 0.2 → 0.7, एक-एक करके (`docs/USER_STEPS_hi.md`)।
2. Foreman deploy (0.11) और एक ख़ाली batch का पूरा चक्कर।
3. P1 1.1–1.4 (बीज-सूचियाँ, ACC, title-index, Wikidata): इन्हें keys नहीं चाहिए, PR से चलेंगे।

---
अंतिम अपडेट: 2026-11-14 · claude-fable-5-2 · निर्माण-session 1, turn 7
