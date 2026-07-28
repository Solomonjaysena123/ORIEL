import unittest

from oriel.interpreter import run_source


class OrielTests(unittest.TestCase):
    def execute(self, source: str):
        output = []
        run_source(source, output=output.append)
        return output

    def test_arithmetic_and_precedence(self):
        self.assertEqual(
            self.execute("fn main() { print(2 + 3 * 4) }"),
            ["14"],
        )

    def test_function(self):
        source = """
        fn add(a, b) {
            return a + b
        }

        fn main() {
            print(add(10, 20))
        }
        """
        self.assertEqual(self.execute(source), ["30"])

    def test_while(self):
        source = """
        fn main() {
            var x = 1
            while x <= 3 {
                print(x)
                x = x + 1
            }
        }
        """
        self.assertEqual(self.execute(source), ["1", "2", "3"])

    def test_immutable_assignment_fails(self):
        source = """
        fn main() {
            let x = 1
            x = 2
        }
        """
        with self.assertRaises(RuntimeError):
            self.execute(source)


if __name__ == "__main__":
    unittest.main()
