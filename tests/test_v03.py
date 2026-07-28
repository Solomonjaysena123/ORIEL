from pathlib import Path
import json
import tempfile
import unittest
from oriel.interpreter import Lexer, Parser, TypeChecker, OrielError, run_source
from oriel import package_manager


def check(src):
    statements = Parser(Lexer(src).scan_tokens()).parse()
    TypeChecker().check(statements)


class V03Tests(unittest.TestCase):
    def test_typed_program_runs(self):
        out = []
        run_source(
            'fn add(a: Int, b: Int) -> Int { return a + b }\n'
            'fn main() { let total: Int = add(2, 3)\nprint(total) }',
            output=out.append,
        )
        self.assertEqual(out, ['5'])

    def test_type_mismatch_has_code(self):
        with self.assertRaises(OrielError) as context:
            check('fn main() { let quantity: Int = "ten" }')
        self.assertEqual(context.exception.code, 'E202')

    def test_package_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / 'oriel.toml').write_text(
                '[project]\nname="x"\nversion="0.1.0"\n'
                'entry="src/main.orl"\n\n[dependencies]\n',
                encoding='utf-8',
            )
            package_manager.add(project, 'oriel.text')
            lock = json.loads((project / 'oriel.lock').read_text())
            self.assertEqual(lock['packages'][0]['name'], 'oriel.text')
            package_manager.remove(project, 'oriel.text')


if __name__ == '__main__':
    unittest.main()
