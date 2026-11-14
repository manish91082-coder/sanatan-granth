# sanatan-granth

**सनातन ग्रंथों का खुला पुस्तकालय (निर्माणाधीन) · An open library of Sanatan texts (under construction)**

> ⚠️ **यह निर्माणाधीन डेटा-repo है।** यहाँ के अनुवाद और टिप्पणियाँ **AI-मसौदे हैं, जिनकी मानव-समीक्षा नहीं हुई है।** हर प्रविष्टि पर बैज है। अभी केवल दो बैज संभव हैं:
>
> | बैज | अर्थ |
> |---|---|
> | **C** | AI-मसौदा · मानव-समीक्षा नहीं · स्वचालित जाँचें पास |
> | **D** | AI-मसौदा · जाँच में आपत्ति खुली है |
>
> इस repo की किसी चीज़ को शास्त्र का अंतिम या आधिकारिक अर्थ न मानें। संस्कृत पाठ पर लिखा "N स्वतंत्र डिजिटल गवाहों से मिलान" एक मशीन-जाँच का तथ्य है, विद्वानों की समीक्षा का दावा नहीं।
>
> ⚠️ **Work in progress.** Translations and notes here are **AI drafts with no human review.** Every item carries a badge; only **C** (AI draft, automated checks passed) and **D** (AI draft, a check raised an objection) exist until invited experts review the work. Do not treat anything here as an authoritative reading of scripture.

## क्या है

- श्रेणी-वार और विषय-वार सूची (18 विद्याएँ + 8 जोड़े गए खाने), सृष्टि से आज तक।
- हर ग्रंथ का संस्कृत पाठ कम-से-कम दो स्वतंत्र गवाहों से मिलाया जाता है, तभी lock होता है।
- अनुवाद कई मॉडल-परिवारों के मसौदों, स्वचालित व्याकरण-जाँचों और पुराने सार्वजनिक-डोमेन अनुवादों से परखे जाते हैं।
- विशेषज्ञों की समीक्षा बाद में, केवल-निमंत्रण मंच से होगी। तब तक कोई बैज C/D से ऊपर नहीं जा सकता; यह नियम code में बँधा है (`checks/`, जाँच R3)।

## ढाँचा

```
swarm/      PLAN · DECISIONS · AUDIT_LOG · RUBRIC · HANDOFF   (निरंतरता-फ़ाइलें)
policy/     लाइसेंस allow-list · सीमाएँ · संवेदनशील विषयों के नियम · quotas
schema/     JSON Schemas (सूची-कार्ड, परतें, गवाह, jobs)
catalog/    हर ग्रंथ का एक कार्ड + विषय-तालिका + saturation-मीटर
texts/      <ग्रंथ>/root/sa-Deva · translation/{hi,en} · variant · text_lock.json
witnesses/  गवाह-संस्करणों का metadata (पाठ नहीं)
sources/    manifest.jsonl (sha256 + लाइसेंस; पाठ नहीं)
checks/     R1–R14 (रोज़ पूरे repo पर) · A1–A11 · D1–D12 · canary-परीक्षा
canaries/   3 जानबूझकर ग़लत फ़ाइलें, जिन्हें जाँचें हर बार पकड़ें
foreman/    Cloudflare पर चलने वाला नियतात्मक संचालक (कोई LLM-routing नहीं)
state/      बही-खाते की रात की प्रति
audit/      daily/ (script) · weekly/ (meta-audit)
```

## लाइसेंस

- **Code** (`checks/`, `tools/`, `foreman/`, workflows): MIT, देखें `LICENSE`।
- **डेटा:** हर फ़ाइल के `_meta.licence` में SPDX पहचान है। विवरण `LICENSES.md` में।
- तुलना-गवाह (GRETIL आदि, NC/ND/SA) का पाठ यहाँ नहीं रखा जाता।

## सीमाएँ, साफ़ शब्दों में

- यहाँ कोई त्रुटि-दर नहीं छपेगी, जब तक विशेषज्ञ उसे नाप न लें। केवल प्रक्रिया-आँकड़े दिखेंगे (कितनी जाँचें पास, कितने झंडे खुले)।
- कोई AI यहाँ देवता या गुरु बनकर नहीं बोलता। शास्त्र के वचन केवल श्लोक-ID के साथ अनुवाद के रूप में आते हैं।
- यह क़ानूनी, चिकित्सा या ज्योतिषीय सलाह नहीं है।
