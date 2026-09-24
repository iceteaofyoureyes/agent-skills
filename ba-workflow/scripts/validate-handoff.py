from pathlib import Path
import argparse
import sys

sys.dont_write_bytecode = True

from contracts import validate_handoff_file


def main():
    parser = argparse.ArgumentParser(description="Validate an approved BA engineering handoff")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    errors = validate_handoff_file(args.path)
    for error in errors:
        print(f"INVALID: {error}", file=sys.stderr)
    if errors:
        return 1
    print("VALID: engineering handoff and source hashes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
