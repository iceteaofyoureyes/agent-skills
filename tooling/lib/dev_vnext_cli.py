"""Thin CLI dispatch to frozen Dev contracts and the persisted VNext runtime.

--host names a trusted deployment module with BA/Foundation/technical callbacks.
Requests and workflow choices cannot supply authenticators or mint receipts.
"""
import argparse
import importlib
import json
from pathlib import Path
import sys

from . import dev_vnext as contracts


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def trusted_context(module_name):
    if not module_name:
        return {}
    module = importlib.import_module(module_name)
    context = {}
    for name in ('ba_authenticator', 'foundation_authenticator', 'technical_authenticator'):
        callback = getattr(module, name, None)
        if callback is not None and not callable(callback):
            raise ValueError(f'trusted host {name} must be callable')
        if callback is not None:
            context[name] = callback
    return context


def parser():
    cli = argparse.ArgumentParser(description='Dev Kit VNext runtime (READY_FOR_TEST is a Dev handoff)')
    cli.add_argument('--project-root', type=Path, default=Path.cwd())
    cli.add_argument('--host', help='Trusted deployment module; never a receipt/request field')
    cli.add_argument('--run-id', help='Persisted run; defaults to .devkit/current.json')
    commands = cli.add_subparsers(dest='command', required=True)
    start = commands.add_parser('start')
    start.add_argument('--request', type=Path, required=True)
    for name in ('validate-authority', 'impact-template', 'technical-gate-required', 'implementation-ready', 'begin-implementation', 'verify', 'status', 'replan', 'begin-fix-wave'):
        commands.add_parser(name)
    for name in ('impact', 'raise-gap', 'bind-technical-approval', 'escalate-risk'):
        sub = commands.add_parser(name)
        sub.add_argument('--artifact', type=Path, required=True, help='JSON document (impact/gap/risk) or exact reference (approval)')
    resume = commands.add_parser('resume-gap')
    resume.add_argument('--replacement-ref', type=Path, required=True)
    resume.add_argument('--resolution-ref', type=Path, required=True)
    plan = commands.add_parser('plan')
    plan.add_argument('--plan', type=Path, required=True)
    plan.add_argument('--tasks', type=Path, required=True)
    plan.add_argument('--decision-ref', type=Path, action='append', default=[])
    plan.add_argument('--decision-refs', type=Path, help='JSON array of exact ED refs')
    plan.add_argument('--revision')
    for name in ('authorize-write', 'write-source'):
        sub = commands.add_parser(name)
        sub.add_argument('--repository-id', required=True)
        sub.add_argument('--path', required=True)
        if name == 'write-source': sub.add_argument('--content', type=Path, required=True)
    review = commands.add_parser('review')
    review.add_argument('--evidence-ref', type=Path, action='append', required=True)
    review.add_argument('--findings', type=Path)
    review.add_argument('--kind', choices=('full', 'scoped'), default='full')
    review.add_argument('--what-gap', type=Path)
    fixed = commands.add_parser('complete-fix-wave')
    fixed.add_argument('--evidence-ref', type=Path, action='append', required=True)
    discovery = commands.add_parser('maintenance-discovery')
    discovery.add_argument('--changes', type=Path, required=True, help='JSON array of discovered changes')
    final = commands.add_parser('finalize', aliases=['handoff'])
    final.add_argument('--coverage', type=Path, required=True)
    final.add_argument('--known-risks', type=Path)
    validate = commands.add_parser('validate-artifact')
    validate.add_argument('--kind', choices=('state','impact','handoff'), required=True)
    validate.add_argument('path', type=Path)
    legacy = commands.add_parser('legacy')
    inspect = legacy.add_subparsers(dest='legacy_command', required=True).add_parser('inspect')
    inspect.add_argument('--kind', choices=('state','impact','handoff'), required=True)
    inspect.add_argument('path', type=Path)
    route = commands.add_parser('route')
    route.add_argument('--delivery', type=Path, required=True)
    route.add_argument('--summary', required=True)
    gate = commands.add_parser('gate-approved')
    gate.add_argument('--choice', required=True)
    gate.add_argument('--workflow-run-id', required=True)
    workflow = commands.add_parser('spec-kit')
    workflow.add_argument('action', choices=('run','resume','status','observe'))
    workflow.add_argument('--executable', default='specify')
    workflow.add_argument('--workflow-run-id')
    workflow.add_argument('--state-ref', type=Path)
    workflow.add_argument('--devkit-command', default='devkit')
    workflow.add_argument('--technical-receipt-ref', default='')
    workflow.add_argument('--integration', default='auto')
    workflow.add_argument('--choice', choices=('approve','reject'), default='', help='Orchestration choice only; never technical authority')
    describe = commands.add_parser('workflow')
    describe.add_argument('depth', choices=('normal','high-risk'))
    return cli


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == 'route':
            raise ValueError('DELIVERY_MANIFEST: DEFERRED_NON_AUTHORITATIVE; use start with Engineering Handoff VNext')
        if args.command == 'gate-approved':
            raise ValueError('Spec Kit choice is orchestration evidence only; bind an exact authenticated technical receipt')
        context = trusted_context(args.host)
        if args.command == 'workflow':
            from .dev_vnext_spec_kit import workflow_document
            result = workflow_document(high_risk=args.depth == 'high-risk')
        elif args.command in ('validate-artifact','legacy'):
            data = read_json(args.path)
            if args.command == 'legacy' and data.get('schema_version') != 1:
                raise ValueError('legacy inspect accepts V1 artifacts only')
            result = contracts.read_artifact(data,args.kind,args.project_root,**context)
        else:
            if args.command == 'start':
                request = read_json(args.request)
                if not isinstance(request,dict) or type(request.get('schema_version',2)) is not int or request.get('schema_version',2) != 2 or 'authority_mode' not in request:
                    raise ValueError('new start requires a VNext request; V1 is read-only LEGACY_COMPAT')
                request.pop('schema_version',None)
                request.setdefault('run_id',request.get('change_id'))
            from .dev_vnext_runtime import DevRuntime
            runtime = DevRuntime(args.project_root,**context)
            if args.command == 'start':
                result = runtime.start(request)
            else:
                # Gap recovery validates old persisted integrity and authenticates
                # the replacement; the previous Human approval may be revoked.
                runtime.load(args.run_id,validate=args.command != 'resume-gap')
                simple = {'validate-authority':'validate_authority','implementation-ready':'implementation_ready',
                    'begin-implementation':'begin_implementation','verify':'verify','status':'status',
                    'replan':'replan','begin-fix-wave':'begin_fix_wave','impact-template':'impact_template','technical-gate-required':'technical_gate_required'}
                if args.command in simple:
                    result = getattr(runtime,simple[args.command])()
                    if args.command == 'technical-gate-required': result = {'required':result}
                elif args.command in ('impact','raise-gap','bind-technical-approval','escalate-risk'):
                    result = getattr(runtime,args.command.replace('-','_'))(read_json(args.artifact))
                elif args.command == 'resume-gap':
                    result = runtime.resume_gap(read_json(args.replacement_ref),read_json(args.resolution_ref))
                elif args.command == 'plan':
                    decisions = [read_json(p) for p in args.decision_ref]
                    if args.decision_refs: decisions += read_json(args.decision_refs)
                    result = runtime.plan(args.plan,args.tasks,decisions=decisions,revision=args.revision)
                elif args.command in ('authorize-write','write-source'):
                    if args.command == 'authorize-write': result = runtime.authorize_write(args.repository_id,args.path)
                    else: result = runtime.write_source(args.repository_id,args.path,args.content.read_bytes())
                elif args.command == 'review':
                    result = runtime.record_review([read_json(p) for p in args.evidence_ref],
                        blocking_findings=read_json(args.findings) if args.findings else (),kind=args.kind,
                        what_gap=read_json(args.what_gap) if args.what_gap else None)
                elif args.command == 'complete-fix-wave':
                    result = runtime.complete_fix_wave([read_json(p) for p in args.evidence_ref])
                elif args.command == 'maintenance-discovery':
                    result = runtime.discover_maintenance_change(read_json(args.changes))
                elif args.command in ('finalize','handoff'):
                    result = runtime.finalize(read_json(args.coverage),known_risks=read_json(args.known_risks) if args.known_risks else ())
                elif args.command == 'spec-kit':
                    from .dev_vnext_spec_kit import SpecKitAdapter
                    adapter = SpecKitAdapter(args.project_root,[args.executable])
                    if args.action == 'observe':
                        if not args.state_ref or not args.workflow_run_id: raise ValueError('observe requires exact state-ref and workflow-run-id')
                        result = adapter.observe(runtime,read_json(args.state_ref),args.workflow_run_id)
                    else:
                        result = adapter.execute_runtime(runtime,args.action,args.workflow_run_id,
                            devkit_command=args.devkit_command,technical_receipt_ref=args.technical_receipt_ref,integration=args.integration,host=args.host or '',choice=args.choice)
                else:
                    raise ValueError(f'unsupported VNext command: {args.command}')
        print(json.dumps(result,indent=2,ensure_ascii=False))
        outcome = result.get('status',result.get('lifecycle',result.get('state'))) if isinstance(result,dict) else None
        if isinstance(outcome,dict): outcome = outcome.get('lifecycle')
        if isinstance(result,dict) and 'checks' in result and any(row.get('status')=='FAIL' for row in result['checks']): return 1
        return 1 if outcome in ('FAIL','BLOCKED','UPSTREAM_GAP','NEEDS_REPLAN') else 0
    except (OSError,ValueError,KeyError,TypeError,ImportError) as error:
        print(f'ERROR: {error}',file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
