from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
NEXT_VERSION_SCRIPT = ROOT / "scripts" / "next_version.py"


def git(repo, *arguments):
    return subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


class ReleaseVersionTests(unittest.TestCase):
    def test_version_at_v0_1_2_tagged_head_reports_0_1_2(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            git(repo, "init", "--quiet")
            git(repo, "config", "user.name", "Test User")
            git(repo, "config", "user.email", "test@example.com")
            marker = repo / "marker"
            marker.write_text("release\n", encoding="utf-8")
            git(repo, "add", "marker")
            git(repo, "commit", "--quiet", "-m", "Release")
            git(repo, "tag", "v0.1.2")

            result = subprocess.run(
                [sys.executable, NEXT_VERSION_SCRIPT],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.stdout.strip(), "0.1.2")

    def test_next_version_increments_latest_stable_v0_1_2_tag_to_0_1_3(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            git(repo, "init", "--quiet")
            git(repo, "config", "user.name", "Test User")
            git(repo, "config", "user.email", "test@example.com")
            marker = repo / "marker"
            marker.write_text("release\n", encoding="utf-8")
            git(repo, "add", "marker")
            git(repo, "commit", "--quiet", "-m", "Release")
            git(repo, "tag", "v0.1.2")
            git(repo, "tag", "v9.9.9-rc1")
            marker.write_text("next\n", encoding="utf-8")
            git(repo, "commit", "--quiet", "-am", "Next")

            result = subprocess.run(
                [sys.executable, NEXT_VERSION_SCRIPT],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.stdout.strip(), "0.1.3")

    def test_release_workflow_tags_merged_master_commits_automatically(self):
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )

        self.assertRegex(
            workflow,
            r"(?ms)^on:\s*\n\s+pull_request:\s*\n\s+branches:\s*\n\s+- master",
        )
        self.assertIn("github.event.pull_request.merged == true", workflow)
        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn("python scripts/next_version.py", workflow)
        self.assertIn('git tag -a "$TAG"', workflow)
        self.assertIn('git push origin "$TAG"', workflow)

    def test_release_workflow_pushes_semver_and_latest_images_with_same_build_version(
        self,
    ):
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("tag: ${{ steps.version.outputs.tag }}", workflow)
        self.assertRegex(workflow, r"(?m)^\s+needs:\s+version\s*$")
        self.assertIn(
            "RELEASE_TAG: ${{ needs.version.outputs.tag }}",
            workflow,
        )
        self.assertIn(
            "GAME_VERSION=${{ env.RELEASE_TAG }}",
            workflow,
        )
        self.assertIn("IMAGE: ghcr.io/simonborin/trek_bot", workflow)
        self.assertIn("${{ env.IMAGE }}:${{ env.RELEASE_TAG }}", workflow)
        self.assertIn("${{ env.IMAGE }}:latest", workflow)
        self.assertIn("ref: ${{ env.RELEASE_TAG }}", workflow)
        self.assertRegex(workflow, r"(?m)^\s+push:\s+true\s*$")

    def test_dockerfile_promotes_build_version_to_runtime_environment(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

        self.assertRegex(
            dockerfile,
            r"(?m)^ARG GAME_VERSION(?:=[^\s]+)?\s*$",
        )
        self.assertRegex(
            dockerfile,
            (
                r"(?m)^ENV GAME_VERSION="
                r"[\"']?(?:\$\{GAME_VERSION\}|\$GAME_VERSION)[\"']?\s*$"
            ),
        )
