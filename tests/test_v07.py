from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest

from oriel.console_tools import benchmark, compile_bytecode, doctor, generate_docs, run_bytecode, write_bytecode

SOURCE = 'fn main() { print("hello") }'

class ConsoleFoundationTests(unittest.TestCase):
    def test_bytecode_compile_write_and_execute(self):
        payload = compile_bytecode(SOURCE, "main.orl")
        self.assertEqual(payload["magic"], "ORIELBC1")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "main.orl"
            source.write_text(SOURCE, encoding="utf-8")
            bytecode = write_bytecode(source)
            self.assertTrue(bytecode.exists())
            output = StringIO()
            with redirect_stdout(output):
                run_bytecode(bytecode)
            self.assertIn("hello", output.getvalue())

    def test_documentation_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "main.orl"
            output = root / "API.md"
            source.write_text("fn add(a: Int, b: Int) -> Int { return a + b }", encoding="utf-8")
            generate_docs(source, output)
            self.assertIn("`add(a: Int, b: Int)`", output.read_text(encoding="utf-8"))

    def test_doctor_environment_report(self):
        report = doctor()
        self.assertEqual(report["oriel"], "ok")
        self.assertIn("python", report)
        self.assertIn("platform", report)
        self.assertIsInstance(report["write_access"], bool)

    def test_benchmark_stability(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "main.orl"
            source.write_text(SOURCE, encoding="utf-8")
            result = benchmark(source, iterations=2)
            self.assertEqual(result["iterations"], 2)
            self.assertGreaterEqual(result["min_ms"], 0)
            self.assertGreaterEqual(result["max_ms"], result["min_ms"])

if __name__ == "__main__":
    unittest.main()
