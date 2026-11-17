#!/usr/bin/env bash
# संचालक का एक चक्कर CI में: हालत लाओ → अगला काम चुनो (tick) → हालत लौटाओ।
#   tools/swarm/ci_conduct.sh
# env: SWARM_STATE_DIR, STATE_TOKEN, FOREMAN_URL, FOREMAN_SHARED_SECRET; GH_TOKEN (issue के लिए);
#      GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY (केवल यह देखने को कि key है या नहीं, और OpenRouter से दिन की गिनती पूछने को;
#      संचालक कोई मॉडल-अनुरोध नहीं करता)
set -uo pipefail

bash tools/swarm/state_sync.sh pull || exit 1
python -m tools.swarm.conductor tick > /tmp/swarm_status.md
RC=$?
cat /tmp/swarm_status.md
cat /tmp/swarm_status.md >> "${GITHUB_STEP_SUMMARY:-/dev/null}"
bash tools/swarm/state_sync.sh push "conduct: run ${GITHUB_RUN_ID:-local}" || echo "::warning::हालत नहीं लौटी; अगला चक्कर दोबारा कोशिश करेगा"
exit "$RC"
