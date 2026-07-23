
import tempfile
import unittest
from pathlib import Path

from oriel.cli import check_source, create_project
from oriel.interpreter import run_source


class CLIPackageTests(unittest.TestCase):
    def test_run(self):
        output = []
        run_source('fn main() { print("Hello") }', output=output.append)
        self.assertEqual(output, ["Hello"])

    def test_check(self):
        check_source('fn main() { print("Hello") }')

    def test_new_project(self):
        with tempfile.TemporaryDirectory() as folder:
            project = create_project("demo", Path(folder))
            self.assertTrue((project / "main.orl").exists())


if __name__ == "__main__":
    unittest.main()
