# स्वार्म की हालत

अपडेट: 18 Nov 2026 05:32 IST (2026-11-18T00:02:16Z). यह मशीन की प्रक्रिया-स्थिति है; कोई त्रुटि-दर या सत्यापन का दावा नहीं।

**लक्ष्य:** P2 pilot: कड़ी को नापना और go/no-go की रिपोर्ट तक पहुँचना (मास्टर योजना §9 P2)। उत्पादन नहीं।

## काम

| काम | step | स्थिति | अगला समय | पिछली बार पूरा | कारण / टिप्पणी |
|---|---|---|---|---|---|
| `isha-e2e` | pilot_e2e · daily | चल रहा / कतार में | — | 17 Nov 18:43 IST |  |
| `judge-requal` | judge_test · weekly | रुका (मॉडल या quota) | 18 Nov 05:35 IST | — | जज-परीक्षा: कड़ी के जज (roster) अभी सब उपलब्ध नहीं |
| `gita-1-2-e2e` | pilot_e2e · once | बंद (कतार में enabled नहीं) | — | — |  |

## मॉडल

| मॉडल | परिवार | भूमिका (roster) | अभी | आज के अनुरोध / हमारा हिस्सा |
|---|---|---|---|---|
| `gemini-3.5-flash-lite` | google | ड्राफ़्ट + जज | रुका: overloaded → 18 Nov 05:47 IST | 8 / 300 |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | nvidia | ड्राफ़्ट | रुका: daily_quota → 18 Nov 05:35 IST | 0 / 40 |
| `baidu/ernie-5.5-flash-preview:free` | baidu | जज | दिन का हिस्सा पूरा → 19 Nov 05:35 IST | 0 / 40 |
| `openai/gpt-oss-120b` | openai | ड्राफ़्ट | चल सकता है | 0 / 800 |
| `qwen/qwen3.8-27b` | alibaba-qwen | ड्राफ़्ट | चल सकता है | 0 / 800 |
| `gemma-4-31b-it` | google | ड्राफ़्ट | चल सकता है | 0 / 2000 |
| `gpt-oss-120b` | openai | जज | चल सकता है | 0 / 400 |
| `DeepSeek-V4.1-Flash-1017` | deepseek | ड्राफ़्ट + जज | चल सकता है | 0 / 400 |
| `Qwen3.5-397B-A17B` | alibaba-qwen | ड्राफ़्ट + जज | चल सकता है | 0 / 400 |
| `Qwen3.8-27B` | alibaba-qwen | कोई नहीं | चल सकता है | 0 / 400 |
| `DeepSeek-V3.1` | deepseek | कोई नहीं | चल सकता है | 0 / 18 |
| `Meta-Llama-3.3-70B-Instruct` | meta | कोई नहीं | चल सकता है | 0 / 18 |

OpenRouter ने बताया: खाते के आज के मुफ़्त अनुरोध 0 (मालिक की दूसरी keys समेत)।

## अभी की रचना

चुनी गई: draft_a = `DeepSeek-V4.1-Flash-1017`, draft_b = `Qwen3.5-397B-A17B`, judge = `gpt-oss-120b`, draft_c = `gemma-4-31b-it`

## इस चक्कर में

- isha-e2e: कतार में → isha-e2e.20261118.3
