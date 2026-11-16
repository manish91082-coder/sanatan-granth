# DECISIONS: केवल जोड़ें, कभी बदलें या मिटाएँ नहीं

यहाँ केवल मालिक के फ़ैसले और स्पष्ट स्वीकृतियाँ दर्ज होती हैं, तिथि के साथ।

## 2026-11-14 · मास्टर योजना §10.2 के फ़ैसले #1–#6 (मालिक ने सिफ़ारिश के अनुसार मंज़ूर किए)

स्रोत: मास्टर योजना §10.2 की "स्वीकृत" पंक्ति (14 नवंबर 2026)।

1. **Repo public रहेगा**, C/D मसौदे बैज के साथ दिखेंगे। P5 (front end) तक कोई प्रचार नहीं।
2. **मशीन-स्तर के डेटा-PR अपने-आप merge होंगे**, जब सारी required जाँचें पास हों। बैज C/D से ऊपर code से असंभव (जाँच R3)।
3. **Escalation-चैनल:** GitHub mobile सूचना + Cloudflare status-पन्ना। Telegram नहीं (phone-नंबर चाहिए)।
4. **तुलसीदास/अवधी** (हनुमान चालीसा, सुन्दरकाण्ड, मानस) अभी मशीन-स्तर पर उत्पादन में, 1931-पूर्व संस्करण मिलने पर।
5. **Gemini के मुफ़्त स्तर का डेटा-उपयोग स्वीकार**, केवल PD/सार्वजनिक पाठ भेजा जाएगा।
6. **गीता जयंती केवल आंतरिक milestone**, कोई सार्वजनिक launch नहीं।

खुले (बाद में): #7 P4-मंच कब, #8 Opus/Fable भूमिकाएँ, #9 Kaggle पर फ़िल्म बनाम पुस्तकालय, #10 अनुमति-पत्र, #11–#15।

## 2026-11-14 · निर्माण-session की दो स्वीकृतियाँ (मालिक, chat में)

- पुस्तकालय का repo फ़िल्म-प्रोजेक्ट से बाहर **`E:\sanatan-granth`** में बने: हाँ।
- GitHub पर public repo `sanatan-granth` **Claude `gh` CLI से बनाए** और पहला commit push करे; branch protection और auto-merge भी `gh` से सेट करे: हाँ।
- इसी के तहत P0 का पहला ढाँचा (`.github/workflows/`, `policy/`, `canaries/`, thresholds सहित) इस interactive session में सीधे `main` पर गया। इसके बाद CLAUDE.md की सीमा #3 पूरी तरह लागू है: इन रास्तों में बदलाव केवल PR से।

## 2026-11-14 · निर्माण-session में merge और label Claude करे (मालिक, chat में)

मालिक का निर्देश (सार): "PR merge करना और label लगाना तुम ही करो; पूरा automation पर ले जाना है; verify बाद में करेंगे।"

इससे क्या बदला:

- **मालिक के interactive निर्माण-session में** Claude अपने बनाए PR पर `owner-approved` label लगा सकता है और required checks (checks, canaries, protected-paths) हरे होने पर squash-merge कर सकता है। यह मास्टर योजना §7.2 की सीमा #1 और #3 में मालिक की दी हुई छूट है।
- हर ऐसे merge का ब्योरा PR में रहता है; मालिक बाद में देख सकते हैं और कोई भी PR revert करवा सकते हैं।

क्या **नहीं** बदला:

- बिना-निगरानी runs (साप्ताहिक meta-audit, reviser cloud task) अब भी कभी merge, label, tag, release या deploy नहीं करते। auditor अपना ही काम merge नहीं करता।
- लाल check पर कोई merge नहीं; branch protection bypass नहीं होती।
- बैज C/D से ऊपर नहीं (R3), संस्कृत-ताला (R2), लाइसेंस-द्वार (R6), canaries: सब वैसे ही।
- keys, tokens, passwords और खाते: Claude नहीं बनाता, नहीं छूता; वे मालिक ही secret-खानों में डालते हैं।
- deploy (Foreman) और release-tag मालिक के बटन से ही चलते हैं, जब तक मालिक अलग से न कहें।

## 2026-11-14 · AI Studio: एक project, एक key ही (मालिक ने फ़ैसला Claude पर छोड़ा)

- मालिक ने `GEMINI_API_KEY` secret ख़ुद डाला (मौजूदा एक key)।
- मालिक ने कहा कि कई keys/projects से उन्हें आपत्ति नहीं, और नियम बदलना है या नहीं, यह Claude तय करे।
- **तय हुआ: नियम नहीं बदला।** एक project, एक key। कारण: सीमाएँ प्रति project हैं, तो उसी project की और keys कुछ नहीं जोड़तीं; और अलग projects से quota जोड़ना मंच के नियमों और इस परियोजना की "quota बढ़ाने की कोई चाल नहीं" शर्त के ख़िलाफ़ जाता है, जबकि खाता एक ही है।
- क्षमता कम पड़े तो रास्ते वही हैं जो योजना में हैं: Kaggle पर खुले मॉडल, Groq, Workers AI, और reset का इंतज़ार।

## 2026-11-16 · साप्ताहिक meta-audit routine और Foreman का दूसरा deploy

- साप्ताहिक सीमा reset के बाद मालिक ने कहा: "तुम तय करो और आगे बढ़ो।" इससे पहले Claude ने तीन बाक़ी काम गिनाए थे: Drive की चाबी, साप्ताहिक audit task, Foreman का नया deploy।
- **Foreman:** Claude ने `foreman-deploy` चलाया (PR #23 का retry-नियम)। यह एक बार की अनुमति है; आगे के deploy भी मालिक के कहने पर ही।
- **साप्ताहिक meta-audit:** मालिक ने "Create" चुना। routine: हर रविवार 03:37 UTC (9:07 AM IST), मॉडल `claude-sonnet-5-5` (pinned), repo केवल `sanatan-granth`, connectors हटे। routine कभी merge, label, tag, release या deploy नहीं करता; केवल रिपोर्ट-PR और issue खोलता है।
- routine का prompt बदलना हो तो पहले `policy/audit_prompt.md` बदले (मालिक के label से), फिर routine।

## 2026-11-16 · Drive: मौजूदा OAuth client दोबारा उपयोग (मालिक का फ़ैसला)

- मास्टर योजना क़दम 0.6 अलग Google Cloud project (बिना billing) कहती थी। मालिक ने कहा कि Drive के लिए पहले से बना rclone-client ही उपयोग हो।
- **किया गया:** नया remote `granth` उसी client से, पर केवल `drive.file` scope के साथ। पुराना remote नहीं छुआ गया।
- **ज्ञात कमी:** `drive.file` की पहुँच app (project) के स्तर पर है, इसलिए `granth` को उसी app के बनाए दूसरे folders भी दिखते हैं। इस repo की scripts केवल `granth:Sanatan_Library/` छूती हैं।
- **खुला फ़ैसला (मालिक):** पूरा अलगाव चाहिए तो पुस्तकालय के लिए अलग project का client। जब तक यह तय न हो, Drive-token Kaggle Secret में नहीं जाएगा।

## 2026-11-16 · Drive: पुस्तकालय का अपना OAuth app (पिछला फ़ैसला बदला)

- मौजूदा client दोबारा उपयोग करने पर token को मालिक के दूसरे काम के folders भी दिखे। मालिक ने कहा: "हाँ, अलग बनाओ।"
- console ने दिखाया कि खाते में केवल 1 project-slot बचा है, इसलिए नया project नहीं बना; मालिक के एक पूरी तरह ख़ाली project में app "Sanatan Granth Library" बना (In production, केवल `drive.file`)। इसमें कोई Gemini key नहीं बनेगी।
- "In production" के लिए Google homepage और privacy-policy link माँगता है: repo और `docs/PRIVACY.md` दिए गए।
- अब `granth` की पहुँच केवल `Sanatan_Library/` तक है (जाँचा गया)। Kaggle Secret वाला क़दम अब खुला है।
