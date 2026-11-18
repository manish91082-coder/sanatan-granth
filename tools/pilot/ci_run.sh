#!/usr/bin/env bash
# Pilot की पूरी कड़ी CI में चलाता है और नतीजे का डेटा-PR खोलता है।
#   tools/pilot/ci_run.sh <text_id> <batch_id> <job_key|-> <mock: yes|no> [open_pr: yes|no]
# env: GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY (मॉडल-calls); PR_TOKEN (डेटा-PR के लिए; न हो तो PR नहीं खुलता, केवल artifact);
#      SWARM_STATE_DIR (वैकल्पिक: सेहत-बही और अधूरे काम; tools/swarm/state_sync.sh)
# बाहर: /tmp/pilot/report/*.json; $GITHUB_OUTPUT में status, ref, rc (75 = रुका)
set -uo pipefail

TEXT="${1:?text_id}"; BATCH="${2:?batch_id}"; JOBKEY="${3:--}"; MOCK="${4:-no}"; OPEN_PR="${5:-yes}"
[[ "$TEXT" =~ ^[a-z][a-z0-9_]{0,40}$ ]] || { echo "::error::text_id अमान्य"; exit 2; }
[[ "$BATCH" =~ ^[A-Za-z0-9_.:-]{1,80}$ ]] || { echo "::error::batch_id अमान्य"; exit 2; }
[[ "$JOBKEY" == "-" || "$JOBKEY" =~ ^[0-9a-f]{64}$ ]] || { echo "::error::job_key अमान्य"; exit 2; }

OUT=/tmp/pilot
rm -rf "$OUT"
args=(--text "$TEXT" --out "$OUT" --batch-id "$BATCH")
[ "$JOBKEY" != "-" ] && args+=(--job-key "$JOBKEY")
[ "$MOCK" = "yes" ] && args+=(--mock)

python -m tools.pilot.run_e2e "${args[@]}" | tee /tmp/pilot_summary.json
RC=${PIPESTATUS[0]}

{
  echo "### pilot e2e · $TEXT · batch $BATCH · mock=$MOCK · exit $RC"
  echo '```json'; cat /tmp/pilot_summary.json 2>/dev/null; echo '```'
} >> "${GITHUB_STEP_SUMMARY:-/dev/null}"

REF="run:${GITHUB_RUN_ID:-local}"
if [ "$RC" -eq 0 ] && [ "$MOCK" != "yes" ] && [ "$OPEN_PR" = "yes" ] && [ -n "${PR_TOKEN:-}" ]; then
  KEY16="${JOBKEY:0:16}"; [ "$JOBKEY" = "-" ] && KEY16="run${GITHUB_RUN_ID:-0}"
  BRANCH="data/pilot-${TEXT}-${KEY16}"
  mkdir -p audit/pilot state
  cp "$OUT"/report/*_e2e.json audit/pilot/   # इकाई = ग्रंथ (isha_e2e.json) या उसका अध्याय (gita_1_e2e.json)
  cp "$OUT/report/pilot_metrics.json" state/pilot_metrics.json
  if git ls-remote --exit-code --heads "https://x-access-token:${PR_TOKEN}@github.com/${GITHUB_REPOSITORY}.git" "$BRANCH" >/dev/null 2>&1; then
    echo "branch $BRANCH पहले से है (वही job दोबारा): नया PR नहीं"
  else
    git config user.name "sanatan-granth-swarm"
    git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
    git checkout -q -b "$BRANCH"
    git add audit/pilot/*_e2e.json state/pilot_metrics.json
    git commit -q -m "pilot: ${TEXT} की पूरी कड़ी का नतीजा (batch ${BATCH})" -m "AI-मसौदा; बैज केवल C/D; संस्कृत पाठ इस PR में नहीं। run ${GITHUB_RUN_ID:-local}"
    if git push -q "https://x-access-token:${PR_TOKEN}@github.com/${GITHUB_REPOSITORY}.git" "$BRANCH" 2>/tmp/push_err; then
      BODY="स्वार्म का मशीन-बना डेटा-PR (pilot)। \`audit/pilot/\` में ${TEXT} की रिपोर्ट और \`state/pilot_metrics.json\`। AI-मसौदा; बैज केवल C/D; संस्कृत पाठ इसमें नहीं। run: ${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID:-0}"
      if PR_URL=$(GH_TOKEN="$PR_TOKEN" gh pr create --repo "$GITHUB_REPOSITORY" --head "$BRANCH" --base main \
                    --title "pilot: ${TEXT} की पूरी कड़ी का नतीजा (batch ${BATCH})" --body "$BODY" 2>/tmp/pr_err); then
        echo "PR: $PR_URL"
        REF="pr:${PR_URL##*/}"
        GH_TOKEN="$PR_TOKEN" gh pr merge "$PR_URL" --auto --squash >/dev/null 2>/tmp/merge_err \
          && echo "auto-merge चालू (required checks हरे होने पर)" || echo "::warning::auto-merge चालू नहीं हो सका: $(head -c 200 /tmp/merge_err)"
      else
        echo "::warning::PR नहीं खुल सका (token में Pull requests: write चाहिए): $(head -c 200 /tmp/pr_err)"
        REF="branch:${BRANCH}"
      fi
    else
      echo "::warning::branch push नहीं हुआ: $(sed -E 's/x-access-token:[^@]+@/x-access-token:***@/g' /tmp/push_err | head -c 200)"
    fi
  fi
fi

STATUS=failed; [ "$RC" -eq 0 ] && STATUS=done
# 75 = रुका: बाहर की रुकावट (quota, बंद मॉडल, कोई योग्य रचना नहीं)। Foreman के लिए यह चक्कर पूरा है (दोबारा कब चलाना है,
# यह स्वार्म का संचालक तय करता है; बचा काम state branch में है); job लाल नहीं होता।
if [ "$RC" -eq 75 ]; then
  STATUS=done; REF="blocked:run${GITHUB_RUN_ID:-0}"
  echo "::notice::run रुका (मॉडल या quota): $(head -c 300 "$OUT/report/blocked.json" 2>/dev/null | tr '\n' ' ')"
fi
{ echo "status=$STATUS"; echo "ref=$REF"; echo "rc=$RC"; } >> "${GITHUB_OUTPUT:-/dev/null}"
[ "$RC" -eq 75 ] && exit 0
exit "$RC"
