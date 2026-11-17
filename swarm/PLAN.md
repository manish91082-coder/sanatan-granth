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
| 0.4 | Kaggle API token; quota, reset-दिन | 🔶 token लगा और चला (नया `KGAT_` रूप → `KAGGLE_API_TOKEN`)। बाक़ी: quota-पन्ने से GPU/TPU घंटे और reset-दिन |
| 0.5 | Groq key; Workers AI | ✅ Groq चला (gpt-oss-120b, qwen3.8-27b); Cloudflare token और Account ID परखे गए (Workers 200, D1 200) |
| 0.6 | Google Cloud project → Drive API → OAuth "In production" → `drive.file` → Desktop client | ✅ 16 नवंबर: मालिक के एक ख़ाली project में app "Sanatan Granth Library" (In production, Drive API चालू, billing नहीं); नया project नहीं बनाना पड़ा |
| 0.7 | rclone remote `granth:`; `Sanatan_Library/` tree; token Kaggle Secret में | ✅ remote (अपना client, `drive.file`), tree और `06_runs/` में test-फ़ाइल; अलगाव जाँचा (केवल `Sanatan_Library` दिखता है)। Kaggle Secret `RCLONE_GRANTH_CONF` मालिक को डालना बाक़ी (Kaggle का काम शुरू होने पर) |
| 0.8 | public repo, branch protection, required checks, CODEOWNERS, `CLAUDE.md` | ✅ protection लगा; परीक्षण-PR #1 पर लाल check ने merge रोका |
| 0.9 | schemas, ID-नियम, SPDX allow-list, `swarm/*`, `policy/*`, 3 canaries | ✅ CI में canaries 3/3 |
| 0.10 | जाँचें v0: R1–R14, A3/D11, D2/D3/D6/D7/D8 | ✅ v0। D1, D4, D5, D9, D10, D12 अभी `not_run` (रूप-विश्लेषक P2 में); ईश पर चलाना बाक़ी |
| 0.11 | Cloudflare D1 + Foreman Agent + dead-man cron + status-पन्ना | ✅ deploy हुआ; ख़ाली batch का पूरा चक्कर सफल (dispatch → Actions → callback → बही, ~10 s)। 16 नवंबर: retry-नियम (PR #23) deploy हुआ और परखा गया। Healthchecks/UptimeRobot नहीं जोड़े (वैकल्पिक) |
| 0.12 | Escalation: GitHub mobile सूचना + Cloudflare status-पन्ना | ✅ bot-issue #27 की सूचना मालिक को पहुँची (15 नवंबर); मासिक जाँच: `notify-test` workflow |
| 0.13 | साप्ताहिक meta-audit cloud task | ✅ routine बना (रविवार 03:37 UTC, Sonnet 5.5, connectors हटे); पहला run: PR #30, issue #31 (0 RED, 3 AMBER)। बाक़ी: मालिक usage-% और environment का network "Limited" देखें |
| 0.14 | दिन-8 की Drive-token जाँच | ⏳ 24 नवंबर 2026 को `bash drive/token_check.sh` |

**P0-gate:** किसी मंच ने card/phone नहीं माँगा · CI हरा · canaries 3/3 · Foreman का एक पूरा dispatch-चक्कर · Drive में test-फ़ाइल · पहला audit-issue।

## Lanes

| Lane | हालत |
|---|---|
| सूची (P1) | 1.1 आंशिक: 18 विद्याएँ, 18 महापुराण, मुक्तिका 108 (`catalog/seed/`)। बाक़ी: उपपुराण, 28 आगम, पाञ्चरात्र; फिर 1.2 ACC parse |
| स्रोत/गवाह | ईश: 4 गवाह दर्ज (केवल तुलना), पहला मिलान `audit/witness/isha_collation_v0.json`। बाक़ी: दूसरा काण्व गवाह, PD छपे संस्करण का OCR, तब text-lock |
| ड्राफ़्ट/जूरी | Gemini key तैयार (Draft B / जज-पैर 1 चल सकता है)। दूसरा परिवार (Groq gpt-oss या Kaggle Qwen) अभी नहीं: 0.4–0.5 बाक़ी। ड्राफ़्ट text-lock के बाद ही |
| Kaggle | रुका: token (0.4) चाहिए। फ़िल्म का backup पहले (फ़ैसला #9 खुला) |
| Claude audit | चालू: साप्ताहिक routine + `issue-notify` |

## काम का ढंग (14 नवंबर का फ़ैसला)

मालिक के interactive session में Claude अपने PR पर label लगाकर, checks हरे होने पर ख़ुद merge करता है (`swarm/DECISIONS.md`)। keys/logins मालिक के ही रहते हैं।

## खुले फ़ैसले (मालिक)

- #7 P4-मंच कब · #8 Opus/Fable भूमिकाएँ · #9 Kaggle पर फ़िल्म बनाम पुस्तकालय · #10 अनुमति-पत्र · #11–#15 (मास्टर योजना §10.2)।
- **नया:** इस परियोजना के AI-मसौदों का खुला लाइसेंस (अभी `LicenseRef-sanatan-granth-draft`; `LICENSES.md`)।
- **नया:** मास्टर योजना की प्रति इस public repo में रखें या नहीं (`docs/MASTER_PLAN_POINTER.md`)।

## अगले 3 काम

> **मालिक के निर्देश (16–17 नवंबर 2026):** (1) स्रोत पहले: हर ग्रंथ का आधार-संस्करण तय हो। (2) अंतिम स्रोत-फ़ैसला बाद में; पहले पूरी स्वचालित कड़ी बनकर परखी जाए, अस्थायी भारतीय आधार के साथ। (3) "कड़ी ठीक करो": pilot की कमज़ोरियाँ पहले। (4) quota लौटने पर जजों की तुलना और Foreman-run चलाओ। कोई पाठ `texts/` में तभी जाएगा जब उसका स्रोत तय और lock हो।

**P2 की स्थिति (17 नवंबर, 18:45 IST):** स्वार्म 24×7 चल रहा है (Foreman की 20 मिनट की घड़ी, संचालक, कतार; `swarm/SWARM_24x7.md`)। quota की रुकावट का हल जुड़ा (HANDOFF turn 37): नया स्रोत OVHcloud (बिना खाते, बिना key), उसके मॉडल नापे गए, और roster v0.2 में अब कोई एक स्रोत बंद हो तो भी पहले दर्जे की रचना बनती है (selftest की जाँच)। **नई रचना पर v0.7 की पहली पूरी कड़ी स्वार्म से चली (foreman-job run 44087537183, PR #65): पहले दौर की सहमति 16/18 (88.9%; सीमा 60%), बैज C 16 / D 2, 18.5 मिनट, OpenRouter के बिना।** पुरानी रचनाओं पर सहमति 5/18, 3/18, 2/18 थी। यह एक ही run है; रोज़ का `isha-e2e` इसे दोहराएगा।

1. **दोहराव देखना:** branch `swarm-state` की `STATUS.md` और `runs/isha-e2e.*.json`: रोज़ के run में सहमति 60% के ऊपर टिकती है या नहीं; ERNIE उपलब्ध हो तब की रचना (जज ERNIE) का नतीजा; `judge-requal` (ERNIE और OVH के जज दोबारा)। जज के `pick` की अस्थिरता (0.278) पर सोचना: अंतिम पाठ का चुनाव उसी पर टिकता है।
2. **गीता 1–2 पर पूरी कड़ी (P2 2.2):** `run_e2e.py` को कई अध्यायों वाले ग्रंथ के लिए तैयार करना (`TEXTS` में gita, `assemble` अध्याय-वार, स्रोत `tools/witness/gita_collate.py`), फिर कतार में `gita-1-2-e2e` को `enabled: true`। OpenRouter पर बड़े टुकड़े नापना (अनुरोध गिने जाते हैं)।
3. **स्रोत और बचे काम:** `catalog/_base_editions.json` आगे बढ़ाना; मालिक का G1-फ़ैसला; PD संदर्भ-अनुवाद जज को (Hiriyanna 1911); और जजों को योग्य बनाना (gpt-oss, Nemotron की canary-परीक्षा → roster का PR)। P0 के छोटे काम: 24 नवंबर को 0.14; Kaggle का quota-पन्ना और Kaggle Secret।

---
अंतिम अपडेट: 2026-11-17 · claude-fable-5-2 · निर्माण-session 1, turn 37
