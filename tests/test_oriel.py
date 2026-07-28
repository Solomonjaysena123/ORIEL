import tempfile
import unittest
from pathlib import Path

from oriel.interpreter import run_source


class OrielTests(unittest.TestCase):
    def execute(self, source: str):
        output = []
        run_source(source, output=output.append)
        return output

    def test_arithmetic_function_and_while(self):
        source = """
        fn add(a, b) { return a + b }
        fn main() {
            var x = 1
            while x <= 2 {
                print(add(x, 10))
                x = x + 1
            }
        }
        """
        self.assertEqual(self.execute(source), ["11", "12"])

    def test_immutable_assignment_fails(self):
        with self.assertRaises(RuntimeError):
            self.execute("fn main() { let x = 1 x = 2 }")

    def test_lists_indexing_and_for_loop(self):
        source = """
        fn main() {
            var values = [2, 4, 6]
            values[1] = 5
            for value in values { print(value) }
            print(values[-1])
            print(length(values))
        }
        """
        self.assertEqual(self.execute(source), ["2", "5", "6", "6", "3"])

    def test_json_round_trip(self):
        source = """
        fn main() {
            let encoded = json_encode([1, 2, 3])
            let decoded = json_decode(encoded)
            print(decoded[1])
        }
        """
        self.assertEqual(self.execute(source), ["2"])

    def test_file_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            target = (Path(folder) / "note.txt").as_posix()
            source = f"""
            fn main() {{
                write_file("{target}", "hello")
                print(read_file("{target}"))
            }}
            """
            self.assertEqual(self.execute(source), ["hello"])


if __name__ == "__main__":
    unittest.main()
