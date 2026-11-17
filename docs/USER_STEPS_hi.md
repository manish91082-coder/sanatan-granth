# आपके क़दम (P0), एक-एक करके

हर login आप ख़ुद करेंगे। कहीं भी **card, ID या phone-verification** की स्क्रीन आए, तो वहीं रुकें और Claude को बताएँ। कोई key, token या password chat में न चिपकाएँ; वे सीधे GitHub/Cloudflare/Kaggle के secret-खाने में जाते हैं।

## 0.2 · Claude: usage credits और Fable (10 मिनट)

1. claude.ai → Settings → Usage खोलें। देखें कि **usage credits (extra usage) बंद** हैं।
2. Claude Code के model picker में देखें कि **Fable 5.2** के आगे "Requires usage credits" लिखा है या नहीं।
3. Claude को दोनों उत्तर बताएँ ("credits बंद हैं; Fable पर credits नहीं माँगता" जैसा)। Claude उन्हें `policy/quotas.md` में दर्ज करेगा।

## 0.3 · Google AI Studio (~1 घंटा)

1. aistudio.google.com पर अपने Google खाते से जाएँ।
2. **एक ही project, एक ही API key** रखें। पहले से key हो तो वही रहने दें; दूसरी न बनाएँ।
3. Dashboard → Rate limits में इन मॉडलों की **RPD और RPM** पढ़कर Claude को बताएँ: Flash-Lite, 3.8 Flash, 3.6 Flash, 4 Hydrogen।
4. key को GitHub में डालें: repo → Settings → Secrets and variables → Actions → New repository secret → नाम `GEMINI_API_KEY`।
5. phone या ID माँगे तो रुकें।

## 0.4 · Kaggle (20 मिनट)

1. kaggle.com → Settings → API → "Create New Token"।
2. Settings के quota-खाने में पढ़ें: साप्ताहिक **GPU घंटे**, **TPU घंटे**, और **reset का दिन**। Claude को बताएँ।
3. GitHub secrets में डालें: `KAGGLE_USERNAME` और `KAGGLE_KEY`।
4. वही Kaggle खाता उपयोग करें जो फ़िल्म के लिए है (एक कंपनी, एक खाता)। कोई नया phone/ID-verification माँगे तो रुकें।

## 0.5 · Groq और Cloudflare (30 मिनट)

1. console.groq.com पर मुफ़्त key बनाएँ → GitHub secret `GROQ_API_KEY`। Limits पन्ने से gpt-oss-120b की RPM/RPD/TPM/TPD Claude को बताएँ। card माँगे तो रुकें।
2. Cloudflare dashboard → My Profile → API Tokens → "Create Token" → template **Edit Cloudflare Workers** (इसमें D1 की अनुमति भी जोड़ें: Account → D1 → Edit)। → GitHub secret `CLOUDFLARE_API_TOKEN`।
3. Cloudflare dashboard के दाएँ कोने से **Account ID** → GitHub secret `CLOUDFLARE_ACCOUNT_ID`।

## 0.6 · Google Cloud: Drive की अपनी चाबी (30 मिनट)

1. console.cloud.google.com → नया project (या AI Studio वाला ही project चुनें)। **billing न जोड़ें।** इस project में कोई नई Gemini key न बनाएँ।
2. APIs & Services → Library → **Google Drive API** → Enable।
3. OAuth consent screen → External → app का नाम `sanatan-granth-drive` → scope में केवल **`.../auth/drive.file`** → Publishing status को **"In production"** करें (Testing में token 7 दिन में मर जाता है)।
4. Credentials → Create credentials → OAuth client ID → **Desktop app**। Client ID और secret अपने पास रखें (chat में नहीं)।
5. billing माँगे तो रुकें।

## 0.7 · rclone remote `granth:` (30 मिनट, Claude साथ रहेगा)

लैपटॉप के terminal में, अपने client ID/secret के साथ (Claude आदेश देगा, मान आप भरेंगे):

1. `rclone config create granth drive scope=drive.file client_id=<आपका> client_secret=<आपका>` → browser में login।
2. Claude `Sanatan_Library/` का tree बनाएगा और जाँचेगा कि `gdrive:` (फ़िल्म) अछूता है।
3. `rclone config show granth` का token-खंड Kaggle → Settings → Secrets में `RCLONE_GRANTH_CONF` नाम से डालें।

## 0.11 · Foreman deploy (Claude code दे चुका है)

1. GitHub → Settings → Developer settings → Fine-grained tokens → नया token: केवल `sanatan-granth` repo, अनुमति **Contents: Read and write**। यह Cloudflare में जाएगा (`GITHUB_DISPATCH_TOKEN`), ताकि Foreman Actions को जगा सके।
2. repo → Actions → `foreman-deploy` → Run workflow।
3. healthchecks.io और uptimerobot.com के मुफ़्त खाते (card माँगें तो छोड़ दें; GitHub सूचना काफ़ी है)।

### Foreman का दोबारा deploy (जब भी `foreman/` का code बदले)

17 नवंबर 2026 को Foreman में स्वार्म की घड़ी जुड़ी (हर 20 मिनट पर संचालक)। नया code तभी चलेगा जब आप एक बार यह करें:

1. repo → Actions → `foreman-deploy` → Run workflow (`create_d1` को `no` ही रहने दें)।
2. हरा होने पर Foreman का `/status` पन्ना खोलें: कुछ मिनट में "हाल की घटनाएँ" में `conduct` दिखेगा।

### SambaNova की key (वैकल्पिक; एक और स्वतंत्र मॉडल-स्रोत)

स्वार्म इसके बिना भी चलता है। यह इसलिए है कि दो स्रोत एक साथ बंद हों तब भी काम न रुके।

1. cloud.sambanova.ai पर खाता बनाएँ। **कार्ड, फ़ोन या पहचान माँगे तो वहीं रुकें** और Claude को बताएँ। भुगतान-तरीका कभी न जोड़ें (जोड़ते ही मुफ़्त स्तर हट जाता है)।
2. API keys के पन्ने पर एक key बनाएँ (एक ही)।
3. अपने terminal में: `gh secret set SAMBANOVA_API_KEY --repo manish91082-coder/sanatan-granth` और पूछे जाने पर key चिपकाएँ। key chat में न चिपकाएँ।
4. Claude को बताएँ; वह `provider-smoke` (sambanova) चलाकर मॉडल नापेगा।

## 0.12 · सूचना की जाँच (15 मिनट)

phone में GitHub mobile app → इस repo की notifications चालू। Claude एक परीक्षण-issue खोलेगा; सूचना आई या नहीं, बताएँ।

## 0.13 · साप्ताहिक audit task (~1 घंटा)

claude.ai/code → Scheduled tasks → नया task: केवल `sanatan-granth` repo, नेटवर्क **Limited**, सारे connectors हटाएँ, एक मॉडल चुनें, cron `37 3 * * 0`। Prompt `policy/audit_prompt.md` से। पहले **Run now**, फिर transcript और usage-% Claude को बताएँ।
