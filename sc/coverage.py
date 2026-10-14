#!/usr/bin/env python3
"""Build offline visual inspectors and source-relative font coverage reports."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from fontTools.ttLib import TTFont
import yaml

VARIANTS = {'fonts': 'SarasaMonoSCEmoji', 'fonts-lite': 'SarasaMonoSCEmojiLite',
            'fonts-colrv1': 'SarasaMonoSCEmojiCOLRv1', 'fonts-nerd-lite': 'SarasaMonoSCEmojiLiteNerd'}
STYLES = ('Regular', 'Italic', 'Bold', 'BoldItalic')
SOURCES = ('NotoColorEmoji.ttf', 'Noto-COLRv1.ttf', 'NotoEmoji[wght].ttf')
FEATURED = ('😀', '❤️', '⚠️', '👩‍💻', '👋🏻', '🇨🇳', '🇺🇸', '👨‍👩‍👧‍👦')


def ligatures(font, feature=None):
    """Read direct ligature rules, including extension lookups; optionally restrict features."""
    if 'GSUB' not in font:
        return {}
    table = font['GSUB'].table
    if not table.LookupList:
        return {}
    indexes = set(range(len(table.LookupList.Lookup)))
    if feature:
        indexes = {i for record in table.FeatureList.FeatureRecord if record.FeatureTag == feature
                   for i in record.Feature.LookupListIndex} if table.FeatureList else set()
    result = {}
    for index in sorted(indexes):
        lookup = table.LookupList.Lookup[index]
        for subtable in lookup.SubTable:
            kind = lookup.LookupType
            if kind == 7:
                kind, subtable = subtable.ExtensionLookupType, subtable.ExtSubTable
            if kind != 4:
                continue
            for first, entries in subtable.ligatures.items():
                for entry in entries:
                    result.setdefault((first, *entry.Component), entry.LigGlyph)
    return result


def candidates(font):
    cmap = font.getBestCmap() or {}
    singles = {(cp,) for cp in cmap if cp > 0xFF and cp not in (0x200C, 0x200D)
               and not 0xFE00 <= cp <= 0xFE0F and not 0xE0100 <= cp <= 0xE01EF}
    reverse = {}
    for cp, glyph in sorted(cmap.items()):
        reverse.setdefault(glyph, cp)
    for inputs in ligatures(font):
        if all(glyph in reverse for glyph in inputs):
            singles.add(tuple(reverse[glyph] for glyph in inputs))
    return singles


def ranges(codepoints):
    result = []
    for cp in sorted(set(codepoints)):
        if result and result[-1][1] + 1 == cp:
            result[-1][1] = cp
        else:
            result.append([cp, cp])
    return result


def payload_glyphs(font):
    color = set()
    if 'CBDT' in font:
        for strike in font['CBDT'].strikeData:
            color.update(strike)
    if 'COLR' in font:
        colr = font['COLR']
        if getattr(colr, 'version', 0) == 0:
            color.update(colr.ColorLayers)
        else:
            base = getattr(colr.table, 'BaseGlyphList', None)
            if base:
                color.update(record.BaseGlyph for record in base.BaseGlyphPaintRecord)
    return color


def font_report(path, rows):
    with TTFont(path, lazy=False) as font:
        cmap = font.getBestCmap() or {}
        direct = ligatures(font, 'ccmp')
        color = payload_glyphs(font)
        glyf = font['glyf'] if 'glyf' in font else None
        def state(codepoints):
            inputs = tuple(cmap.get(cp) for cp in codepoints)
            glyph = inputs[0] if len(inputs) == 1 else direct.get(inputs)
            # A presentation selector can use the base glyph without a GSUB rule.
            if glyph is None and len(codepoints) == 2 and codepoints[1] in (0xFE0E, 0xFE0F):
                for table in font['cmap'].tables:
                    if table.format == 14:
                        for cp, variant in table.uvsDict.get(codepoints[1], []):
                            if cp == codepoints[0]:
                                glyph = variant or inputs[0]
                if glyph is None:
                    glyph = inputs[0]
                if codepoints[1] == 0xFE0E and glyph in color:
                    return 'empty' if glyf is None or glyph not in glyf or glyf[glyph].numberOfContours == 0 else 'outline'
            if glyph is None:
                return 'missing'
            if glyph in color:
                return 'color'
            if glyf is not None and glyph in glyf and glyf[glyph].numberOfContours != 0:
                return 'outline'
            return 'empty'
        states = [state(row['codepoints']) for row in rows]
        order = font.getGlyphOrder()
        widths = font['hmtx'].metrics
        upm = font['head'].unitsPerEm
        half = widths[cmap[0x41]][0]
        return {'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'family': font['name'].getBestFamilyName(), 'glyph_count': len(order),
                'glyph_slots_remaining': 65535 - len(order), 'units_per_em': upm,
                'half_width': half, 'ascent': font['hhea'].ascent, 'descent': font['hhea'].descent,
                'line_gap': font['hhea'].lineGap, 'size_bytes': path.stat().st_size,
                'mapped_ranges': ranges(cmap), 'states': states, 'counts': dict(Counter(states))}


def generate(root, template):
    pool = set()
    for name in SOURCES:
        matches = sorted(path for path in (root / 'fonts').rglob('*.ttf') if path.name == name)
        if len(matches) != 1:
            raise ValueError(f'Expected one source font {name}, found {len(matches)}')
        with TTFont(matches[0]) as font:
            pool.update(candidates(font))
    pool.update(tuple(ord(char) for char in text) for text in FEATURED)
    config = yaml.safe_load((root / 'config.yaml').read_text())
    icon_ranges = config['nerd_lite']['icon_ranges']
    nerd_matches = list((root / 'fonts').rglob('SymbolsNerdFontMono-Regular.ttf'))
    if len(nerd_matches) != 1:
        raise ValueError('Expected one Nerd Fonts source')
    with TTFont(nerd_matches[0]) as font:
        icons = {cp for cp in (font.getBestCmap() or {}) if any(lo <= cp <= hi for lo, hi in icon_ranges)}
    rows = [{'codepoints': list(cp), 'kind': 'sequence' if len(cp) > 1 else 'emoji'} for cp in sorted(pool)]
    rows += [{'codepoints': [cp], 'kind': 'nerd'} for cp in sorted(icons)]
    provenance = root.parent.parent / 'provenance.json'
    provenance_data = json.loads(provenance.read_text()) if provenance.exists() else None
    for directory, family in VARIANTS.items():
        output = root / 'output' / directory
        fonts = {style: font_report(output / f'{family}-{style}.ttf', rows) for style in STYLES}
        report = {'schema_version': 1, 'family': family, 'rows': rows, 'fonts': fonts,
                  'provenance': provenance_data,
                  'method': 'Source-font cmap + direct GSUB ligatures + curated common samples; multi-character output requires a ccmp ligature and visible payload, except presentation-selector pairs resolved via cmap14/base glyph. This is structural coverage, not a shaping or application compatibility test. Missing rows may include source alias sequences. COLRv1 omissions are not individually attributed to glyph budget.'}
        serialized = json.dumps(report, ensure_ascii=False, separators=(',', ':'))
        (output / 'coverage.json').write_text(serialized + '\n', encoding='utf-8')
        # Escape script delimiters regardless of future provenance/source text.
        embedded = serialized.replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
        (output / 'visual-check.html').write_text(template.read_text().replace('/*COVERAGE_DATA*/null', embedded), encoding='utf-8')
        (output / 'VISUAL_CHECK.txt').write_text('打开 visual-check.html，选择同一包中的 TTF。字体在本机加载，不上传。coverage.json 包含全部四个字重的覆盖和度量数据。未收录的条目不会交给系统回退字体显示。结构覆盖不代表浏览器或 CLion 的实际渲染结果。\n', encoding='utf-8')
        print(f'{family}: {len(rows)} candidates, 4 styles; visual-check.html + coverage.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    generate(args.root.resolve(), Path(__file__).parent / 'preview' / 'visual-check.html')
