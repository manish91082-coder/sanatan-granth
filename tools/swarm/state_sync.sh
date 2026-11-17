#!/usr/bin/env bash
# स्वार्म की हालत (branch 'swarm-state') को SWARM_STATE_DIR में लाना और वापस भेजना।
#   tools/swarm/state_sync.sh pull
#   tools/swarm/state_sync.sh push "<संदेश>"
# env: SWARM_STATE_DIR (ज़रूरी); STATE_TOKEN (इसी repo पर contents: write वाला token); GITHUB_REPOSITORY
# token न हो तो pull ख़ाली हालत बनाता है और push कुछ नहीं करता: काम चलता है, पर हालत अगले run तक नहीं बचती।
# main का ताला वैसा ही रहता है: यह branch केवल मशीन की चालू हालत है (सेहत-बही, कतार की स्थिति, अधूरे काम), कोई ग्रंथ-पाठ नहीं।
# हर लेखक की अपनी फ़ाइलें हैं (संचालक: tasks.json, STATUS.md; काम करने वाला job: health.json, runs/, work/), इसलिए push टकराए
# तो ताज़ा हालत पर अपने commit दोबारा रखे जाते हैं।
set -uo pipefail

CMD="${1:?pull|push}"; MSG="${2:-state}"
DIR="${SWARM_STATE_DIR:?SWARM_STATE_DIR}"
BR=swarm-state
if [ -z "${STATE_TOKEN:-}" ] || [ -z "${GITHUB_REPOSITORY:-}" ]; then
  echo "::warning::STATE_TOKEN नहीं: स्वार्म की हालत इस run के बाहर नहीं बचेगी"
  mkdir -p "$DIR"
  exit 0
fi
REMOTE="https://x-access-token:${STATE_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
mask() { sed -E 's/x-access-token:[^@]+@/x-access-token:***@/g'; }

case "$CMD" in
  pull)
    rm -rf "$DIR"
    mkdir -p "$(dirname "$DIR")"
    if git ls-remote --exit-code --heads "$REMOTE" "$BR" >/dev/null 2>&1; then
      git clone -q --depth 1 --branch "$BR" "$REMOTE" "$DIR" 2>&1 | mask
    else
      mkdir -p "$DIR"
      git -C "$DIR" init -q -b "$BR"
      git -C "$DIR" remote add origin "$REMOTE"
      printf '%s\n' "# swarm-state" "" \
        "स्वार्म की मशीन-हालत: सेहत-बही (health.json), कतार की स्थिति (tasks.json), हर चक्कर का नतीजा (runs/), अधूरे काम (work/)।" \
        "इसे मशीन लिखती है। यह स्रोत-सत्य नहीं है; इसमें कोई संस्कृत पाठ नहीं, और कोई बैज या सत्यापन का दावा नहीं।" \
        "इंसान के पढ़ने के लिए: STATUS.md" > "$DIR/README.md"
    fi
    [ -d "$DIR/.git" ] || { echo "::error::हालत नहीं आई"; exit 1; }
    git -C "$DIR" config user.name "sanatan-granth-swarm"
    git -C "$DIR" config user.email "41898282+github-actions[bot]@users.noreply.github.com"
    echo "हालत आई: $(git -C "$DIR" log -1 --format='%h %cI' 2>/dev/null || echo 'नई branch')"
    ;;
  push)
    [ -d "$DIR/.git" ] || { echo "हालत का फ़ोल्डर git नहीं: push छोड़ा"; exit 0; }
    git -C "$DIR" add -A
    if git -C "$DIR" diff --cached --quiet; then echo "हालत में कोई बदलाव नहीं"; exit 0; fi
    git -C "$DIR" commit -q -m "$MSG"
    for i in 1 2 3 4; do
      if git -C "$DIR" push -q origin "HEAD:refs/heads/$BR" 2>/tmp/state_push_err; then echo "हालत भेजी"; exit 0; fi
      if git -C "$DIR" fetch -q --depth 30 origin "$BR" 2>/dev/null; then
        git -C "$DIR" rebase -q -X theirs FETCH_HEAD 2>/dev/null || git -C "$DIR" rebase --abort 2>/dev/null || true
      fi
      sleep $((i * 3))
    done
    echo "::warning::हालत का push नहीं हुआ: $(mask < /tmp/state_push_err | head -c 200)"
    exit 1
    ;;
  *)
    echo "pull या push"; exit 2 ;;
esac
