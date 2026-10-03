"""Operator entry point; authenticated decisions belong to the trusted host."""
import argparse
import json
from pathlib import Path

from shared.sdlc.foundation import workflow
from shared.sdlc.foundation.inventory import inventory
from shared.sdlc.policy.contract import read_policy
from shared.sdlc.schema import read_document, safe_file
from shared.sdlc.topology.contract import read_topology

PRODUCERS = ('domain-discovery', 'architecture-discovery', 'test-foundation',
             'adr-management', 'c4-modeling')


def _input(root, value):
    data = read_document(safe_file(root, value).read_text(encoding='utf-8'))
    if type(data) is not dict:
        raise ValueError('Foundation input must be an object')
    return data


def _produce(root, run_id, producer, artifact_id, revision, data):
    allowed = {'observations'}
    if producer == 'adr-management': allowed |= {'kind'}
    if producer == 'c4-modeling': allowed |= {'elements', 'relationships'}
    if set(data) - allowed:
        raise ValueError('unsupported producer input')
    return workflow.produce_semantic(root, run_id, producer, artifact_id, revision,
                                     **data)


def main(argv=None):
    commands = ('brownfield', 'greenfield', 'refresh', 'inventory', 'doctor', 'start',
                'prepare', *PRODUCERS, 'render-c4', 'arc42-projection', 'conflicts')
    parser = argparse.ArgumentParser(prog='project-foundation')
    parser.add_argument('command', choices=commands)
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--run-id', default='foundation-1')
    parser.add_argument('--topology', default='.sdlc/topology.json')
    parser.add_argument('--config-revision', default='R1')
    parser.add_argument('--mode', choices=('BROWNFIELD_RECOVERY', 'GREENFIELD_BOOTSTRAP', 'FOUNDATION_REFRESH'))
    parser.add_argument('--level', choices=('MINIMAL', 'STANDARD', 'EXTENDED'), default='MINIMAL')
    parser.add_argument('--input', help='project-relative JSON/YAML semantic input; no authentication callbacks')
    parser.add_argument('--manifest-id', default='foundation')
    parser.add_argument('--revision', default='R1')
    parser.add_argument('--artifact-id', default='semantic')
    parser.add_argument('--source-key')
    args = parser.parse_args(argv)
    root = args.project_root.absolute()
    try:
        if args.command == 'doctor':
            result = workflow.doctor(root, args.run_id)
        elif args.command == 'inventory':
            topology = read_topology(safe_file(root, args.topology).read_text(encoding='utf-8'))
            result = inventory(root, topology, read_policy(root))
        elif args.command == 'start':
            if not args.mode: raise ValueError('start requires --mode')
            result = workflow.start(root, args.run_id, args.mode,
                workflow.exact_ref(root, args.topology, args.config_revision),
                workflow.exact_ref(root, '.sdlc/project-policy.yml', args.config_revision), level=args.level)
        elif args.command == 'prepare':
            inputs = _input(root, args.input) if args.input else {}
            allowed = {'sections', 'blockers', 'impact', 'previous_ref', 'authority_claims', 'contradictions'}
            if set(inputs) - allowed: raise ValueError('unsupported Foundation review input')
            result = workflow.prepare(root, args.run_id, args.manifest_id, args.revision, **inputs)
        elif args.command in PRODUCERS:
            if not args.input: raise ValueError('producer command requires --input')
            result = _produce(root, args.run_id, args.command, args.artifact_id, args.revision,
                              _input(root, args.input))
        elif args.command == 'render-c4':
            if not args.source_key: raise ValueError('render-c4 requires --source-key')
            result = workflow.render_c4_candidate(root, args.run_id, args.source_key)
        elif args.command == 'arc42-projection':
            inputs = _input(root, args.input) if args.input else {}
            if set(inputs) - {'source_keys', 'configuration_revision'} or 'source_keys' not in inputs:
                raise ValueError('arc42 projection requires explicit source_keys')
            result = workflow.project_arc42(root, args.run_id, **inputs)
        elif args.command == 'conflicts':
            inputs = _input(root, args.input) if args.input else {}
            if set(inputs) - {'source_keys', 'disagreements'} or not {'source_keys', 'disagreements'} <= set(inputs):
                raise ValueError('conflict analysis requires explicit source_keys and disagreements')
            result = workflow.detect_semantic_conflicts(root, args.run_id, **inputs)
        else:
            inputs = _input(root, args.input) if args.input else {}
            allowed = {'sections', 'blockers', 'impact', 'previous_ref', 'authority_claims', 'contradictions', 'producers'}
            if set(inputs) - allowed or type(inputs.get('producers', [])) is not list:
                raise ValueError('unsupported Foundation analysis input')
            mode = {'brownfield': 'BROWNFIELD_RECOVERY', 'greenfield': 'GREENFIELD_BOOTSTRAP',
                    'refresh': 'FOUNDATION_REFRESH'}[args.command]
            workflow.start(root, args.run_id, mode,
                workflow.exact_ref(root, args.topology, args.config_revision),
                workflow.exact_ref(root, '.sdlc/project-policy.yml', args.config_revision), level=args.level)
            for item in inputs.pop('producers', []):
                if type(item) is not dict or set(item) != {'producer', 'artifact_id', 'revision', 'input'}:
                    raise ValueError('producer entries require producer, artifact_id, revision and input')
                _produce(root, args.run_id, item['producer'], item['artifact_id'], item['revision'], item['input'])
            result = workflow.prepare(root, args.run_id, args.manifest_id, args.revision, **inputs)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1 if result.get('status') in ('NOT_READY', 'BLOCKED') else 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'BLOCKED', 'human_approval': False, 'reason': str(error)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
