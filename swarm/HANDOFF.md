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

### session 1, turn 17 (2026-11-15, claude-fable-5-2) — यहाँ से नया session उठाए

- **ख़ाली batch का पूरा चक्कर सफल** (`foreman-selftest` run 43688892718): enqueue → tick → repository_dispatch → `foreman-job` run 43688902812 (noop, success) → callback → बही में `done`, ~10 सेकंड में। मालिक ने GitHub token में Contents और Pull requests: Read and write जोड़े थे। Foreman का अपना 5-मिनट वाला schedule भी चलता दिखा (`last_tick_source: schedule`)।
- बही में एक पुरानी `failed` selftest-पंक्ति है (403 वाली); हानिरहित।
- **P0-gate की स्थिति:** card/phone नहीं माँगा ✔ · CI हरा ✔ · canaries 3/3 ✔ · Foreman का पूरा dispatch-चक्कर ✔ · Drive में test-फ़ाइल ✘ (क़दम 0.6–0.7 बाक़ी) · पहला audit-issue ✘ (क़दम 0.13 बाक़ी) · सूचना-परीक्षण (0.12) बाक़ी।
- **अगले session के पहले काम, क्रम से:**
  1. क़दम 0.6–0.7 (Drive: Google Cloud OAuth client → rclone `granth:`), मालिक के साथ एक-एक क़दम।
  2. क़दम 0.12 (परीक्षण-issue) और 0.13 (साप्ताहिक audit cloud task; `policy/audit_prompt.md` में "दैनिक रिपोर्ट branch `audit-log` पर" जोड़कर)।
  3. Kaggle: workflows में `KAGGLE_API_TOKEN: ${{ secrets.KAGGLE_KEY }}`; quota-पन्ने से GPU/TPU घंटे और reset-दिन (मालिक pane में login करें)।
  4. ईश का text-lock: दूसरा काण्व गवाह + हिरियण्णा 1911 का PD-दर्जा (2 स्रोत) + Actions में Tesseract OCR।
  5. `planTick` में dispatch-विफल `failed` jobs का retry; डेटा-PR `FOREMAN_DISPATCH_TOKEN` से खोलना।
  6. बाक़ी बीज-सूचियाँ (उपपुराण, 28 आगम, पाञ्चरात्र), फिर P1 1.2 (ACC)।

### session 1, turn 18 (2026-11-15, claude-fable-5-2)

- **हुआ (PR #23, main `d8d3759`):** `planTick` अब `failed` में अटके job को 10 मिनट के backoff के बाद retry-सीमा के भीतर दोबारा कतार में डालता है, वरना `needs_expert`; tick की query `failed` भी पढ़ती है; tests 13/13। `policy/audit_prompt.md` में लिखा कि दैनिक रिपोर्टें branch `audit-log` पर हैं।
- **अभी deploy नहीं हुआ:** Cloudflare पर पुराना Foreman चल रहा है। `foreman-deploy` दोबारा चलाने पर ही retry-नियम लागू होगा (मालिक की हाँ चाहिए)। deploy के बाद बही की पुरानी `failed` selftest-पंक्ति एक बार noop चलकर `done` होगी; यह अपेक्षित है।
- **क़दम 0.12:** परीक्षण-issue #24 खुला है। मालिक बताएँ कि फ़ोन/ईमेल पर सूचना आई या नहीं; आई हो तो issue बंद करें और PLAN में 0.12 ✅ करें।
- **Claude की सीमा:** 15 नवंबर दोपहर "Weekly · all models" 97% था (reset सोमवार 16 नवंबर 3:30 PM IST)। Fable का उपयोग इसी साझा सीमा में गिनता है। इसलिए turn 17 की क्रम-सूची जस की तस है; अगला बड़ा काम Drive की चाबी (0.6–0.7) ही है।

### session 1, turn 19–20 (2026-11-15, claude-fable-5-2)

- **क़दम 0.12 पूरा।** issue #24 वाला परीक्षण अमान्य था: वह `gh` से मालिक के अपने खाते के नाम से बना था, और GitHub अपनी गतिविधि की सूचना नहीं भेजता। सही परीक्षण के लिए `notify-test` workflow जोड़ा (PR #26); उससे bot के नाम से issue #27 खुला, और मालिक ने पुष्टि की कि सूचना पहुँची। दोनों issue बंद हैं।
- **सीख:** सूचना-परीक्षण हमेशा bot से बने issue से करें, `gh issue create` से नहीं।
- **P0-gate में बाक़ी:** Drive की test-फ़ाइल (0.6–0.7) और पहला साप्ताहिक audit-issue (0.13)। Foreman का retry-नियम (PR #23) अब भी deploy नहीं हुआ।

### session 1, turn 21 (2026-11-16, claude-fable-5-2) — साप्ताहिक सीमा reset के बाद

मालिक ने कहा: "तुम तय करो और आगे बढ़ो।"

- **Foreman:** `foreman-deploy` run 43847209611 सफल (log में कोई ईमेल नहीं)। selftest run 43847353730 सफल; पुरानी `failed` पंक्ति नए retry-नियम से `queued` हुई।
- **क़दम 0.13 पूरा:** cloud routine `trig_01CZiRzJYuzdSkLRSqPpzMY8` ("sanatan-granth साप्ताहिक meta-audit"; cron `37 3 * * 0`; claude-sonnet-5-5; connectors हटे)। prompt routine में ही चिपका है (`policy/audit_prompt.md` का विस्तारित रूप)। पहला run ~2 मिनट चला: PR #30 (merge हुआ) और issue #31 (0 RED, 3 AMBER)।
  - AMBER M2: 14 नवंबर का दैनिक run नहीं है। कारण: `daily-audit` workflow 15 नवंबर को बना; यह अपेक्षित है।
  - AMBER M5: `sources/manifest.jsonl` ख़ाली, जबकि `witnesses/` में रिकॉर्ड हैं। खुला काम।
  - AMBER M9: `state/heartbeat.json` नहीं, R14 रोज़ WARN देता है। खुला काम: R14 को Foreman के `/status.json` से जोड़ना या heartbeat लिखना।
  - routine का environment "Default" है; उसका network "Limited" है या नहीं, यह API से नहीं दिखा। मालिक claude.ai/code में देखें। usage-% भी मालिक देखकर बताएँ।
- **सूचना:** cloud routine issue मालिक के अपने खाते के नाम से खोलता है, जिसकी सूचना GitHub नहीं भेजता। `issue-notify` workflow (PR #32) ऐसे issue पर bot-टिप्पणी जोड़ता है; #31 पर परखा गया।
- **Drive (0.6–0.7):** `tools/setup/setup_drive.ps1` तैयार (PR #29)। app के browser-pane में Google sign-in नहीं है (accounts.google.com का sign-in पन्ना आया); मालिक के sign-in के बाद ही 0.6 आगे बढ़ेगा। मौजूदा Google Cloud project उपयोग करें (नया नहीं), जैसा मास्टर योजना 0.6 कहती है।
- **ईश के गवाह:**
  - `ia-hiriyanna-1911`: पन्ने देखे गए; मंत्र देवनागरी में **नहीं** छपे (केवल अंग्रेज़ी अनुवाद)। अब `pd_translation` / `reference`। अनुवादक की मृत्यु 1950 दो स्रोतों से (LoC authority n50034752; Wikidata Q15452708 ← BnF) → `LicenseRef-PD-India-US`। G1 अब भी मालिक पर।
  - नया `ia-nsp-108-1925`: निर्णयसागर का 108-उपनिषद् संग्रह (तृतीय संस्करण 1925, संपादक वासुदेव शर्मा पणशीकर)। ईश पृ. 1 (leaf n13), काण्व क्रम, 18 मंत्र। इस प्रति के पृ. 1 पर हाथ की लिखावट है और archive की OCR कमज़ोर है। संपादक की मृत्यु-तिथि नहीं मिली → `LicenseRef-unknown`, केवल तुलना।
  - **न करें:** Claude का पन्ना "पढ़कर" टंकित पाठ गवाह न माना जाए (मॉडल को पाठ याद है; स्वतंत्र नहीं)।
- **अगला:** PLAN के "अगले 3 काम"। Kaggle का quota-पन्ना (0.4) भी मालिक के sign-in पर टिका है।

### session 1, turn 22 (2026-11-16, claude-fable-5-2) — Drive का पुल बना; P0-gate

- मालिक ने browser-pane में Google sign-in किया और कहा कि Drive के लिए पहले से बना OAuth client ही उपयोग हो।
- Google Cloud में देखा: मालिक के एक मौजूदा project में दो Desktop clients हैं; consent screen "In production", External। लैपटॉप का पुराना Drive remote इन्हीं में से एक client से चलता है।
- **rclone का अपना login नहीं चला:** Windows की "excluded port range" 53642–53741 में rclone का तय port 53682 आता है (`netsh interface ipv4 show excludedportrange protocol=tcp`)। यह sandbox की बात नहीं थी; मालिक के terminal में भी वही त्रुटि आई। दोबारा `rclone config reconnect` न आज़माएँ।
- **हल:** `tools/setup/drive_login.py` (PKCE, ख़ाली loopback port, scope केवल `drive.file`; token केवल rclone config के `[granth]` section में)। मालिक ने browser में Allow दबाया; login सफल।
- `tools/setup/setup_drive.ps1` से tree (9 folders) और `06_runs/setup_test_20261116T105414Z.txt` बने। पुराना remote जस का तस (scope और token वही)।
- **अलगाव अधूरा (मालिक को बताया):** `rclone lsd granth:` में `Sanatan_Library` के अलावा उसी app के बनाए, मालिक के दूसरे काम के कुछ folders भी दिखते हैं। फ़िल्म का folder नहीं दिखता। `drive.file` की सीमा app (Cloud project) के स्तर पर है, client ID के स्तर पर नहीं; इसलिए उसी project में नया client बनाने से कुछ नहीं बदलेगा, अलग project चाहिए। तब तक token Kaggle Secret में न जाए।
- **P0-gate:** सातों शर्तें पूरी (card/phone नहीं माँगा; CI हरा; canaries 3/3; Foreman का पूरा चक्कर; सूचना; Drive test-फ़ाइल; पहला साप्ताहिक audit-issue)।
- terminal tool की सीख: `;` से जुड़े दो commands एक साथ भेजने पर tool ने Ctrl-C भेज दिया; एक बार में एक ही command भेजें।

### session 1, turn 23 (2026-11-16, claude-fable-5-2) — Drive का अलग project: काम बीच में

मालिक ने कहा: "हाँ, अलग बनाओ" (पुस्तकालय के Drive-token के लिए अलग Cloud project)।

- **नया project नहीं बनाया:** console ने दिखाया कि मालिक के खाते में केवल 1 project-slot बचा है। मालिक का एक पूरी तरह ख़ाली project मिला ("Gemini Project GAG": कोई API key, OAuth client, service account या consent screen नहीं), इसलिए वही उपयोग हो रहा है। इसमें कोई Gemini key नहीं बनेगी (मास्टर योजना 0.6 की शर्त)।
- **हो चुका:** उस project में Google Drive API चालू; OAuth "Project configuration" form में App name "Sanatan Granth Library" भरा गया।
- **मालिक के हाथ से बाक़ी (pane में):** support email चुनना → Audience "External" → contact email → policy पर सहमति → Create।
- **फिर Claude:** Audience पन्ने पर "Publish app" (In production); Clients → Create client → Desktop app का form भरना। **अंतिम "Create" और client secret की नक़ल मालिक करें; Claude वह dialog न पढ़े।**
- **फिर terminal में (मालिक टाइप करें):** `python tools\setup\drive_login.py --remote granth --ask-client` (branch `claude/drive-own-project` में; अभी main में नहीं)। यह पुराने client वाला `granth` हटाकर नए client से बनाता है।
- **उससे पहले Claude:** पुराने app से बना `granth:Sanatan_Library` (9 ख़ाली folders + 1 test-फ़ाइल) Drive के trash में भेजे, वरना नए app को वह नहीं दिखेगा और उसी नाम का दूसरा folder बन जाएगा।
- **फिर:** `tools\setup\setup_drive.ps1` से नया tree + test-फ़ाइल; `rclone lsd granth:` में केवल `Sanatan_Library` दिखना चाहिए (अलगाव की जाँच); `drive/README.md`, PLAN, DECISIONS अद्यतन।

### session 1, turn 24–26 (2026-11-16, claude-fable-5-2) — Drive का अलगाव पूरा

- मालिक ने pane में OAuth form पूरा किया। Claude ने Branding में homepage (repo) और privacy link (`docs/PRIVACY.md`, PR #36) भरे, authorized domain `github.com` जोड़ा, और app को "In production" किया। Desktop client "sanatan-granth rclone" का form भरा; Create मालिक ने दबाया।
- मालिक ने download हुई client-फ़ाइल का पथ chat में दिया और कहा "तुम ही कर लो"। `drive_login.py --client-json` जोड़ा: script फ़ाइल ख़ुद पढ़ती है। **client secret का मान कहीं दोहराया या लिखा नहीं गया** (न repo, न commit, न log)।
- **नतीजा:** `granth` अब नए client पर (project अलग), scope `drive.file`, token मौजूद। `rclone lsd granth:` में केवल `Sanatan_Library`। नया tree + `06_runs/setup_test_20261116T115854Z.txt`। पुराना remote जस का तस।
- **Claude की चूक (दोहराएँ नहीं):** एक बार remote जाँचे बिना tree बना दिया, जो पुराने client से बन गया; उसे trash में भेजना पड़ा। नियम: पहले `rclone config show granth` से client-prefix और token देखें, फिर ही कुछ बनाएँ। Drive के trash में पुराने app के दो test-trees पड़े हैं (हानिरहित; 30 दिन में अपने-आप हटेंगे)।
- **terminal tool:** `run_in_terminal` ने तीन बार चलते command पर Ctrl-C भेज दिया (shell देर से "शुरू" बताता है)। लंबे या browser खोलने वाले command Bash में `run_in_background` से चलाएँ; वह चला।
- **Bash heredoc की सीख:** heredoc के भीतर Python में backslash आधे हो जाते हैं (`\\n` → newline)। regex या backslash वाले बदलाव Write tool से बनी script-फ़ाइल से करें।
- **मालिक के लिए बाक़ी:** Downloads में पड़ी `client_secret_*.json` हटाना (rclone config में मान आ चुका है); चाहें तो console में उस client का secret बदलना, क्योंकि फ़ाइल का पाठ chat में दिख चुका है।

### session 1, turn 27 (2026-11-16, claude-fable-5-2) — ईश: छपे गवाहों का OCR मापा गया

- मालिक ने Downloads वाली client-फ़ाइल रखने को कहा ("रहने दो"); उसे छुआ नहीं गया।
- **नया औज़ार (PR #38):** `.github/workflows/ocr-witness.yml` (Tesseract 5, tessdata_best के `san` और `script/Devanagari`) + `tools/witness/ocr_collate.py` (हर मंत्र पर `contained` / `coverage`)। OCR-पाठ repo या artifact में नहीं जाता; केवल रिपोर्ट।
- **नया गवाह:** `ia-roer-1850` (Bibliotheca Indica खंड 8; संपादक Röer की मृत्यु 1866, दो स्रोत) → `LicenseRef-PD-India-US`, उपयोग अभी `compare`, G1 बाक़ी। निर्णयसागर 1925 के संपादक (वासुदेव लक्ष्मण शास्त्री पणशीकर) की मृत्यु-तिथि नहीं मिली: LoC authority n82118487 में तिथि नहीं, Wikidata/VIAF में प्रविष्टि नहीं, web-खोज बेनतीजा।
- **माप (रिपोर्टें `audit/witness/isha_ocr_*.json`; संदर्भ-गवाह = विकिस्रोत 'ईशोपनिषत्'):**

| छपा गवाह | पन्ने | मॉडल | coverage न्यून/औसत/अधिक | strong ≥0.95 | partial ≥0.80 | weak |
|---|---|---|---|---|---|---|
| निर्णयसागर 1925 (पृ. 1; हाथ की लिखावट वाली प्रति) | 1 | script/Devanagari | 0.33 / 0.83 / 1.00 | 3 | 10 | 5 |
| निर्णयसागर 1925 | 1 | san | 0.38 / 0.72 / 0.95 | 0 | 5 | 13 |
| Röer 1850 (leaf 9–40) | 32 | script/Devanagari | 0.47 / 0.74 / 0.96 | 1 | 6 | 11 |
| Röer 1850 | 32 | san | 0.47 / 0.70 / 0.94 | 0 | 5 | 13 |

  - run: 43869298989 (निर्णयसागर), 43869307008 (Röer)। किसी भी मंत्र पर `key_contained` नहीं आया।
  - निर्णयसागर में मंत्र 17–18 अगले पन्ने (leaf n14) पर जाते हैं; वह पन्ना इस run में नहीं था, इसलिए मंत्र 18 का 0.33 OCR की नहीं, दायरे की कमी है। Röer में ईश leaf 40 के बाद भी चल सकता है; यह जाँचा नहीं गया।
  - `script/Devanagari` मॉडल दोनों जगह `san` से बेहतर रहा।
- **निष्कर्ष [हमारा माप]:** पुराने छपे संस्करणों पर Tesseract अकेले "≥2 गवाह कुंजी पर सहमत" वाली शर्त पूरी नहीं कर सकता; वह केवल सहायक प्रमाण देता है (पन्ने पर लगभग वही पाठ है)। यह P2 का एक असली नतीजा है: text-lock की बाधा OCR है, मिलान नहीं।
- **आगे के रास्ते (अभी कोई नहीं चुना गया):** (क) इसी संस्करण की बिना-लिखावट वाली प्रति; (ख) चित्र-सफ़ाई (grayscale, upscale, binarise) और `--psm 6`; (ग) दूसरा OCR-engine (vision-LLM, जैसे Gemini Flash-Lite) प्रयोग के रूप में। (ग) में जोखिम: प्रसिद्ध पाठ मॉडल को याद होता है, इसलिए वह छपे पाठभेद को "सुधार" सकता है; उसे अकेला स्वतंत्र गवाह न मानें। lock-नियम बदलना हो तो मालिक का फ़ैसला और `DECISIONS.md`।
- **G1-batch मालिक के सामने रखना बाक़ी:** `witnesses/` के 6 रिकॉर्ड (`sa-ws-isha`, `sa-ws-vsm40`, `ia-anantacharya-1896`, `ia-hiriyanna-1911`, `ia-nsp-108-1925`, `ia-roer-1850`), सब `pending_owner`।

### session 1, turn 28 (2026-11-16, claude-fable-5-2) — दिशा बदली: स्रोत पहले

- **मालिक का निर्देश:** "पहले स्रोत खोजो... हर टेक्स्ट का एक मास्टर स्रोत... भारतीय लेखक/प्रकाशन, पुरानी प्रतियाँ जो इंटरनेट पर हैं; किसने लिखा, किसने संकलन किया, किसने प्रकाशित किया, यह देखकर फ़ैसला लो। अभी ये सब [OCR आदि] मत करो।" → OCR-सुधार, lock और ड्राफ़्ट रोके गए। G1-batch की स्वीकृति नहीं ली गई।
- **Claude ने मालिक को बताया:** ज़्यादातर ग्रंथों का कोई एक "प्रमाणित मूल" नहीं होता; जो होता है वे संस्करण हैं। इसलिए हर ग्रंथ का घोषित आधार-संस्करण चुना जाएगा (मास्टर योजना §3.1)।
- **नया:** `docs/SOURCE_SELECTION_hi.md` (कसौटी का मसौदा: 7 कसौटियाँ, जाँच के 4 स्तर) और `catalog/_base_editions.json` (खेप 1: ईश के 9 और गीता के 3 उम्मीदवार; हर एक पर संपादक, प्रकाशक, वर्ष, शाखा, इंटरनेट-प्रति, जाँच का स्तर, सर्वाधिकार, चिंताएँ)। किसी का आधार तय नहीं; `proposal.status = pending_owner`।
- **इस खेप में क्या सच में देखा गया:** मुखपृष्ठ केवल निर्णयसागर 1925 का। बाक़ी उम्मीदवार archive.org के रिकॉर्ड या upload-शीर्षक से हैं (`catalogue_metadata` / `uploader_metadata`); उनके मुखपृष्ठ देखना अगला काम है। archive.org के खोज-नतीजों में मिला: वाणी विलास 1910 खंड 4 (`wg1059`), काण्व संहिता 1915 (`in.ernet.dli.2015.405425`), काण्व संहिता 1956 (सातवलेकर), काण्व + सायण (सम्पूर्णानन्द), शुक्ल यजुर्वेद संहिता 1929 (निर्णयसागर), Weber 1852, आनन्दाश्रम गीता 1909, निर्णयसागर गीता 1936, BORI भीष्मपर्व।
- **ध्यान:** ईशावास्य शुक्ल यजुर्वेद संहिता का 40वाँ अध्याय है, इसलिए उसके स्रोत दो तरह के हैं (उपनिषद्-संस्करण और संहिता-संस्करण); सूची में दोनों हैं।
- **खोज की सीख:** archive.org की advancedsearch में देवनागरी शब्द या बहुत लंबे OR-समूह बेतुके नतीजे देते हैं; छोटे रोमन-शब्द वाले query चलाएँ। R-जाँचें `catalog/*.json` में "सत्यापित/verified" जैसे शब्द रोकती हैं; `_` से शुरू होने वाली फ़ाइलें card-schema से बाहर हैं।

### session 1, turn 29 (2026-11-16, claude-fable-5-2) — पूरी कड़ी बनी और Foreman से स्वचालित चली

- **मालिक का निर्देश:** "पहले ये सब एक बार बना लो... जो तुमको verified स्रोत लगता है, भारतीय लेखक होना चाहिए... पूरे agent-स्वार्म की end-to-end pipeline testing कर लो, और यह automation पर आ जाए। फिर तय करेंगे कि स्रोत क्या रखेंगे।"
- **अस्थायी आधार:** निर्णयसागर 1925 (`ia-nsp-108-1925`; संपादक वासुदेव शास्त्री पणशीकर)। उसका OCR साफ़ नहीं, इसलिए मशीन-पठनीय पाठ का वाहक विकिस्रोत का e-text (`sa-ws-isha`, CC BY-SA) है; छपे पन्ने से उसका मेल औसत 0.83 (Tesseract)। LLM से संस्कृत नहीं पढ़वाई गई (रेलिंग 3)।
- **बना (PR #41, #43):** `tools/pilot/run_e2e.py` (कड़ी), `tools/pilot/llm.py` (Google AI Studio + Groq), `tools/pilot/ci_run.sh` (CI + डेटा-PR), workflows `pilot-e2e` (हाथ से) और `foreman-enqueue` (Foreman से), `foreman-job` में step `pilot_e2e`, Foreman में `/admin/enqueue` (अनुमत: `noop`, `pilot_e2e`)। Foreman का तीसरा deploy: run 43875221685 (log में कोई ईमेल नहीं)।
- **कड़ी के क़दम:** गवाह से पाठ → ID/गिनती → Draft A (Groq qwen3.8-27b, alibaba) और Draft B (gemini-3.5-flash-lite, google) → जज 1 (gpt-oss-120b, openai) → असहमति पर Draft C (gpt-oss-120b) और जज 2 (ड्राफ़्टों से अलग परिवार: google या alibaba) → D2/D3/D6/D7/D8 → बैज C/D → परतों का पेड़ (workspace में) → R-जाँचें → रिपोर्ट → डेटा-PR (auto-merge)।
- **नतीजे [हमारा माप; एक छोटा ग्रंथ, 18 मंत्र]:**

| run | रास्ता | समय | API-calls | 429 | पहले दौर की सहमति | C / D | डेटा-PR |
|---|---|---|---|---|---|---|---|
| 43874308820 (v0.1) | हाथ से | 142 s | 19 | 3 | 5/18 (28%) | 10 / 8 | #42, अपने-आप merge |
| 43875372883 (v0.2) | Foreman | 159 s | 19 | 7 | 6/18 (33%) | 10 / 8 | #44, अपने-आप merge |

  - Foreman वाले run में: enqueue → dispatch → Actions → callback `pr:44`; बही में job `done`, 166 s।
  - बने पेड़ पर R-जाँचें: R2 (lock) और R6 (लाइसेंस) लाल, बाक़ी 13 हरी। ये दोनों लाल **अपेक्षित** हैं: स्रोत तय नहीं, पाठ lock नहीं। इसलिए पेड़ repo में नहीं गया; repo में केवल `audit/pilot/isha_e2e.json` (अनुवाद के मसौदे, संस्कृत का केवल hash) और `state/pilot_metrics.json`।
- **pilot ने जो कमज़ोरियाँ दिखाईं (छिपाएँ नहीं):**
  1. पहले दौर की सहमति 28–33% है; go-सीमा 60%। योजना के अनुसार इसका अर्थ: "हमेशा 3 ड्राफ़्ट"।
  2. जज अस्थिर है: D वाले मंत्र run 1 में 1, 2, 8, 10, 12, 13, 17, 18 थे और run 2 में 4, 8, 9, 10, 12, 13, 16, 18। दोनों में साझा: 8, 10, 12, 13, 18।
  3. gemini-3.5-flash-lite ने मंत्र 1 का ग़लत अनुवाद दिया (जजों ने पकड़ा)। थोक-ड्राफ़्टर के रूप में यह मॉडल कमज़ोर हो सकता है।
  4. Groq पर केवल दो उपयोगी परिवार हैं (`openai/gpt-oss-120b`, `gpt-oss-20b`, `qwen/qwen3.8-27b`; बाक़ी: `allam-2-7b`, दो आवाज़-मॉडल)। "चौथे परिवार का जज" अभी उपलब्ध नहीं; जज घुमाकर चुना जाता है।
  5. Groq की TPM-सीमा से 429 बार-बार (एक run में qwen पर 5 बार, 90 s इंतज़ार)।
  6. योजना का Draft A (Kaggle पर fine-tuned Qwen) और D1/D4/D5/D9/D10/D12 अभी नहीं हैं; PD संदर्भ-अनुवाद जज को नहीं दिया गया।
- **v0.2 का नियम-बदलाव:** दूसरे दौर में अगर दूसरा जज भी पहले जज का चुना ड्राफ़्ट ही चुने और ठीक कहे, तो झंडा नहीं (हारे ड्राफ़्ट की ग़लती से D नहीं)।
- **"स्वचालित" का सही अर्थ अभी:** एक बटन (`foreman-enqueue`) से लेकर merge तक कोई हाथ नहीं लगता। पर Foreman अभी अपने-आप अगला ग्रंथ नहीं चुनता (ग्रंथ-स्तर की state-machine P3 में)।
- **न करें:** `texts/isha/` में कुछ न लिखें जब तक स्रोत तय और lock न हो; R2/R6 को "ठीक" करने के लिए लाइसेंस या lock न गढ़ें।

### session 1, turn 30 (2026-11-16, claude-fable-5-2) — कड़ी v0.3: कमज़ोरियाँ ठीक करने का पहला दौर

- **मालिक का चुनाव:** "कड़ी ठीक करो" (pilot की कमज़ोरियाँ)।
- **v0.2 में मिला bug:** दोनों पुराने runs में Draft A (Groq qwen) का बीच का टुकड़ा (मंत्र 7–12) Groq के JSON-mode की 400-त्रुटि से गिरता था और चुपचाप छूट जाता था। इसलिए वे छह मंत्र बिना पहले जज के cascade में जाते थे। पुरानी "28–33% सहमति" इसी से कम दिखी: जिन 12 जोड़ों पर जज बैठा, उनमें 5/12 (42%) और 6/12 (50%) सहमत थे।
- **v0.3 में बना (branch `pilot-v03`):**
  1. **चौथा परिवार:** Cloudflare Workers AI provider (`tools/pilot/llm.py`)। मौजूदा `CLOUDFLARE_API_TOKEN` से चलता है (probe run 43897044579)। मुफ़्त स्तर पर Meta Llama, Mistral, gpt-oss, Qwen, Gemma मिले; DeepSeek और Kimi "Workers Free plan पर उपलब्ध नहीं" (403)।
  2. **pacing:** Groq के headers (8,000 tokens/मिनट) और 429-संदेश से सीखी output-सीमा (qwen: 1,000 output-tokens/मिनट) के हिसाब से अनुरोध पहले ही रुकते हैं।
  3. **छूटे टुकड़े:** `ask_items` छूटी ids को छोटे टुकड़ों में दोबारा भेजता है; JSON-mode की 400 पर सादा अनुरोध। अब `draft_missing` और `judge1_missing` माप में अलग दिखते हैं।
  4. **fallback:** हर भूमिका की क्रमबद्ध सूची (`DEFAULT_MODELS`); पहला मॉडल उत्तर न दे तो अगला (`draft_fb`, `judge_fb`)। परिवार-नियम बना रहता है। कभी दूसरी key या खाता नहीं।
  5. **जज:** हर ग़ैर-OK label के लिए प्रमाण-क्षेत्र (बिना प्रमाण का CONTRADICTED → UNSURE); A/B का क्रम id के hash से बदलता है (स्थान-पक्षपात के लिए)।
  6. **स्थिरता-माप:** वही जोड़े उसी जज को उलटे क्रम में, और एक और परिवार के जज को (`judge_stability`)। फ़ैसला इससे नहीं बदलता।
  7. **विफलता:** आधे से ज़्यादा मंत्रों पर जूरी अधूरी हो तो run विफल होता है और डेटा-PR नहीं खुलता (Foreman बाद में दोबारा चलाए)।
  8. **औज़ार:** `tools/pilot/bakeoff.py` (ड्राफ़्टरों की तुलना; `pilot-e2e` में `mode=bakeoff`), `tools/providers/probe.py` (`provider-smoke` में `provider=probe`)। `pilot-e2e` के नए inputs: `mode`, `open_pr`, `draft_a/b/c`, `judges`।
- **branch पर परखने का तरीका (PR के बिना):** `gh workflow run pilot-e2e.yml --ref <branch> -f text_id=isha -f mode=pipeline -f open_pr=no`
- **ड्राफ़्टरों की तुलना [हमारा माप; run 43898284352 का log; run 45 मिनट पर कट गया, artifact नहीं बना; जज भी मॉडल हैं]:**

| ड्राफ़्टर | बने | जज gpt-oss-120b: OK / MINOR / CONTRADICTED / UNSURE | जज mistral-small |
|---|---|---|---|
| Gemma 4 31B (AI Studio) | 18/18, 139 s | 12 / 3 / 3 / 0 | 6 / 10 / 2 / 0 |
| qwen3.8-27b (Groq) | 18/18, 104 s | 9 / 3 / 5 / 1 | — |
| llama-4-scout (Workers AI) | 18/18, 268 s | 10 / 2 / 5 / 1 | — |
| mistral-small-3.1 (Workers AI) | 18/18, 35 s | 10 / 2 / 6 / 0 | — |
| llama-3.3-70b (Workers AI) | 16/18, 83 s | 6 / 2 / 8 / 0 | — |
| gpt-oss-120b (Groq) | 18/18, 67 s | — | 4 / 6 / 8 / 0 |
| gemini-3.5-flash-lite | 0/18 (HTTP 503) | — | — |
| gemini-3.8-flash | 0/18 (HTTP 429, quota) | — | — |

  इसी से Draft A की सूची में Gemma 4 31B पहला रखा गया। यह तुलना पूरी नहीं है: दोबारा चलाकर `audit/pilot/` में रखनी है।
- **v0.3 का असली run [हमारा माप; run 43920792204, branch पर, PR नहीं खोला]:**
  - उस समय Gemma (503, फिर समय-सीमा) और Workers AI (दिन का quota ख़त्म) उत्तर नहीं दे रहे थे। fallback से Draft A = gemini-3.5-flash-lite, Draft B = qwen, जज 1 = gpt-oss-120b, Draft C = gpt-oss-120b, जज 2 = qwen (केवल google-ड्राफ़्ट वाले जोड़ों पर)।
  - पहले दौर की सहमति **9/18 (50%)**, सभी 18 जोड़ों पर जज बैठा। बैज C 10 / D 8। झंडे: JURY_INCOMPLETE 6 (qwen-ड्राफ़्ट वाले जोड़ों के लिए कोई पात्र जज उत्तर नहीं दे रहा था), CONTRADICTED 1, JURY_DISAGREE 1।
  - जज की स्थिरता (वही जज, उलटा क्रम, 18 जोड़े): label 0.889, स्वीकार 0.889, **चुनाव (pick) 0.556**। यानी "ठीक या ग़लत" काफ़ी स्थिर है, पर "कौन बेहतर" क्रम पर निर्भर है। दूसरे परिवार के जज से तुलना नहीं हो सकी (Workers AI बंद)।
  - समय **1,562 s (26 मिनट)**; 59 API-calls, 22 बार 429, pacing में 748 s और 429 के बाद 290 s इंतज़ार। स्थिरता-माप अकेला 441 s।
  - इससे पहले के दो runs (43915053026, 43917316702) में पूरा Google-परिवार 503 दे रहा था; दूसरा run नए नियम से विफल हुआ और कोई PR नहीं बना (यही अपेक्षित व्यवहार है)।
- **जज की गुणवत्ता [निर्माता की अपनी पढ़त; विशेषज्ञ-समीक्षा नहीं]:** gpt-oss-120b ने मंत्र 10 और 13 में "विचचक्षिरे = समझाया" वाले सही ड्राफ़्ट को "उलटा" कहकर ग़लत ड्राफ़्ट ("जिन्होंने नहीं देखा") चुना; मंत्र 18 में "राये = धन के लिए" को "संस्कृत में नहीं" कहा; मंत्र 4 में "अनेजत् = अचल" को ग़लत कहा; मंत्र 1 में "भुञ्जीथाः = पालन करो" (शांकर-पाठ) को CONTRADICTED कहा। इन मंत्रों पर D लगा है, पर कारण संयोग है (जूरी अधूरी थी)। **निष्कर्ष: इस जज के C-बैज पर भरोसा नहीं किया जा सकता।**
- **गति [हमारा माप]:** Groq का मुफ़्त स्तर प्रति मॉडल 8,000 tokens/मिनट और 1,000 अनुरोध/दिन देता है (headers से); gpt-oss हर अनुरोध में ~1,700 reasoning-tokens ख़र्च करता है। 18 मंत्र = 26 मिनट (स्थिरता-माप के बिना लगभग 19)। योजना का ~7,000 श्लोक/दिन इस रास्ते से नहीं निकलता।
- **provider की घटनाएँ (16 नवंबर):** AI Studio पर Gemma और Flash-Lite घंटों 503 "high demand" देते रहे; Flash-वर्ग का मुफ़्त quota ख़त्म मिला। Workers AI के 10,000 neurons/दिन तुलना के runs में ख़त्म हो गए (00:00 UTC पर लौटते हैं); nemotron-3-120b पर अनुरोध अटकते रहे।
- **merge के बाद Foreman से run (main, v0.3) [हमारा माप; enqueue run 43926253521 → foreman-job run 43926279410]:** **विफल, और यही सही व्यवहार था।** Gemma 4 31B लौट आया (18/18, 179 s) और qwen ने 18/18 दिए, पर पहले दौर का कोई जज उत्तर नहीं दे सका: Groq पर gpt-oss-120b की **दिन-भर की सीमा (200,000 tokens/दिन)** आज के परीक्षणों में ख़त्म हो चुकी थी, और Workers AI का quota भी। नए नियम से run विफल हुआ, कोई डेटा-PR नहीं बना, callback `failed` गया। v0.3 का Foreman-रास्ता इसलिए अभी हरा नहीं दिखा; quota लौटने पर (Workers AI: 00:00 UTC; Groq: 24 घंटे की खिड़की) `foreman-enqueue` दोबारा चलाना है।
- **इससे निकला काम:** Foreman को "quota ख़त्म, इतने बजे लौटेगा" का संकेत मिलना चाहिए (अवस्था `waiting_reset` पहले से है), ताकि वह 10 मिनट बाद बेकार दोबारा न चलाए। अभी `llm.py` दिन-भर की सीमा वाली 429 पर तुरंत रुकता है (पहले 9 मिनट इंतज़ार करता था)।
- **हटाए गए runs:** 43915053026 और 43920792204 के log और artifact GitHub से हटा दिए गए, क्योंकि Groq की 429-त्रुटि के संदेश में खाते का संगठन-ID छपा था। उनके माप (ID हटाकर) `state/pilot_metrics.json` और `audit/pilot/isha_e2e.json` में हैं; `llm.py` का `scrub()` अब यह ID अपने-आप हटाता है।
- **जानबूझकर नहीं किया:** Foreman का नया deploy नहीं (उसकी सूची का `promptHash: "pilot-e2e-0.1"` job-अनुबंध का नाम है; कड़ी का version नतीजे के `pipeline_version` में है)। Hiriyanna 1911 का पाठ जज को नहीं दिया (G1 बाक़ी; OCR में मंत्र और भाष्य मिले हुए हैं, parser चाहिए)। `texts/` ख़ाली है।
- **खुला जोखिम:** pilot का क़दम अब `CLOUDFLARE_API_TOKEN` पढ़ता है, जो deploy वाला चौड़ा token है। Workers AI के लिए अलग, केवल-पढ़ने वाला token बेहतर है (मालिक का क़दम)।
- **न करें:** `texts/isha/` में कुछ न लिखें जब तक स्रोत तय और lock न हो; R2/R6 को "ठीक" करने के लिए लाइसेंस या lock न गढ़ें; तुलना (bake-off) एक दिन में दो बार न चलाएँ (Workers AI का quota ख़त्म हो जाता है)।

### session 1, turn 31 (2026-11-17, claude-fable-5-2) — जज-परीक्षा, कड़ी v0.4, और सुबह का स्वचालित run

- **मालिक:** "हाँ, चलाओ" (quota लौटने पर जजों की तुलना और Foreman-run)।
- **turn 30 के बाद:** Foreman ने विफल job को अपने-आप दो बार और चलाया (runs 43929775854, 43934148900); quota ख़त्म होने से वे भी विफल हुए। कोई डेटा-PR नहीं बना।
- **नया औज़ार: जज-परीक्षा** (`tools/pilot/judge_test.py`; `pilot-e2e` में `mode=judgetest`)। repo के AI-मसौदों में नियम से ठीक एक ग़लती डाली जाती है (संख्या, निषेध, नाम, विलोम) और जज को असली कड़ी वाला ही prompt मिलता है। उत्तर हमें पता है, इसलिए पकड़-दर सीधी नापी जाती है। यह मोटी ग़लतियाँ नापता है, बारीक अर्थ नहीं।
- **पहला नतीजा [हमारा माप; pilot-e2e run 43935550508, branch पर; 18 मंत्र]:**

| जज | बिगड़ी नक़ल पकड़ी | आधार चुना | बिगड़ी नक़ल को ठीक कहा | आधार पर आपत्ति | समय |
|---|---|---|---|---|---|
| Gemini 3.5 Flash-Lite | 17/18 | 18/18 | 1 (ईश 3) | 3 (ईश 10, 13, 18) | 40 s |
| qwen3.8-27b (Groq) | 15/18 | 17/18 | 3 (ईश 3, 15, 16) | 0 | 65 s |
| Gemma 4 31B | उत्तर नहीं (HTTP 503) | — | — | — | — |

  Flash-Lite ने आधार-मसौदे पर ठीक उन्हीं तीन मंत्रों (10, 13, 18) में आपत्ति की जिनमें निर्माता की पढ़त से आधार सचमुच ग़लत है; qwen ने इन्हें ठीक कहा, और gpt-oss-120b ने असली run में इन्हीं पर ग़लत ड्राफ़्ट चुना था। Mistral, Llama और gpt-oss की परीक्षा Workers AI का quota लौटने पर होगी।
- **कड़ी v0.4 (`DEFAULT_MODELS`):** जज = Gemini 3.5 Flash-Lite (फिर Gemma, Mistral, Llama, gpt-oss, qwen); Draft A = Groq qwen (फिर Workers AI Llama 4 Scout); Draft B = Groq gpt-oss-120b (फिर Workers AI gpt-oss-120b); Draft C = Workers AI Mistral Small (फिर Llama 3.3)। यही मास्टर योजना §3.3 की मूल रचना है (जज Flash-Lite)। क़ीमत: Gemma 4 31B अब ड्राफ़्टर नहीं है, क्योंकि जज अपने परिवार का काम नहीं जाँचता।
- **नियम कड़ा हुआ:** "दो जजों ने वही ड्राफ़्ट चुना" वाली छूट अब तभी मिलती है जब दूसरा जज सचमुच दूसरे परिवार का हो। वही जज दोबारा वही कहे तो वह स्वतंत्र पुष्टि नहीं है; ऐसे मंत्र पर D लगता है।
- **v0.4 की स्थिति:** mock में हरा; **असली मॉडलों पर अभी नहीं चला** (Groq gpt-oss और Workers AI के दिन के quota ख़त्म थे)।
- **सुबह का स्वचालित run:** `.github/workflows/pilot-scheduled.yml`, cron `20 0 17 11 *` (17 नवंबर, 00:20 UTC = 05:50 IST; GitHub का schedule कुछ मिनट देर से भी चल सकता है)। क्रम: जज-परीक्षा (छह जज) → डेटा-PR `audit/pilot/judge_test_isha.json` → `foreman-enqueue` (पूरी कड़ी) → डेटा-PR। laptop की ज़रूरत नहीं। **चल जाने के बाद `schedule` वाली पंक्तियाँ हटानी हैं** (वरना अगले साल इसी तिथि पर फिर चलेगा); `workflow_dispatch` रहेगा।
- **जोखिम:** Groq gpt-oss की दिन-भर की सीमा 24 घंटे की खिड़की पर है; 00:20 UTC तक वह आंशिक ही लौटेगी। Draft B के लिए वह काफ़ी होनी चाहिए (≈7,000 tokens), न हो तो Workers AI वाला gpt-oss लिया जाएगा। Google पर 503 रहे तो जज Mistral पर गिरेगा।
- **न करें:** वही जो turn 30 में; और `pilot-scheduled` को एक ही दिन में बार-बार हाथ से न चलाएँ (quota)।
