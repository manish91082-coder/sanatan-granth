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

> **मालिक का निर्देश (16 नवंबर 2026): स्रोत पहले।** जब तक किसी ग्रंथ का आधार-संस्करण तय न हो और मालिक उसे G1 में स्वीकार न करें, उस ग्रंथ पर OCR, पाठ-lock या अनुवाद नहीं। कसौटी: `docs/SOURCE_SELECTION_hi.md`; सूची: `catalog/_base_editions.json`।

1. **आधार-संस्करण की सूची, खेप 1 पूरी करना (ईश, गीता):** उम्मीदवारों के मुखपृष्ठ और भूमिका देखना; संपादकों की मृत्यु-तिथि दो स्रोतों से (सबसे पहले वासुदेव लक्ष्मण शास्त्री पणशीकर: उनका एक तथ्य निर्णयसागर के कई संस्करण खोल देगा); गीता प्रेस और वाणी विलास की प्रतियाँ ढूँढना। फिर मालिक का G1-फ़ैसला।
2. **खेप 2 से आगे:** मुक्तिका के 108 उपनिषद् → चार वेद-संहिताएँ → महाभारत, रामायण → 18 महापुराण → विषय-क्रम से।
3. **रुका हुआ (स्रोत तय होने तक):** ईश का OCR-सुधार, पाठ-lock, ड्राफ़्ट और जूरी (P2 2.1 का बाक़ी हिस्सा)। P0 के छोटे काम: 24 नवंबर को 0.14; Kaggle का quota-पन्ना और Kaggle Secret।

---
अंतिम अपडेट: 2026-11-16 · claude-fable-5-2 · निर्माण-session 1, turn 28
