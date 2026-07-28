import tempfile
import unittest
from pathlib import Path

from oriel.cli import build_project, check_source, create_project, format_paths


class CLIPackageTests(unittest.TestCase):
    def test_check(self):
        check_source('fn main() { print("Hello") }')

    def test_new_format_and_build(self):
        with tempfile.TemporaryDirectory() as folder:
            project = create_project("demo", Path(folder))
            main = project / "main.orl"
            main.write_text('fn main() {  \n\tprint("Hello")  \n}\n\n', encoding="utf-8")
            self.assertEqual(format_paths([main]), 1)
            formatted = main.read_text(encoding="utf-8")
            self.assertNotIn("\t", formatted)
            self.assertTrue(formatted.endswith("\n"))
            archive = build_project(project)
            self.assertTrue(archive.exists())


if __name__ == "__main__":
    unittest.main()
