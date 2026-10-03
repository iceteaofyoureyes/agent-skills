"""Operator entry point; authenticated decisions belong to the trusted host API."""
import argparse
import json
from pathlib import Path

from shared.sdlc.foundation import workflow
from shared.sdlc.foundation.inventory import inventory
from shared.sdlc.policy.contract import read_policy
from shared.sdlc.schema import read_document, safe_file
from shared.sdlc.topology.contract import read_topology


def main(argv=None):
    parser = argparse.ArgumentParser(prog='project-foundation')
    parser.add_argument('command', choices=('brownfield', 'greenfield', 'refresh', 'inventory', 'doctor'))
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--run-id', default='foundation-1')
    parser.add_argument('--topology', default='.sdlc/topology.json')
    parser.add_argument('--config-revision', default='R1')
    parser.add_argument('--level', choices=('MINIMAL', 'STANDARD', 'EXTENDED'), default='MINIMAL')
    parser.add_argument('--input', help='project-relative JSON/YAML analysis input; no authentication callbacks')
    parser.add_argument('--manifest-id', default='foundation')
    parser.add_argument('--revision', default='R1')
    args = parser.parse_args(argv)
    root = args.project_root.absolute()
    try:
        if args.command == 'doctor':
            result = workflow.doctor(root, args.run_id)
        elif args.command == 'inventory':
            topology = read_topology(safe_file(root, args.topology).read_text(encoding='utf-8'))
            result = inventory(root, topology, read_policy(root))
        else:
            inputs = read_document(safe_file(root, args.input).read_text(encoding='utf-8')) if args.input else {}
            allowed = {'sections', 'blockers', 'impact', 'previous_ref', 'authority_claims', 'contradictions'}
            if type(inputs) is not dict or set(inputs) - allowed:
                raise ValueError('unsupported Foundation analysis input')
            mode = {'brownfield': 'BROWNFIELD_RECOVERY', 'greenfield': 'GREENFIELD_BOOTSTRAP',
                    'refresh': 'FOUNDATION_REFRESH'}[args.command]
            workflow.start(root, args.run_id, mode,
                workflow.exact_ref(root, args.topology, args.config_revision),
                workflow.exact_ref(root, '.sdlc/project-policy.yml', args.config_revision), level=args.level)
            result = workflow.prepare(root, args.run_id, args.manifest_id, args.revision, **inputs)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1 if result.get('status') in ('NOT_READY', 'BLOCKED') else 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'BLOCKED', 'human_approval': False, 'reason': str(error)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
