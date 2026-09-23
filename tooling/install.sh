#!/usr/bin/env sh
set -eu
tool_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python=${PYTHON:-python3}
command -v "$python" >/dev/null 2>&1 || { echo "Python 3.8+ is required (set PYTHON if needed)." >&2; exit 2; }
exec "$python" "$tool_dir/lib/ba_kit.py" install "$@"
