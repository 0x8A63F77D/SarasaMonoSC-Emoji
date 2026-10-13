#!/usr/bin/env python3
"""Adapt upstream SarasaMonoTC-Emoji source into an SC builder, without maintaining a forked merge engine.

Run from any directory: python sc/adapt.py /path/to/upstream-checkout
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

REPLACEMENTS = (
    ("SarasaMonoTC", "SarasaMonoSC"),
    ("Sarasa Mono TC", "Sarasa Mono SC"),
    ("sarasa-mono-tc", "sarasa-mono-sc"),
    ("traditional-chinese", "simplified-chinese"),
    ("Traditional Chinese", "Simplified Chinese"),
    ("繁體中文", "简体中文"),
    ("繁體", "简体"),
    ("繁中", "简中"),
)


def adapt(root: Path, repository: str = "") -> list[str]:
    root = root.resolve()
    mandatory = (root / "config.yaml", root / "build.py", root / "tests" / "conftest.py")
    for path in mandatory:
        if not path.is_file():
            raise FileNotFoundError(f"Not an upstream SarasaMonoTC-Emoji checkout: {path}")

    paths = [root / "build.py", root / "config.yaml", root / "pyproject.toml"]
    paths += sorted((root / "src").rglob("*.py"))
    paths += sorted((root / "tests").rglob("*.py"))
    changed = []
    for path in paths:
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        result = content
        for needle, replacement in REPLACEMENTS:
            result = result.replace(needle, replacement)
        if repository and path.name == "config.yaml":
            old = 'https://github.com/sspig0127/SarasaMonoSC-Emoji'
            result = result.replace(old, f'https://github.com/{repository}')
        if result != content:
            path.write_text(result, encoding="utf-8")
            changed.append(str(path.relative_to(root)))

    config = (root / "config.yaml").read_text(encoding="utf-8")
    tests = (root / "tests" / "conftest.py").read_text(encoding="utf-8")
    if ('base_font: "SarasaMonoSC-Regular.ttf"' not in config
            or 'family_name: "SarasaMonoSCEmoji"' not in config
            or 'SarasaMonoSC-Regular.ttf' not in tests):
        raise RuntimeError("Upstream config/fixtures changed; adjust sc/adapt.py before publishing")
    if "SarasaMonoTC" in config or "SarasaMonoTC" in tests:
        raise RuntimeError("A TC-specific source reference remains in critical SC build files")
    if not changed:
        raise RuntimeError("No substitutions applied: upstream layout likely changed")
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("upstream_dir", type=Path)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    args = parser.parse_args()
    changed = adapt(args.upstream_dir, args.repository)
    print(f"Adapted {len(changed)} upstream source files:")
    for path in changed:
        print(f"  {path}")


if __name__ == "__main__":
    main()
