# quotas: console में देखी गई असली सीमाएँ

यहाँ केवल वही लिखा जाता है जो मालिक ने अपने console/dashboard में **देखा** हो, तिथि के साथ। अनुमान यहाँ नहीं आते। हर महीने के पहले रविवार को दोबारा देखें।

| मंच | क्या देखा | मान | देखने की तिथि | किसने दर्ज किया |
|---|---|---|---|---|
| Claude Max | usage credits बंद? | **हाँ, बंद** | 2026-11-14 | मालिक ने देखकर बताया; Claude ने दर्ज किया |
| Claude Max | `/model` picker में Fable 5.2 पर "Requires usage credits"? | **नहीं दिखता** (Fable उपयोग-योग्य) | 2026-11-14 | मालिक ने देखकर बताया; Claude ने दर्ज किया |
| Google AI Studio | Gemini 3.5 Flash Lite: RPM / TPM / RPD | **15 / 250K / 500** | 2026-11-14 | Claude ने मालिक के logged-in AI Studio पन्ने (Rate limit, Free tier) से पढ़ा |
| Google AI Studio | Gemini 3.1 Flash Lite: RPM / TPM / RPD | **15 / 250K / 500** | 2026-11-14 | Claude ने मालिक के logged-in AI Studio पन्ने (Rate limit, Free tier) से पढ़ा |
| Google AI Studio | Gemini 2.5 Flash Lite: RPM / TPM / RPD | 10 / 250K / 20 | 2026-11-14 | Claude ने मालिक के logged-in AI Studio पन्ने (Rate limit, Free tier) से पढ़ा |
| Google AI Studio | Gemini 3.8 Flash: RPM / TPM / RPD | 5 / 250K / **20** | 2026-11-14 | Claude ने मालिक के logged-in AI Studio पन्ने (Rate limit, Free tier) से पढ़ा |
| Google AI Studio | Gemini 3.6 Flash: RPM / TPM / RPD | 5 / 250K / **20** | 2026-11-14 | Claude ने मालिक के logged-in AI Studio पन्ने (Rate limit, Free tier) से पढ़ा |
| Google AI Studio | Gemini 4 Hydrogen: RPM / TPM / RPD | 5 / 250K / **20** | 2026-11-14 | Claude ने मालिक के logged-in AI Studio पन्ने (Rate limit, Free tier) से पढ़ा |
| Google AI Studio | Gemini 3 Flash, 2.5 Flash: RPM / TPM / RPD | 5 / 250K / 20 | 2026-11-14 | Claude ने मालिक के logged-in AI Studio पन्ने (Rate limit, Free tier) से पढ़ा |
| Google AI Studio | Gemini 4 Argon, 4 Carbon, 3.1 Pro, 2.5 Pro | 0 / 0 / 0 (मुफ़्त स्तर पर उपलब्ध नहीं) | 2026-11-14 | Claude ने मालिक के logged-in AI Studio पन्ने (Rate limit, Free tier) से पढ़ा |
| Google AI Studio | Gemma 4 26B और 31B: RPM / TPM / RPD | 30 / **16K** / **14.4K** | 2026-11-14 | Claude ने मालिक के logged-in AI Studio पन्ने (Rate limit, Free tier) से पढ़ा |
| Google AI Studio | Gemini Embedding 1, 2: RPM / TPM / RPD | 100 / 30K / 1K | 2026-11-14 | Claude ने मालिक के logged-in AI Studio पन्ने (Rate limit, Free tier) से पढ़ा |
| Google AI Studio | मुफ़्त Batch API चला? | **नहीं।** `gemini-3.5-flash-lite:batchGenerateContent` ने HTTP 400 "Precondition check failed." लौटाया। कारण पक्का नहीं (मुफ़्त स्तर पर Batch बंद होना सबसे संभावित; अनुरोध का रूप भी कारण हो सकता है)। क्षमता-गणित में Batch नहीं गिना जाएगा। | 2026-11-14 | `provider-smoke` run 43623513779 |
| Google AI Studio | key GitHub Actions से चली? | **हाँ।** `gemini-3.5-flash-lite`: HTTP 200, 0.77 s, strict JSON parse हुआ, दोनों ID ठीक लौटे; 50 prompt + 102 output tokens। models की सूची में 49 मॉडल generateContent देते हैं; `gemma-4-26b-a4b-it` और `gemma-4-31b-it` भी। | 2026-11-14 | `provider-smoke` run 43623513779 |
| Google AI Studio | कितने projects और keys? | **3 projects, 1 key।** Projects: "Default Gemini Project" (1 key; मालिक के दूसरे काम में उपयोग), "Gemini Project GAG" (कोई key नहीं), "My First Project" (कोई key नहीं)। सब Free tier, billing नहीं जुड़ा। | 2026-11-14 | Claude ने मालिक के logged-in AI Studio (Projects और API Keys पन्ने) से पढ़ा; कोई key या ID दर्ज नहीं |
| Kaggle | साप्ताहिक GPU घंटे | (बाक़ी: क़दम 0.4) | | |
| Kaggle | साप्ताहिक TPU घंटे | (बाक़ी: क़दम 0.4) | | |
| Kaggle | reset का दिन | (बाक़ी: क़दम 0.4) | | |
| Kaggle | T4×2 दोगुना गिनता है? | (बाक़ी: क़दम 0.4) | | |
| Groq | मुफ़्त स्तर पर दिखे मॉडल | `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`, `allam-2-7b`, दो आवाज़-मॉडल। चौथा पाठ-परिवार (जैसे Llama) नहीं दिखा। | 2026-11-16 | pilot run 43875372883 (`state/pilot_metrics.json`) |
| Groq | 429 का व्यवहार (console की सीमाएँ अब भी देखनी बाक़ी) | 18 मंत्रों के एक run में 7 बार HTTP 429 (qwen पर 5, 90 s इंतज़ार); 6 मंत्र/अनुरोध पर भी TPM-सीमा लगती है | 2026-11-16 | pilot run 43875372883 |
| Groq | API के rate-limit headers (console नहीं): `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b` | हर एक पर **1,000 अनुरोध/दिन, 8,000 tokens/मिनट** | 2026-11-16 | `provider-smoke` (probe) run 43897044579 |
| Groq | `openai/gpt-oss-120b` की दिन-भर की सीमा (429 के संदेश से) | **200,000 tokens/दिन**; 16 नवंबर को चार pilot-runs और एक तुलना में ख़त्म हो गई (एक pilot-run ≈ 60,000–95,000 tokens, ज़्यादातर reasoning) | 2026-11-16 | foreman-job run 43926279410 |
| Groq | `qwen/qwen3.8-27b` की output-सीमा (429 के संदेश से) | **1,000 output-tokens/मिनट** (OTPM) | 2026-11-16 | pilot run 43915053026 |
| Cloudflare | Workers AI: मौजूदा token से चला? मुफ़्त स्तर के मॉडल | **हाँ।** Llama 3.3 70B, Llama 4 Scout, Mistral Small 3.1, gpt-oss-120b/20b, qwen3.8-27b, Gemma 4 26B आदि चले; DeepSeek और Kimi पर 403 "not available on the Workers Free plan" | 2026-11-16 | `provider-smoke` (probe) run 43897044579 |
| Cloudflare | Workers AI neurons/दिन (त्रुटि-संदेश से) | **10,000/दिन**; 16 नवंबर को तुलना के runs में ख़त्म हो गए (HTTP 429 "used up your daily free allocation") | 2026-11-16 | pilot run 43915053026 |
| Cloudflare | neurons का ख़र्च (छोटे परीक्षण-अनुरोध) | mistral-small 144 tokens = 5.9; gpt-oss-120b 533 tokens = 31.5; qwen3.8-27b 535 tokens = 121.9; llama-4-scout 102 tokens = 3.6 | 2026-11-16 | `provider-smoke` (probe) run 43897044579 |
| Cloudflare | Workers AI का quota कब लौटता है | **नहीं पता।** 17 नवंबर को 05:45–06:10 UTC पर भी HTTP 429 "used up your daily free allocation" मिला (16 नवंबर की शाम, UTC, को ख़त्म हुआ था)। "00:00 UTC पर लौटता है" हमारा माप नहीं है | 2026-11-17 | pilot-scheduled run 44026092918; foreman-job run 44028350640 |
| Cloudflare | Workers AI का उपयोग इस परियोजना में | **बंद (17 नवंबर 2026 से)।** neurons पूरे खाते के साझा हैं और वही खाता मालिक के दूसरे काम में लगा है | 2026-11-17 | मालिक का निर्देश; `swarm/DECISIONS.md` |
| OpenRouter | मुफ़्त मॉडलों (`:free`) की सीमा, बिना credit ख़रीदे | **20 अनुरोध/मिनट, 50 अनुरोध/दिन** (UTC दिन); ज़्यादा keys या खाते बनाने से सीमा नहीं बढ़ती | 2026-11-17 | openrouter.ai/docs/api-reference/limits (हमारा माप नहीं; key आने पर `provider-smoke` का probe नापेगा) |
| OpenRouter | मुफ़्त पाठ-मॉडल (सार्वजनिक सूची) | 14, जैसे `nvidia/nemotron-3-ultra-550b-a55b:free`, `nvidia/nemotron-3.5-super-vl:free`, `baidu/ernie-5.5-flash-preview:free`, `inclusionai/ling-3.2-flash:free`, `google/gemma-4-31b-it:free`। Mistral या Meta का कोई मुफ़्त मॉडल नहीं दिखा | 2026-11-17 | `tools/providers/probe.py` (बिना key, laptop से; सूची सार्वजनिक है) |
| GitHub Models | उपलब्ध? | **नहीं।** 30 जुलाई 2026 को पूरी तरह बंद | 2026-11-17 | docs.github.com/en/github-models |
| Cerebras | मुफ़्त स्तर | भुगतान-तरीका जोड़ने पर $5 का 30 दिन का credit; अपने-आप लौटने वाला मुफ़्त स्तर नहीं। नियम के कारण नहीं लिया | 2026-11-17 | inference-docs.cerebras.ai (खोज-नतीजे से; पन्ना ख़ुद नहीं खोला) |
| GitHub Actions | `schedule` कितनी देर से चलता है (इस repo में) | `daily-audit` (cron 23:30 UTC): 3 घंटे 23 मिनट, 3 घंटे 24 मिनट, 5 घंटे 38 मिनट देर से। एक बार का cron (`20 0 17 11 *`) 5 घंटे 20 मिनट बाद भी नहीं चला था, तब हटाया गया | 2026-11-17 | daily-audit runs 43669817479, 43794947415, 44021997957 |
| Google AI Studio | 16 नवंबर की उपलब्धता | Gemma 4 31B/26B और Gemini 3.5 Flash-Lite पर घंटों HTTP 503 "high demand"; Gemini 3.8 Flash पर HTTP 429 (quota ख़त्म) | 2026-11-16 | pilot runs 43898284352, 43915053026, 43917316702 |
| Cloudflare | D1 और DO की Free सीमाएँ console में | (बाक़ी: क़दम 0.11) | | |
| Cloudflare | Agent DO पर CPU-सीमा: 10 ms या 30 s? | (बाक़ी: क़दम 0.11, परीक्षण से) | | |

## नियम

- किसी सीमा-त्रुटि पर अपने-आप upgrade नहीं। billing, upgrade, card या phone की कोई स्क्रीन दिखे तो रुकें।
- नई key, नया project या दूसरा खाता कभी नहीं।

## पढ़े गए आँकड़ों का अर्थ (14 नवंबर 2026) [हमारी गणना]

- **Flash वर्ग (3.8, 3.6, 4 Hydrogen): 20 अनुरोध/दिन।** यह मास्टर योजना §10.1 का बताया जोखिम है ("Flash ~20")। 30 श्लोक/अनुरोध पर भी एक Flash मॉडल ~600 श्लोक/दिन से ज़्यादा नहीं दे सकता, इसलिए Flash थोक-ड्राफ़्टर नहीं हो सकता; उसे केवल कठिन श्लोकों या tie-break के लिए रखें।
- **Flash-Lite (3.5 और 3.1): 500 अनुरोध/दिन प्रति मॉडल।** pilot की go-सीमा "Gemini RPD ≥ 500" ठीक किनारे पर पूरी होती है। 30 श्लोक/अनुरोध पर एक मॉडल ~15,000 श्लोक/दिन की ऊपरी सीमा देता है; असली बाधा RPM (15) और TPM (250K) होंगे।
- **Gemma 4 (26B, 31B): 14,400 अनुरोध/दिन, पर केवल 16K tokens/मिनट।** TPM के कारण छोटे batch (5–7 श्लोक) ही चलेंगे। Gemma Google-परिवार है, इसलिए जूरी में वह Gemini के साथ एक ही परिवार गिना जाएगा (अलग परिवार का जज नहीं बन सकता)।
- Pro-वर्ग मुफ़्त स्तर पर नहीं है।
- ये सीमाएँ प्रति project हैं। दूसरा project या दूसरी key बनाकर इन्हें बढ़ाना वर्जित है।
- क्षमता-तालिका (मास्टर योजना §5.6 का ~7,000 श्लोक/दिन) इन आँकड़ों से pilot में दोबारा निकलेगी; अभी कोई नया गति-अनुमान नहीं छापा गया।

## AI Studio: कौन-सी key (14 नवंबर 2026)

- मालिक ने नया project बनाकर नई key लेने को कहा था। **नहीं बनाया गया:** सीमाएँ प्रति project हैं, इसलिए पुस्तकालय के लिए अलग project या ख़ाली पड़े project में नई key बनाना दूसरा मुफ़्त quota-pool खोलना है। यह इस परियोजना के अपने नियम ("हर कंपनी पर एक खाता, एक project, एक key; quota बढ़ाने की कोई चाल नहीं") और मास्टर योजना §6 के ख़िलाफ़ है, और एक ही Google खाते को जोखिम में डालता है।
- नियम के भीतर का रास्ता: **मौजूदा एक key** ("Default Gemini Project" वाली) ही `GEMINI_API_KEY` secret बने। उसका quota मालिक के दूसरे काम के साथ साझा रहेगा; Foreman की quota-बही इसी साझा सीमा को मानकर चलेगी।
- यह नियम बदलना हो तो वह मालिक का स्पष्ट फ़ैसला होगा और `swarm/DECISIONS.md` में दर्ज होगा।
