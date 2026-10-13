#!/usr/bin/env python3
"""Install only SC-specific overlay files into a clone of the upstream GitHub fork.

This preserves the fork's README, LICENSE, original code and workflows.
"""
from pathlib import Path
import argparse
import shutil

FILES = (
    '.github/workflows/sc-autobuild.yml',
    'sc/adapt.py',
    'sc/discover.py',
    'sc/verify.py',
    'sc/install_into_fork.py',
    'tests/test_overlay.py',
    'LICENSE-AUTOMATION',
)


def install(overlay: Path, fork: Path) -> list[str]:
    overlay = overlay.resolve()
    fork = fork.resolve()
    if not (fork / '.git').exists():
        raise ValueError(f'Not a local Git repository: {fork}')
    if not (fork / 'build.py').is_file() or not (fork / 'config.yaml').is_file():
        raise ValueError(f'Not an existing upstream TC project fork: {fork}')
    for path in FILES:
        if not (overlay / path).is_file():
            raise FileNotFoundError(f'Overlay file is missing: {overlay / path}')
    for path in FILES:
        target = fork / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(overlay / path, target)
    shutil.copy2(overlay / 'README.md', fork / 'SC_README.md')
    shutil.copy2(overlay / 'SETUP_SC_CN.md', fork / 'SETUP_SC_CN.md')
    return list(FILES) + ['SC_README.md', 'SETUP_SC_CN.md']


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fork', type=Path, help='Path to cloned original GitHub fork')
    args = parser.parse_args()
    changed = install(Path(__file__).resolve().parents[1], args.fork)
    print('Installed SC overlay without overwriting original LICENSE/README:')
    for path in changed:
        print('  ' + path)


if __name__ == '__main__':
    main()
