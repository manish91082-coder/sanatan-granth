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
| Google AI Studio | मुफ़्त Batch API चला? | (बाक़ी: `GEMINI_API_KEY` secret के बाद परीक्षण) | | |
| Google AI Studio | एक ही project और एक ही key? | (बाक़ी: मालिक पुष्टि करें; पन्ने पर एक project चुना दिखा, जिस पर "Antigravity" नाम की agent-श्रेणी भी है, यानी यह quota मालिक के दूसरे काम के साथ साझा हो सकता है) | 2026-11-14 | |
| Kaggle | साप्ताहिक GPU घंटे | (बाक़ी: क़दम 0.4) | | |
| Kaggle | साप्ताहिक TPU घंटे | (बाक़ी: क़दम 0.4) | | |
| Kaggle | reset का दिन | (बाक़ी: क़दम 0.4) | | |
| Kaggle | T4×2 दोगुना गिनता है? | (बाक़ी: क़दम 0.4) | | |
| Groq | मुफ़्त RPM / RPD / TPM / TPD (gpt-oss-120b) | (बाक़ी: क़दम 0.5) | | |
| Cloudflare | Workers AI neurons/दिन; D1 और DO की Free सीमाएँ console में | (बाक़ी: क़दम 0.11) | | |
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
