"""Neutral multi-repository fixture routing contracts."""
import unittest

from tooling.tests.fixtures.public_cross_kit_conformance import repository_for_role


class TopologyResolutionTests(unittest.TestCase):
    def test_role_resolves_declared_repository_id_and_path(self):
        topology = {"repositories": [
            {"id": "docs-repo", "path": "project-docs", "role": "project_documentation_authority"},
            {"id": "app-repo", "path": "service-app", "role": "application_implementation"},
            {"id": "tests-repo", "path": "test-automation", "role": "project_test_automation"},
        ]}
        self.assertEqual(repository_for_role(topology, "application_implementation")["id"], "app-repo")

    def test_ambiguous_role_fails_closed(self):
        topology = {"repositories": [
            {"id": "tests-one", "path": "test-automation", "role": "project_test_automation"},
            {"id": "tests-two", "path": "alternate-tests", "role": "project_test_automation"},
        ]}
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            repository_for_role(topology, "project_test_automation")


if __name__ == "__main__":
    unittest.main()
