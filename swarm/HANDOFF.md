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

### session 1, turn 3 (2026-11-14, claude-fable-5-2)

- क़दम 0.2 पूरा: मालिक ने बताया कि usage credits **बंद** हैं, और Fable 5.2 पर "Requires usage credits" **नहीं दिखता**। `policy/quotas.md` में दर्ज करना बाक़ी (0.3–0.5 के उत्तरों के साथ एक PR में)।
- PR #4 खुला (`claude/p2-isha-witnesses`): तुलना-कुंजी, ईश के 4 गवाहों का metadata (सब `pending_owner`, केवल तुलना), पहला मिलान: 18 में 9 कुंजी-बराबर, 5 लगभग, 2 अलग (मंत्र 6, 15), 2 गवाह B में नहीं (16, 17)।
- ईश के लिए अगला काम: (1) दूसरा काण्व-शाखा गवाह (GRETIL केवल तुलना; शांकरभाष्य वाले पन्ने में मूल), (2) हिरियण्णा 1911 के संपादक की मृत्यु-तिथि दो स्रोतों से, (3) Actions में Tesseract `san` से अपना OCR, (4) तब text-lock।
- DCS में ईशोपनिषद् नहीं है (वाजसनेयि-माध्यन्दिन के केवल अध्याय 1–15 हैं): देखा गया, दोबारा न खोजें।

### session 1, turn 4 (2026-11-14, claude-fable-5-2)

- मालिक का नया फ़ैसला: merge और label Claude करे (`DECISIONS.md`, PR #5)। PR #2, #3, #4, #5 merge हुए; सब पर चारों checks हरे थे।
- क़दम 0.2 `policy/quotas.md` में दर्ज।
- AI Studio (क़दम 0.3): app के built-in browser में Google का sign-in पन्ना आया (वहाँ login नहीं है)। Claude password नहीं डालता। मालिक से पूछा गया है: pane में ख़ुद sign in करें, या Claude उनके Chrome का उपयोग करे। key बनाना और GitHub secret में डालना मालिक का ही काम रहेगा।
- "दोबारा मत करो": PR #1 बंद परीक्षण-PR है; उसे न खोलें।

### session 1, turn 5–7 (2026-11-14, claude-fable-5-2)

- मालिक ने app के browser pane में Google login किया; Claude ने AI Studio की सीमाएँ पढ़कर दर्ज कीं (PR #7), projects/keys गिने (3 projects, 1 key; PR #8)।
- मालिक ने `GEMINI_API_KEY` secret ख़ुद डाला। फ़ैसला: एक project, एक key ही (`DECISIONS.md`, PR #9)। नया project/key बनाने की बात दोबारा न उठाएँ, जब तक मालिक ख़ुद न कहें।
- `provider-smoke` workflow चला (run 43623513779): key चली; मुफ़्त Batch नहीं चला (HTTP 400)।
- अगला मालिक-क़दम: 0.4 (Kaggle token → `KAGGLE_USERNAME`, `KAGGLE_KEY`) और 0.5 (Groq → `GROQ_API_KEY`; Cloudflare → `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`)। सबसे आसान तरीका: terminal में `gh secret set NAME --repo manish91082-coder/sanatan-granth` और paste।
- अगला Claude-काम (keys के बिना): ईश का दूसरा काण्व गवाह + PD छपे संस्करण का OCR-workflow → text-lock; फिर Gemini से पहला ड्राफ़्ट।

### session 1, turn 8–9 (2026-11-15, claude-fable-5-2)

- `tools/setup/set_secrets.ps1` merge हुई (PR #12): मालिक एक बार चलाकर सारे secrets लगा सकते हैं; keys Claude को नहीं दिखतीं। मालिक ने keys के screenshot भेजने की बात कही थी; मना किया गया (keys chat में नहीं आनी चाहिए)।
- **सीख (दोबारा मत करो):** GITHUB_TOKEN से बना PR (#11, दैनिक ऑडिट) merge नहीं हो पाया। उसका `pull_request` run `ACTION_REQUIRED` (approval) पर अटकता है, और `workflow_dispatch` से चले हरे checks भी उसे नहीं खोलते। इसलिए दैनिक रिपोर्ट अब branch `audit-log` पर सीधे जाती है (main में नहीं)।
- **आगे के लिए:** Actions से बनने वाले डेटा-PR (अनुवाद-परतें) इसी दीवार से टकराएँगे। रास्ता: PR `FOREMAN_DISPATCH_TOKEN` (मालिक का fine-grained token; उसमें Pull requests: Read and write भी चाहिए) से खोलें, ताकि checks सामान्य रूप से चलें। यह अभी लागू नहीं हुआ।
- साप्ताहिक audit के prompt (`policy/audit_prompt.md`) में "दैनिक रिपोर्ट branch `audit-log` पर हैं" जोड़ना बाक़ी।

### session 1, turn 10 (2026-11-15, claude-fable-5-2)

- मालिक ने `set_secrets.ps1` चलाकर सारे 8 secrets लगाए। `secrets-check` run 43685007102 का नतीजा:
  - **Kaggle:** चला, पर token नए रूप (`KGAT_…`) का है: Bearer से 200, पुराने basic-auth से 401। workflows में `KAGGLE_API_TOKEN: ${{ secrets.KAGGLE_KEY }}` दें; पुराना `KAGGLE_USERNAME`/`KAGGLE_KEY` जोड़ा CLI में नहीं चलेगा।
  - **Groq:** चला; `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b` उपलब्ध।
  - **Cloudflare:** token सक्रिय है, पर **`CLOUDFLARE_ACCOUNT_ID` ग़लत है** (7 अक्षर; 32 hex अक्षर होने चाहिए), इसलिए Workers/D1 के अनुरोध 404 देते हैं। मालिक को ठीक करना है। ठीक होने तक Foreman deploy न चलाएँ। D1 अनुमति अभी परखी नहीं जा सकी।
  - **FOREMAN_DISPATCH_TOKEN:** चला, Contents write है। Pull requests write की जाँच नहीं हो सकती (बिना कुछ लिखे)। token को 13 repos दिखते हैं; यह "केवल एक repo" चुनने पर भी सार्वजनिक repos के कारण हो सकता है, पक्का नहीं।
- Foreman deploy किसके बटन से: `DECISIONS.md` के अनुसार अभी मालिक के; मालिक से पूछा गया है।

### session 1, turn 11 (2026-11-15, claude-fable-5-2)

- `CLOUDFLARE_ACCOUNT_ID` ठीक हुआ (मालिक ने dashboard का पता दिखाया; Account ID गुप्त key नहीं, पहचान है, इसलिए Claude ने `gh secret set` से लगाया)। `secrets-check` run 43685486596: Workers 200, D1 200 (0 databases), workers.dev subdomain मौजूद। **ऊपर turn 10 की "Account ID ग़लत" वाली बात अब पुरानी है।**
- अब Foreman deploy (क़दम 0.11) के लिए सब तैयार है: पहली बार `foreman-deploy` को `create_d1=yes` के साथ चलाना है। किसके बटन से, यह मालिक से पूछा गया है।

### session 1, turn 12 (2026-11-15, claude-fable-5-2)

- मालिक ने कहा: Foreman का deploy Claude चलाए ("हाँ, चलाओ")। पहला run (43685780426) D1 बनाने पर रुका: Cloudflare token में **D1 Edit** नहीं है (D1 list चलता है, create नहीं; "Authentication error 10000")। मालिक को token में Account → D1 → Edit जोड़ना है।
- **निजता-घटना:** wrangler ने त्रुटि-संदेश में मालिक का ईमेल public Actions log में छापा। वह run तुरंत मिटाया गया। `foreman-deploy.yml` में अब हर wrangler-आउटपुट ईमेल-filter (`REDACT`) से गुज़रता है। **नया कोई workflow जो wrangler या किसी खाते-CLI को चलाए, यही filter लगाए।**
- अगला: token ठीक होते ही `gh workflow run foreman-deploy.yml -f create_d1=yes`, फिर ख़ाली batch का चक्कर (`/admin/enqueue-noop` + `/admin/tick`, HMAC के साथ; इसके लिए एक छोटा हाथ-से-चलने वाला workflow चाहिए, क्योंकि shared secret केवल GitHub/Cloudflare में है)।
- **CI की सीख:** PR को label के साथ एक ही आदेश में बनाने पर `opened` और `labeled` के दो runs टकराते थे; रद्द हुआ run PR को BLOCKED कर देता था। `ci.yml` में अब `cancel-in-progress: false` है। फिर भी सुरक्षित क्रम: पहले PR बनाएँ, फिर label लगाएँ।

### session 1, turn 13–16 (2026-11-15, claude-fable-5-2)

- **Foreman deploy हो गया** (run 43687425895; मालिक ने Cloudflare token में D1 Edit और Workers Scripts Edit जोड़े)। D1 `sanatan-granth-ledger` बना, migration लगा, Worker `sanatan-granth-foreman` चल रहा है। पता repo variable `FOREMAN_URL` में है; `/status` और `/status.json` सार्वजनिक हैं। deploy-log में ईमेल नहीं छपा (filter काम कर रहा है)।
- **ख़ाली batch का चक्कर अभी अधूरा** (`foreman-selftest` run 43687614326): enqueue ✔, tick ✔ (1 action), पर **dispatch HTTP 403**। कारण लगभग पक्का: `FOREMAN_DISPATCH_TOKEN` (fine-grained) में Contents **Read and write** नहीं है। पिछली `secrets-check` का `contents_write: true` भ्रामक था: वह उपयोगकर्ता की भूमिका दिखाता है, token की अनुमति नहीं। मालिक को token में Contents: Read and write और Pull requests: Read and write जोड़ने हैं; फिर `gh workflow run foreman-selftest.yml`।
- **ज्ञात कमी (ठीक करना बाक़ी):** dispatch विफल होने पर job `failed` में अटक जाता है; `planTick` उसे दोबारा कतार में नहीं डालता (callback वाला रास्ता डालता है)। बही में अभी एक `failed` selftest-पंक्ति है; वह हानिरहित है।
- **Claude की सीमा:** 15 नवंबर को साप्ताहिक "all models" 96% पर था (reset सोमवार 3:30 PM IST)। नया काम reset के बाद, **नए session** में शुरू करें (यह session बहुत लंबा है)। मालिक को सलाह दी गई: निर्माण Opus 5.5 पर, गहरे audit Fable पर; "Buy usage credits" कभी नहीं।
- Cloudflare token अभी बहुत चौड़ा है (सारे खातों/zones की ~175 read-अनुमतियाँ + दो edit)। बाद में केवल-ज़रूरी अनुमतियों वाला token बनवाना अच्छा रहेगा (मालिक का काम)।
