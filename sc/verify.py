#!/usr/bin/env python3
"""Fail closed on missing variants, broken SC family metadata and obvious width regressions."""
from pathlib import Path
import sys
from fontTools.ttLib import TTFont

VARIANTS = {
    "fonts": ("SarasaMonoSCEmoji", "CBDT"),
    "fonts-lite": ("SarasaMonoSCEmojiLite", None),
    "fonts-colrv1": ("SarasaMonoSCEmojiCOLRv1", "COLR"),
    "fonts-nerd-lite": ("SarasaMonoSCEmojiLiteNerd", None),
}
STYLES = ("Regular", "Italic", "Bold", "BoldItalic")


def verify(root: Path) -> int:
    count = 0
    for variant, (family, required_table) in VARIANTS.items():
        for style in STYLES:
            path = root / "output" / variant / f"{family}-{style}.ttf"
            if not path.is_file() or path.stat().st_size < 100_000:
                raise AssertionError(f"Missing / undersized font: {path}")
            font = TTFont(str(path), lazy=False)
            try:
                family_name = font["name"].getBestFamilyName() or ""
                if family_name != family:
                    raise AssertionError(f"{path}: unexpected family '{family_name}'")
                cmap = font.getBestCmap() or {}
                for cp in (0x0041, 0x4E00, 0x6C49, 0x7B80, 0x9F99, 0x1F600):
                    if cp not in cmap:
                        raise AssertionError(f"{path}: missing U+{cp:04X}")
                glyphs = len(font.getGlyphOrder())
                if glyphs >= 65536:
                    raise AssertionError(f"{path}: glyph count overflow {glyphs}")
                hmtx = font["hmtx"].metrics
                half = hmtx[cmap[0x0041]][0]
                cjk = hmtx[cmap[0x4E00]][0]
                emoji = hmtx[cmap[0x1F600]][0]
                if half <= 0 or cjk != 2 * half or emoji != cjk:
                    raise AssertionError(f"{path}: width mismatch A={half}, CJK={cjk}, emoji={emoji}")
                if required_table and required_table not in font:
                    raise AssertionError(f"{path}: missing {required_table}")
                if variant == "fonts-colrv1" and "CPAL" not in font:
                    raise AssertionError(f"{path}: missing CPAL")
                if variant == "fonts" and "CBLC" not in font:
                    raise AssertionError(f"{path}: missing CBLC")
                print(f"PASS {path.name}: glyphs={glyphs} halfwidth={half} emoji={emoji}")
                count += 1
            finally:
                font.close()
    return count


if __name__ == "__main__":
    directory = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    print(f"SC font checks passed: {verify(directory)} fonts")
