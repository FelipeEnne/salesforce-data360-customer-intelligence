import re
import unittest
from pathlib import Path
from urllib.parse import unquote


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"!?(?:\[[^]]*\])\(([^)]+)\)")


class DocumentationLinkTests(unittest.TestCase):
    def test_local_markdown_links_resolve(self):
        broken_links = []

        markdown_files = [PROJECT_ROOT / "README.md"]
        markdown_files.extend(sorted((PROJECT_ROOT / "docs").glob("*.md")))

        for document in markdown_files:
            content = document.read_text(encoding="utf-8")

            for raw_target in MARKDOWN_LINK.findall(content):
                target = raw_target.split(maxsplit=1)[0].strip("<>")

                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue

                relative_path = unquote(target.split("#", maxsplit=1)[0])
                destination = (document.parent / relative_path).resolve()

                if not destination.exists():
                    broken_links.append(
                        f"{document.relative_to(PROJECT_ROOT)} -> {target}"
                    )

        self.assertEqual(broken_links, [], "Broken local links found")


if __name__ == "__main__":
    unittest.main()
