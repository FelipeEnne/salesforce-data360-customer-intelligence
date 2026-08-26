import fnmatch
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAX_TRACKED_FILE_BYTES = 5 * 1024 * 1024
ALLOWED_ENV_FILES = {".env.example"}
FORBIDDEN_NAMES = {
    "credentials.json",
    "id_ed25519",
    "id_rsa",
    "kaggle.json",
}
FORBIDDEN_PATTERNS = (
    "*credentials*.json",
    "*secret*.json",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*.jks",
    "*.ppk",
)


def tracked_files():
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
    )
    return [
        PROJECT_ROOT / path.decode("utf-8")
        for path in result.stdout.split(b"\0")
        if path
    ]


class RepositoryHygieneTests(unittest.TestCase):
    def test_no_sensitive_filenames_are_tracked(self):
        violations = []

        for path in tracked_files():
            relative_path = path.relative_to(PROJECT_ROOT).as_posix()
            filename = path.name.lower()

            if filename.startswith(".env") and filename not in ALLOWED_ENV_FILES:
                violations.append(relative_path)
            elif filename in FORBIDDEN_NAMES:
                violations.append(relative_path)
            elif any(fnmatch.fnmatch(filename, pattern) for pattern in FORBIDDEN_PATTERNS):
                violations.append(relative_path)

        self.assertEqual(violations, [], "Sensitive filenames are tracked")

    def test_generated_csv_files_are_not_tracked(self):
        violations = [
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in tracked_files()
            if path.suffix.lower() == ".csv"
            and "tests/fixtures" not in path.relative_to(PROJECT_ROOT).as_posix()
        ]

        self.assertEqual(violations, [], "Generated CSV files are tracked")

    def test_tracked_files_stay_below_size_limit(self):
        oversized = [
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in tracked_files()
            if path.stat().st_size > MAX_TRACKED_FILE_BYTES
        ]

        self.assertEqual(oversized, [], "Oversized files are tracked")


if __name__ == "__main__":
    unittest.main()
