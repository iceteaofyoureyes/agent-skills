from pathlib import Path
import argparse
import sys

sys.dont_write_bytecode = True

from ba_contracts import validate_state_data, read_state
from shared.sdlc.schema import read_document


def main():
    parser = argparse.ArgumentParser(description="Validate BA workflow-state.json")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        state = read_document(args.path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"INVALID: {error}", file=sys.stderr)
        return 1
    errors = validate_state_data(state, args.path.parent)
    for error in errors:
        print(f"INVALID: {error}", file=sys.stderr)
    if errors:
        return 1
    print("VALID: workflow state; " + read_state(state, args.path.parent)['mode'])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
