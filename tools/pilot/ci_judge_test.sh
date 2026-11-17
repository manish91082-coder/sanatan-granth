#!/usr/bin/env bash
# जज-परीक्षा CI में चलाता है और नतीजे का डेटा-PR खोलता है।
#   tools/pilot/ci_judge_test.sh <text_id> [open_pr: yes|no]
# env: JUDGES (वैकल्पिक: जजों की सूची, अल्पविराम से); GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY; PR_TOKEN (न हो तो PR नहीं, केवल artifact)
set -uo pipefail

TEXT="${1:?text_id}"; OPEN_PR="${2:-yes}"
[[ "$TEXT" =~ ^[a-z][a-z0-9_]{0,40}$ ]] || { echo "::error::text_id अमान्य"; exit 2; }

OUT=/tmp/pilot
rm -rf "$OUT"
python -m tools.pilot.judge_test --text "$TEXT" --out "$OUT" --judges "${JUDGES:-}" | tee /tmp/judge_test_summary.json
RC=${PIPESTATUS[0]}
{
  echo "### जज-परीक्षा · $TEXT · exit $RC"
  echo '```json'; cat /tmp/judge_test_summary.json 2>/dev/null; echo '```'
} >> "${GITHUB_STEP_SUMMARY:-/dev/null}"

REPORT="$OUT/report/judge_test_${TEXT}.json"
if [ "$RC" -eq 0 ] && [ "$OPEN_PR" = "yes" ] && [ -n "${PR_TOKEN:-}" ] && [ -f "$REPORT" ]; then
  BRANCH="data/judge-test-${TEXT}-run${GITHUB_RUN_ID:-0}"
  REMOTE="https://x-access-token:${PR_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
  mkdir -p audit/pilot
  cp "$REPORT" "audit/pilot/judge_test_${TEXT}.json"
  git config user.name "sanatan-granth-swarm"
  git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
  git checkout -q -b "$BRANCH"
  git add "audit/pilot/judge_test_${TEXT}.json"
  git commit -q -m "pilot: ${TEXT} पर जज-परीक्षा का नतीजा" -m "मशीन-माप; मानव-समीक्षा नहीं। run ${GITHUB_RUN_ID:-local}"
  if git push -q "$REMOTE" "$BRANCH" 2>/tmp/push_err; then
    BODY="स्वार्म का मशीन-बना डेटा-PR: \`audit/pilot/judge_test_${TEXT}.json\` (जानबूझकर बिगाड़े गए अनुवाद जज ने पकड़े या नहीं)। मशीन-माप; मानव-समीक्षा नहीं। run: ${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID:-0}"
    if PR_URL=$(GH_TOKEN="$PR_TOKEN" gh pr create --repo "$GITHUB_REPOSITORY" --head "$BRANCH" --base main \
                  --title "pilot: ${TEXT} पर जज-परीक्षा का नतीजा" --body "$BODY" 2>/tmp/pr_err); then
      echo "PR: $PR_URL"
      GH_TOKEN="$PR_TOKEN" gh pr merge "$PR_URL" --auto --squash >/dev/null 2>/tmp/merge_err \
        && echo "auto-merge चालू (required checks हरे होने पर)" || echo "::warning::auto-merge चालू नहीं हो सका: $(head -c 200 /tmp/merge_err)"
    else
      echo "::warning::PR नहीं खुल सका: $(head -c 200 /tmp/pr_err)"
    fi
  else
    echo "::warning::branch push नहीं हुआ: $(sed -E 's/x-access-token:[^@]+@/x-access-token:***@/g' /tmp/push_err | head -c 200)"
  fi
  git checkout -q --detach 2>/dev/null || true
fi
exit "$RC"
