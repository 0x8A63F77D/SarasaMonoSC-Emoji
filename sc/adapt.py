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



def patch_color_collisions(path: Path) -> None:
    """Preserve CBDT sequence outputs whose generic names collide with CJK glyphs."""
    source = path.read_text(encoding="utf-8")
    anchor = "    # Build emoji_glyphs_to_add preserving NotoColorEmoji's glyph ID order."
    if source.count(anchor) != 1:
        raise RuntimeError("Upstream Color merge changed; review collision patch")
    patch = '    # SC overlay: generic glyphNNNNN names are not shared semantic identities.\n    # Keep required emoji and sequence outputs, renaming collisions before CBLC\n    # copying so the existing bitmap rename path preserves glyph-ID ordering.\n    required_names = set(emoji_cmap.values()) | {\n        entry.source_glyph for entry in sequence_entries\n    }\n    reserved_names = base_existing_names | set(emoji_all_glyph_order) | set(color_forced_rename.values())\n    for name in sorted(required_names & base_existing_names):\n        if name not in color_forced_rename:\n            candidate = f"{name}_color"\n            while candidate in reserved_names:\n                candidate += "_color"\n            color_forced_rename[name] = candidate\n            reserved_names.add(candidate)\n    emoji_cmap = {cp: color_forced_rename.get(name, name) for cp, name in emoji_cmap.items()}\n    sequence_entries = [\n        EmojiEntry(\n            codepoints=entry.codepoints,\n            source_glyph=color_forced_rename.get(entry.source_glyph, entry.source_glyph),\n            kind=entry.kind,\n            source_table_kind=entry.source_table_kind,\n        )\n        for entry in sequence_entries\n    ]\n\n'
    path.write_text(source.replace(anchor, patch + anchor), encoding="utf-8")


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

    engine = root / "src" / "emoji_merge.py"
    if engine.is_file():
        patch_color_collisions(engine)
        if "src/emoji_merge.py" not in changed:
            changed.append("src/emoji_merge.py")

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
