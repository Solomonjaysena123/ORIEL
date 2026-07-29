from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> None:
    print('+', ' '.join(args))
    subprocess.run(args, cwd=ROOT, check=True)


if __name__ == '__main__':
    run(sys.executable, '-m', 'pytest')
    run(sys.executable, '-m', 'build')
    print('Repository verification completed successfully.')
