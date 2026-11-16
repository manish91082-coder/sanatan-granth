# Drive पुल: `MyDrive/Sanatan_Library/` (मास्टर योजना §4.2)

Drive पूरा master-भंडार है; सत्य-स्रोत git ही रहता है। पहुँच केवल मालिक के **अपने OAuth client** और केवल **`drive.file`** scope से होती है। इस scope की चाबी केवल वही फ़ाइलें देख सकती है जो **इसी Google Cloud project के app** ने बनाई हों।

> **16 नवंबर 2026 की स्थिति (मालिक का फ़ैसला):** नया project नहीं बना; मालिक के एक मौजूदा project का Desktop OAuth client दोबारा उपयोग हुआ (consent "In production")। जाँच में दिखा कि `granth:` को `Sanatan_Library/` के अलावा वे folders भी दिखते हैं जो उसी project के app ने मालिक के दूसरे काम के लिए पहले बनाए थे। फ़िल्म का folder नहीं दिखता। यानी अलगाव पूरा नहीं है: इस repo की scripts केवल `granth:Sanatan_Library/` छूती हैं, पर token की पहुँच उससे चौड़ी है। पूरा अलगाव चाहिए तो पुस्तकालय के लिए अलग Cloud project (बिना billing) का client बनाकर `granth` दोबारा बनाएँ। **यह token Kaggle Secret में तब तक न डालें जब तक मालिक यह तय न कर लें।**

- rclone remote का नाम: **`granth:`** (क़दम 0.7 में मालिक बनाते हैं; client ID/secret और token केवल मालिक के लैपटॉप के rclone config और Kaggle Secret `RCLONE_GRANTH_CONF` में)।
- **GitHub में कोई Drive token नहीं।** Actions Release assets बनाता है; Drive में लिखने का काम Kaggle kernel (official API से चला) या मालिक का लैपटॉप करता है।
- हर उप-folder का एक ही लेखक। मशीन कभी स्थायी delete नहीं करती: हटाना = `99_trash_staging/` में ले जाना।
- फ़िल्म-प्रोजेक्ट का Drive-folder और उसका rclone remote इस repo के किसी code में नहीं आते (जाँच R13)।

## Tree

```
Sanatan_Library/
├── 00_admin/             manifest.jsonl (path, sha256, size, source, licence, run_id)
├── 01_sources_raw/       मूल डाउनलोड और scans (सर्वाधिकार-युक्त scans केवल यहीं, कभी public नहीं)
├── 02_canonical/         git की release-वार प्रति
├── 03_releases/          SQLite, Parquet, JSONL, checksums
├── 04_media/             P6 में
├── 05_review/            Sheet-dashboard (केवल देखने के लिए)
├── 06_runs/              Kaggle/Actions logs, checkpoints, token-जाँच की test-फ़ाइलें
├── 07_tickets/colab/     Colab-tickets; Run all केवल मालिक दबाएँ (Colab कभी स्वचालित नहीं)
└── 99_trash_staging/     soft-delete
```

## एक बार का setup (क़दम 0.7)

```powershell
# 1. login (किसी भी ख़ाली port पर; मौजूदा remote का OAuth client दोबारा उपयोग)
python tools\setup\drive_login.py --remote granth --reuse-from <मौजूदा remote>

# 2. tree + test-फ़ाइल + जाँच
powershell -ExecutionPolicy Bypass -File tools\setup\setup_drive.ps1
```

rclone का अपना login (`rclone config create` / `reconnect`) हमेशा port 53682 पर सुनता है। मालिक के Windows पर यह port "excluded port range" में है, इसलिए वह रास्ता वहाँ नहीं चलता; `drive_login.py` इसी कारण बना।

`drive.file` की एक सीमा: इस remote से `rclone lsd granth:` में Drive की बाक़ी फ़ाइलें नहीं दिखतीं। यही अपेक्षित है।

## दिन-8 की जाँच (क़दम 0.14)

OAuth consent screen "Testing" में रह गया हो तो refresh token 7 दिन में मर जाता है। 0.7 के 8 दिन बाद `bash drive/token_check.sh` चलाएँ: `06_runs/` में एक छोटी test-फ़ाइल बननी चाहिए।
