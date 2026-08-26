#!/usr/bin/env bash
# workspaceOpen — load engineering-memory plugin for this workspace only.
set -euo pipefail
EM_ROOT="${EM_ROOT:-${HOME}/Documents/GitHub/spec-dev-knowledge-graph}"
export EM_ROOT
python3 -c 'import json, os; print(json.dumps({"pluginPaths": [os.path.join(os.environ["EM_ROOT"], "cursor-plugin")]}))'
