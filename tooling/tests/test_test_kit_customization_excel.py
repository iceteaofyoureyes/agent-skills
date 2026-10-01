"""Project-profile selection uses the existing Excel projection contract."""

import json
import shutil
from pathlib import Path

import pytest

from tooling.lib import test_kit_v1_excel as excel
from tooling.tests.test_test_kit_v1_excel import BASELINE, DESIGN, TEMPLATE, TESTWARE


def project(tmp_path, template=True):
    root = tmp_path / 'project'
    policy_root = root / '.test-kit'
    policy_root.mkdir(parents=True)
    if template:
        path = policy_root / 'templates/testcases.xlsx'
        path.parent.mkdir()
        shutil.copyfile(TEMPLATE, path)
    profile = (
        'schema_version: 1\nprofile:\n  id: portal-testing\n  revision: "1"\n'
        'rules:\n  common: []\n  test_design: []\n  testcases: []\n'
        + ('templates:\n  excel:\n    path: templates/testcases.xlsx\n' if template else 'templates: {}\n')
    )
    (policy_root / 'project.yaml').write_text(profile, encoding='utf-8')
    return root


@pytest.mark.parametrize('human,configured,expected', [
    (True, True, 'HUMAN_SUPPLIED_APPROVED_TEMPLATE'),
    (False, True, 'PROJECT_TEMPLATE'),
    (False, False, 'DEFAULT_TEMPLATE'),
])
def test_profile_template_precedence(tmp_path, human, configured, expected):
    root = project(tmp_path, configured)
    result = excel.export_test_only_approved_testware_excel(
        TESTWARE, DESIGN, BASELINE, tmp_path / 'output',
        project_root=root, template_path=TEMPLATE if human else None,
    )
    assert json.loads(result.manifest_path.read_text(encoding='utf-8'))['template_source'] == expected
    assert result.semantic_diff.status == 'PASS'


def test_invalid_selected_project_template_fails_without_default(tmp_path):
    root = project(tmp_path)
    (root / '.test-kit/templates/testcases.xlsx').write_bytes(b'invalid workbook')
    with pytest.raises(excel.ExcelProjectionError) as failure:
        excel.export_test_only_approved_testware_excel(
            TESTWARE, DESIGN, BASELINE, tmp_path / 'output', project_root=root,
        )
    assert failure.value.code == 'CANNOT_PROJECT_TEMPLATE'
    assert not (tmp_path / 'output').exists()


def test_human_template_wins_over_invalid_project_workbook(tmp_path):
    root = project(tmp_path)
    (root / '.test-kit/templates/testcases.xlsx').write_bytes(b'invalid workbook')
    result = excel.export_test_only_approved_testware_excel(
        TESTWARE, DESIGN, BASELINE, tmp_path / 'output',
        project_root=root, template_path=TEMPLATE,
    )
    assert json.loads(result.manifest_path.read_text(encoding='utf-8'))['template_source'] == 'HUMAN_SUPPLIED_APPROVED_TEMPLATE'


def test_missing_selected_project_template_fails_closed(tmp_path):
    root = project(tmp_path)
    (root / '.test-kit/templates/testcases.xlsx').unlink()
    with pytest.raises(excel.ExcelProjectionError) as failure:
        excel.export_test_only_approved_testware_excel(
            TESTWARE, DESIGN, BASELINE, tmp_path / 'output', project_root=root,
        )
    assert failure.value.code == 'CANNOT_PROJECT_TEMPLATE'
