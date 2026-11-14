#!/usr/bin/env bash
# दिन-8 की जाँच (क़दम 0.14): drive.file token जीवित है? 06_runs/ में एक छोटी test-फ़ाइल लिखता है।
set -euo pipefail
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TMP="$(mktemp)"
echo "sanatan-granth drive.file token check $STAMP" > "$TMP"
rclone copyto "$TMP" "granth:Sanatan_Library/06_runs/token_check_$STAMP.txt"
rclone ls "granth:Sanatan_Library/06_runs" | tail -3
rm -f "$TMP"
echo "token जीवित है"
