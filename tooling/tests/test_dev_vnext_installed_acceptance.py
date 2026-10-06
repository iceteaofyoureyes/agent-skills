"""Fresh install acceptance; the synthetic Human host is test infrastructure."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tooling import install_dev_kit
from tooling.tests import test_dev_vnext_runtime_acceptance as runtime_fixtures


ROOT = Path(__file__).resolve().parents[2]


def _launcher_command(installed, *args):
    launcher = Path(installed["launcher"])
    if os.name == "nt":
        return ["powershell", "-NoProfile", "-File", str(launcher), *map(str, args)]
    return [str(launcher), *map(str, args)]


def _tree_bytes(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*") if path.is_file()
    }


DRIVER = r'''import copy, hashlib, importlib, json, os, pathlib, subprocess, sys
runtime_root=pathlib.Path(sys.argv[1]).resolve()
project=pathlib.Path(sys.argv[2]).resolve()
source_root=pathlib.Path(sys.argv[3]).resolve()
assert sys.flags.isolated == 1
assert 'PYTHONPATH' not in os.environ
assert not project.is_relative_to(source_root)
sys.path.insert(0,str(runtime_root))
from tooling.lib import dev_vnext as dev
from tooling.lib.dev_vnext_runtime import DevRuntime
from shared.sdlc.foundation.impact import knowledge_impact
modules=('tooling.lib.dev_kit','tooling.lib.dev_router','tooling.lib.dev_vnext',
    'tooling.lib.dev_vnext_runtime','tooling.lib.dev_vnext_cli','tooling.lib.dev_vnext_spec_kit',
    'ba_contracts','ba_vnext','contracts','approved_baseline','shared.sdlc.schema',
    'shared.sdlc.authority.approved_baseline','shared.sdlc.foundation.contract',
    'shared.sdlc.foundation.impact','shared.sdlc.foundation.inventory',
    'shared.sdlc.foundation.profiles','shared.sdlc.foundation.workflow','shared.sdlc.foundation.producers')
loaded={name:importlib.import_module(name) for name in modules}
for name,module in loaded.items():
    path=pathlib.Path(module.__file__).resolve()
    assert path.is_relative_to(runtime_root),(name,path,runtime_root)

def ref(path,revision='FIXTURE-1'):
    data=(project/path).read_bytes()
    return {'path':path,'revision':revision,'sha256':hashlib.sha256(data).hexdigest()}

request=json.loads((project/'start-request.json').read_text(encoding='utf-8'))
upstream=json.loads((project/request['upstream']['path']).read_text(encoding='utf-8'))
receipt_ref=upstream['approval_receipt']
receipt=json.loads((project/receipt_ref['path']).read_text(encoding='utf-8'))
ba_auth=lambda actor,row: actor==receipt['actor_id'] and row==receipt
protected={item['path']:(project/item['path']).read_bytes() for item in dev._all_refs(upstream)}
protected[request['upstream']['path']]=(project/request['upstream']['path']).read_bytes()
repo=pathlib.Path(request['repository_roots']['core'])
runtime=DevRuntime(project,ba_authenticator=ba_auth)
state=runtime.start(request)
assert state['lifecycle']=='INTAKE'
state=runtime.validate_authority()
assert state['lifecycle']=='AUTHORITY_VALIDATED'
assert dev.read_upstream(state['upstream'],project,ba_authenticator=ba_auth)['vnext_authority'] is True
impact={'schema_version':2,'change_id':state['change_id'],'upstream_ref':state['upstream'],
    'repository_base_revisions':{row['id']:row['base_revision'] for row in state['repositories']},
    'affected_repositories':copy.deepcopy(state['repositories']),
    'affected_components':['neutral module'],'affected_interfaces':[],'affected_data':[],
    'dependencies':[],'constraints':[],'risk':copy.deepcopy(state['risk']),
    'technical_unknowns':[],'upstream_gaps':[],
    'write_scope':{row['id']:row['allowed_write_paths'] for row in state['repositories']},
    'knowledge_impact':copy.deepcopy(upstream['knowledge_impact'])}
state=runtime.impact(impact)
assert state['lifecycle']=='IMPACT_ANALYZED'
(project/'installed-plan.md').write_text('Neutral technical plan bound to exact runtime snapshot.\n',encoding='utf-8')
(project/'installed-tasks.md').write_text('Implement one neutral module change and verify it.\n',encoding='utf-8')
state=runtime.plan('installed-plan.md','installed-tasks.md',revision='INSTALLED-TECH-1')
assert state['lifecycle']=='TECHNICAL_PLANNED'
assert state['risk']['level']=='NORMAL'
assert runtime.technical_gate_required() is False
state=runtime.implementation_ready()
assert state['lifecycle']=='IMPLEMENTATION_READY'
runtime.begin_implementation()
runtime.write_source('core','src/module.py','def result():\n    return 2\n')
subprocess.run(['git','add','src/module.py'],cwd=repo,check=True)
subprocess.run(['git','commit','--quiet','-m','Neutral installed implementation'],cwd=repo,check=True)
review=ref('review-evidence.json')
runtime.record_review([review])
verification=runtime.verify()
assert verification['checks'] and all(row['status']=='PASS' and row['exit_code']==0 for row in verification['checks'])
coverage=[{'id':identity,'status':'COVERED',
    'code_refs':[ref('repositories/core/src/module.py')],
    'test_refs':[ref('repositories/core/tests/check_native.py')]} for identity in ('BR-001','FR-001')]
handoff=runtime.finalize(coverage)
assert handoff['artifact_class']=='HANDOFF_MANIFEST'
assert handoff['state']=='READY_FOR_TEST'
assert [row['id'] for row in handoff['requirements_coverage']]==['BR-001','FR-001']
assert not handoff.get('verified')
assert not any(row.get('status')=='VERIFIED' for row in handoff.get('engineering_verification',{}).get('checks',[]))
assert {row['repository_id'] for row in handoff['engineering_verification']['checks']}=={'core'}
assert all(before==(project/path).read_bytes() for path,before in protected.items())

reloaded=DevRuntime(project,ba_authenticator=ba_auth)
assert reloaded.load()['lifecycle']=='READY_FOR_TEST'
saved=project/'.devkit/runs/RUN-1/dev-handoff.json'
again=json.loads(saved.read_text(encoding='utf-8'))
bases={row['id']:row['base_revision'] for row in reloaded.state['repositories']}
assert dev.validate_handoff(again,project,current_base_revisions=bases,ba_authenticator=ba_auth)['state']=='READY_FOR_TEST'

# A V1 handoff remains inspectable but never gains VNext authority.
legacy=json.loads((project/'legacy-v1-handoff.json').read_text(encoding='utf-8'))
legacy_result=dev.read_artifact(legacy,'handoff',project)
assert legacy_result['mode']=='LEGACY_COMPAT' and legacy_result['vnext_authority'] is False

# The installed HIGH_RISK path refuses implementation without a trusted receipt.
high=copy.deepcopy(request)
high.update(run_id='RUN-HIGH-RISK',risk={'level':'HIGH_RISK','categories':['PUBLIC_API'],'reasons':['public boundary']})
for row in high['repositories']:
    row['base_revision']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=request['repository_roots'][row['id']],text=True).strip()
high_state=runtime.start(high)
high_state=runtime.validate_authority()
high_impact=copy.deepcopy(impact)
high_impact.update(change_id=high_state['change_id'],upstream_ref=high_state['upstream'],
    repository_base_revisions={row['id']:row['base_revision'] for row in high_state['repositories']},
    affected_repositories=copy.deepcopy(high_state['repositories']),risk=copy.deepcopy(high_state['risk']),
    write_scope={row['id']:row['allowed_write_paths'] for row in high_state['repositories']})
high_state=runtime.impact(high_impact)
high_state=runtime.plan('installed-plan.md','installed-tasks.md',revision='INSTALLED-HIGH-1')
assert runtime.technical_gate_required() is True
try:
    runtime.implementation_ready()
except ValueError:
    pass
else:
    raise AssertionError('HIGH_RISK reached IMPLEMENTATION_READY without authenticated technical approval')
assert runtime.load('RUN-HIGH-RISK')['lifecycle']=='TECHNICAL_PLANNED'
print('FRESH_INSTALLED_DEV_VNEXT_PASS')
'''


class InstalledDevVNextAcceptance(unittest.TestCase):
    def test_fresh_install_doctor_isolation_flow_and_high_risk_gate(self):
        with tempfile.TemporaryDirectory(prefix="dev-vnext-installed-") as temporary:
            temporary = Path(temporary)
            fixture = runtime_fixtures.RuntimeAcceptanceTests("test_normal_full_runtime_path_keeps_ba_authority_bytes_unchanged")
            fixture.setUp()
            self.addCleanup(fixture.doCleanups)
            project = fixture.root.resolve()
            (project / "AGENTS.md").write_text("Neutral synthetic repository instructions.\n", encoding="utf-8")
            (project / "unrelated.txt").write_text("preserve me\n", encoding="utf-8")
            request = fixture.request(run_id="RUN-1")
            request["checks"] = [
                {**row, "command": [sys.executable, "-I", *row["command"][1:]]}
                for row in request["checks"]
            ]
            (project / "start-request.json").write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
            legacy = json.loads((ROOT / "tooling/tests/fixtures/dev/dev-handoff.valid.json").read_text(encoding="utf-8"))
            (project / "legacy-v1-handoff.json").write_text(json.dumps(legacy), encoding="utf-8")

            install_home = temporary / "developer-home" / ".devkit"
            (install_home / "runtime/v1").mkdir(parents=True)
            (install_home / "runtime/v1/preserved-v1.txt").write_text("keep V1\n", encoding="utf-8")
            (install_home / "bin").mkdir(parents=True)
            (install_home / "bin/preserved-user-tool.txt").write_text("keep unrelated\n", encoding="utf-8")
            installed = install_dev_kit.install(ROOT, install_home)
            runtime_root = Path(installed["runtime_root"]).resolve()
            self.assertEqual(runtime_root, (install_home / "runtime/v2").resolve())
            self.assertTrue((install_home / "runtime/v1/preserved-v1.txt").is_file())
            self.assertEqual((install_home / "bin/preserved-user-tool.txt").read_text(encoding="utf-8"), "keep unrelated\n")
            manifest = json.loads(Path(installed["manifest"]).read_text(encoding="utf-8"))
            self.assertEqual((manifest["schema_version"], manifest["runtime"]), (2, "dev-kit-v2"))
            self.assertEqual(manifest["kit_version"], "0.4.0-rc.3")
            self.assertEqual(len(manifest["files"]), installed["file_count"])
            before = _tree_bytes(runtime_root)
            repeated = install_dev_kit.install(ROOT, install_home)
            self.assertEqual(before, _tree_bytes(runtime_root))
            self.assertEqual(Path(repeated["runtime_root"]).resolve(), runtime_root)

            if os.name == "nt":
                specify = temporary / "specify.cmd"
                specify.write_text("@echo off\r\necho specify version 1.0.11\r\n", encoding="utf-8")
            else:
                specify = temporary / "specify"
                specify.write_text("#!/bin/sh\necho specify version 1.0.11\n", encoding="utf-8")
                specify.chmod(0o755)
            env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
            env.pop("PYTHONHOME", None)
            doctor = subprocess.run(
                _launcher_command(installed, "doctor", "--json", "--spec-kit-cli", specify),
                cwd=project, env=env, capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(doctor.returncode, 0, doctor.stderr + doctor.stdout)
            report = json.loads(doctor.stdout)
            self.assertEqual(report["status"], "READY")
            self.assertEqual(report["readiness_scope"], "PACKAGE/CAPABILITY READY")
            self.assertNotIn("feature_state", report)
            self.assertNotIn("approval", report)
            self.assertTrue(all(Path(path).resolve().is_relative_to(runtime_root) for path in report["module_paths"].values()))

            runtime_root_result = subprocess.run(
                _launcher_command(installed, "runtime-root"), cwd=project, env=env,
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(runtime_root_result.returncode, 0, runtime_root_result.stderr)
            self.assertEqual(Path(runtime_root_result.stdout.strip()).resolve(), runtime_root)
            schema = subprocess.run(
                _launcher_command(installed, "schema", "start-request"), cwd=project, env=env,
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(schema.returncode, 0, schema.stderr)
            self.assertIn("authority_mode", json.loads(schema.stdout)["required"])
            legacy_schema = subprocess.run(
                _launcher_command(installed, "schema", "legacy/start-request"), cwd=project, env=env,
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(legacy_schema.returncode, 0, legacy_schema.stderr)
            self.assertEqual(json.loads(legacy_schema.stdout)["properties"]["schema_version"]["const"], 1)
            template = subprocess.run(
                _launcher_command(installed, "template", "technical-approval"), cwd=project, env=env,
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(template.returncode, 0, template.stderr)
            self.assertIn("does not approve a change", template.stdout)

            driver = temporary / "installed-flow.py"
            driver.write_text(DRIVER, encoding="utf-8")
            flow = subprocess.run(
                [sys.executable, "-I", str(driver), str(runtime_root), str(project), str(ROOT)],
                cwd=project, env=env, capture_output=True, text=True, timeout=180,
            )
            self.assertEqual(flow.returncode, 0, flow.stderr + flow.stdout)
            self.assertIn("FRESH_INSTALLED_DEV_VNEXT_PASS", flow.stdout)
            self.assertEqual((project / "unrelated.txt").read_text(encoding="utf-8"), "preserve me\n")

            repeated_doctor = subprocess.run(
                _launcher_command(installed, "doctor", "--json", "--spec-kit-cli", specify),
                cwd=project, env=env, capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(repeated_doctor.returncode, 0, repeated_doctor.stderr + repeated_doctor.stdout)
            self.assertEqual(json.loads(repeated_doctor.stdout)["status"], "READY")


if __name__ == "__main__":
    unittest.main()
