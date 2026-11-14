#!/usr/bin/env bash
# Sanatan_Library/ का tree बनाता है। केवल granth: remote छूता है। दोबारा चलाना सुरक्षित है।
set -euo pipefail
REMOTE="granth:Sanatan_Library"
for d in 00_admin 01_sources_raw 02_canonical 03_releases 04_media 05_review 06_runs 07_tickets/colab 99_trash_staging; do
  rclone mkdir "$REMOTE/$d"
  echo "ok  $d"
done
rclone lsd "$REMOTE"
