#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
ADAPTER_FILE="${ADAPTER_FILE:-$REPO_ROOT/script/db-compare/adapters/effy-adapter.yml}"

cd "$REPO_ROOT"
exec python -m script.python.mysql_db_compare_upgrade start --adapter "$ADAPTER_FILE" "$@"
