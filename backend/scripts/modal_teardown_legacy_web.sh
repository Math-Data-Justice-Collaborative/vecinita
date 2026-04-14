#!/bin/bash
# Reference commands after migrating deploy hooks to services/* Modal entrypoints.
# Run locally with an authenticated Modal CLI when you are ready to retire old web routes.
#
# Modal keeps traffic on old containers until new ones are ready (zero-downtime redeploy);
# deleting an app is destructive — confirm consumers have moved to the new URLs first.
#
# Docs: https://modal.com/docs/guide/managing-deployments
#       https://modal.com/docs/guide/modal-1-0-migration

set -euo pipefail

echo "Examples (uncomment and run after verifying names in your workspace):"
echo "# modal app list --all"
echo "# modal app stop <legacy-app-name>    # stops traffic; see Modal dashboard for exact names"
echo "# modal app delete <legacy-app-name>  # irreversible"
