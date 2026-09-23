from pathlib import Path
import argparse
import json
import sys

sys.dont_write_bytecode = True

from contracts import validate_state_data


def main():
    parser = argparse.ArgumentParser(description="Validate BA workflow-state.json")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        state = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"INVALID: {error}", file=sys.stderr)
        return 1
    errors = validate_state_data(state)
    for error in errors:
        print(f"INVALID: {error}", file=sys.stderr)
    if errors:
        return 1
    print("VALID: workflow state")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
