"""A new spec path remains a first addition when Git detects a rename."""
import importlib.util
import pathlib
import subprocess
import tempfile
import unittest
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_evidence_tiers as AUDIT
SPEC = importlib.util.spec_from_file_location(
    "preregistration", ROOT / "scripts/check_preregistration.py")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PreregPathBirth(unittest.TestCase):
    def test_rename_like_supersession_has_new_path_birth(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = pathlib.Path(directory)
            def git(*args):
                return subprocess.check_output(["git", *args], cwd=repo).decode().strip()
            git("init", "-q")
            git("config", "user.name", "Test")
            git("config", "user.email", "test@example.invalid")
            (repo / "hypotheses" / "growth").mkdir(parents=True)
            old = repo / "hypotheses/growth/old_case.yaml"
            new = repo / "hypotheses/growth/new_case.yaml"
            old.write_text("claim: " + "a repeated preregistered claim " * 30 + "\n")
            git("add", ".")
            git("commit", "-qm", "old registration")
            first_commit = git("rev-parse", "HEAD")
            new.write_text(old.read_text().replace("claim:", "claim: updated", 1))
            old.unlink()
            git("add", "-A")
            git("commit", "-qm", "supersede before any run")
            second_commit = git("rev-parse", "HEAD")
            self.assertIn("rename ", git("show", "--summary", "--format=", "HEAD"))
            previous_root = MODULE.ROOT
            try:
                MODULE.ROOT = repo
                paths, _ = MODULE.first_additions()
            finally:
                MODULE.ROOT = previous_root
            self.assertEqual(paths["hypotheses/growth/old_case.yaml"].commit, first_commit)
            self.assertEqual(paths["hypotheses/growth/new_case.yaml"].commit, second_commit)
            previous_audit_root = AUDIT.ROOT
            try:
                AUDIT.ROOT = repo
                self.assertEqual(
                    AUDIT.first_addition_commits("hypotheses/growth/old_case.yaml"),
                    [first_commit])
                self.assertEqual(
                    AUDIT.first_addition_commits("hypotheses/growth/new_case.yaml"),
                    [second_commit])
            finally:
                AUDIT.ROOT = previous_audit_root


if __name__ == "__main__":
    unittest.main()
