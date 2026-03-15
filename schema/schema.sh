#!/usr/bin/env bash
# Regenerates src/aind_log_utils/_log_model.py from schema/logs.json using datamodel-codegen.
# Run from anywhere:  bash schema/schema.sh
# Or make executable: chmod +x schema/schema.sh && ./schema/schema.sh
set -euo pipefail

# Always operate relative to the repo root, regardless of where the script is called from.
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

uv run datamodel-codegen \
  --input "$REPO_ROOT/schema/logs.json" \
  --input-file-type jsonschema \
  --output "$REPO_ROOT/src/aind_log_utils/_log_model.py" \
  --output-model-type pydantic_v2.BaseModel \
  --use-default \
  --use-default-kwarg \
  --strict-nullable
