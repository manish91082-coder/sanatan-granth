# स्वार्म की हालत

अपडेट: 25 Nov 2026 05:33 IST (2026-11-25T00:03:14Z). यह मशीन की प्रक्रिया-स्थिति है; कोई त्रुटि-दर या सत्यापन का दावा नहीं।

**लक्ष्य:** P2 pilot: कड़ी को नापना और go/no-go की रिपोर्ट तक पहुँचना (मास्टर योजना §9 P2)। उत्पादन नहीं।

## काम

| काम | step | स्थिति | अगला समय | पिछली बार पूरा | कारण / टिप्पणी |
|---|---|---|---|---|---|
| `isha-e2e` | pilot_e2e · daily | चल रहा / कतार में | — | 24 Nov 06:20 IST |  |
| `judge-requal` | judge_test · weekly | पूरा | — | 18 Nov 06:00 IST |  |
| `gita-1-e2e` | pilot_e2e · once | पूरा | — | 18 Nov 14:42 IST |  |
| `gita-2-e2e` | pilot_e2e · once | पूरा | — | 18 Nov 15:10 IST |  |
| `gita-1-e2e-v08` | pilot_e2e · once | पूरा | — | 19 Nov 00:36 IST |  |
| `gita-2-e2e-v08` | pilot_e2e · once | पूरा | — | 19 Nov 01:34 IST |  |

## मॉडल

| मॉडल | स्रोत | परिवार | भूमिका (roster) | अभी | आज के अनुरोध / हमारा हिस्सा |
|---|---|---|---|---|---|
| `gemini-3.5-flash-lite` | google_ai_studio | google | ड्राफ़्ट + जज | रुका: quality → 01 Dec 06:20 IST | 0 / 300 |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | openrouter | nvidia | ड्राफ़्ट + जज | चल सकता है | 0 / 40 |
| `baidu/ernie-5.5-flash-preview:free` | openrouter | baidu | जज | चल सकता है | 0 / 40 |
| `openai/gpt-oss-120b` | groq | openai | ड्राफ़्ट + जज | चल सकता है | 0 / 800 |
| `qwen/qwen3.8-27b` | groq | alibaba-qwen | ड्राफ़्ट | चल सकता है | 0 / 800 |
| `gemma-4-31b-it` | google_ai_studio | google | ड्राफ़्ट | चल सकता है | 0 / 2000 |
| `gpt-oss-120b` | ovh | openai | जज | चल सकता है | 0 / 400 |
| `DeepSeek-V4.1-Flash-1017` | ovh | deepseek | ड्राफ़्ट + जज | चल सकता है | 0 / 400 |
| `Qwen3.5-397B-A17B` | ovh | alibaba-qwen | ड्राफ़्ट + जज | चल सकता है | 0 / 400 |
| `Qwen3.8-27B` | ovh | alibaba-qwen | कोई नहीं | चल सकता है | 0 / 400 |
| `DeepSeek-V3.1` | sambanova | deepseek | कोई नहीं | key नहीं (यह स्रोत अभी जुड़ा नहीं) | 0 / 18 |
| `Meta-Llama-3.3-70B-Instruct` | sambanova | meta | कोई नहीं | key नहीं (यह स्रोत अभी जुड़ा नहीं) | 0 / 18 |

OpenRouter ने बताया: खाते के आज के मुफ़्त अनुरोध 0 (मालिक की दूसरी keys समेत)।

## अभी की रचना

चुनी गई: draft_a = `DeepSeek-V4.1-Flash-1017`, draft_b = `nvidia/nemotron-3-ultra-550b-a55b:free`, judge = `baidu/ernie-5.5-flash-preview:free`, draft_c = `Qwen3.5-397B-A17B`

## इस चक्कर में

- isha-e2e: कतार में → isha-e2e.20261125.10
