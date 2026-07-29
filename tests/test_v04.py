from pathlib import Path
import json
import tempfile
import unittest

from oriel.modules import load_module_graph, ModuleError
from oriel.api_framework import create_api_project, route_manifest
from oriel import package_manager
from oriel.lsp import declaration, locations


class V04Tests(unittest.TestCase):
    def test_module_graph(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'src').mkdir()
            (root / 'oriel.toml').write_text(
                '[project]\nname="x"\nversion="0.1.0"\n'
                'entry="src/main.orl"\n[dependencies]\n',
                encoding='utf-8',
            )
            (root / 'src' / 'util.orl').write_text(
                'fn twice(x: Int) -> Int { return x * 2 }', encoding='utf-8'
            )
            entry = root / 'src' / 'main.orl'
            entry.write_text(
                'use util\nfn main() { print(twice(3)) }', encoding='utf-8'
            )
            source, files = load_module_graph(entry)
            self.assertIn('fn twice', source)
            self.assertEqual(len(files), 2)

    def test_circular_import_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'src').mkdir()
            (root / 'oriel.toml').write_text(
                '[project]\nname="cycle"\nversion="0.1.0"\n'
                'entry="src/a.orl"\n[dependencies]\n',
                encoding='utf-8',
            )
            (root / 'src' / 'a.orl').write_text('use b\nfn a() {}', encoding='utf-8')
            (root / 'src' / 'b.orl').write_text('use a\nfn b() {}', encoding='utf-8')
            with self.assertRaises(ModuleError) as context:
                load_module_graph(root / 'src' / 'a.orl')
            self.assertIn('Circular module import detected', str(context.exception))

    def test_api_project_and_routes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_api_project('demo-api', Path(directory))
            routes = route_manifest((root / 'src/main.orl').read_text(encoding='utf-8'))
            self.assertEqual(routes[0]['method'], 'GET')
            self.assertTrue(any(route['path'] == '/health' for route in routes))

    def test_transitive_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'oriel.toml').write_text(
                '[project]\nname="x"\nversion="0.1.0"\n'
                'entry="src/main.orl"\n\n[dependencies]\n'
                '"oriel.api"="^0.1.0"\n',
                encoding='utf-8',
            )
            self.assertEqual(package_manager.install(root), 3)
            lock = json.loads((root / 'oriel.lock').read_text(encoding='utf-8'))
            self.assertEqual(lock['lock_version'], 2)
            self.assertEqual(
                {package['name'] for package in lock['packages']},
                {'oriel.api', 'oriel.core', 'oriel.json'},
            )

    def test_lsp_navigation_foundations(self):
        source = 'fn add(a: Int, b: Int) -> Int { return a + b }\nfn main() { print(add(2, 3)) }'
        definition = declaration(source, 'add')
        self.assertIsNotNone(definition)
        self.assertEqual(definition['line'], 0)
        self.assertEqual(len(locations('file:///main.orl', source, 'add')), 2)


if __name__ == '__main__':
    unittest.main()
