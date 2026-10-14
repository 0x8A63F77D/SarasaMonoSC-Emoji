from pathlib import Path
from types import SimpleNamespace as NS
import tempfile
import unittest

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

from sc.coverage import candidates, font_report, ligatures, ranges


def font_fixture(path):
    builder = FontBuilder(1000, isTTF=True)
    names = ['.notdef', 'A', 'woman', 'zwj', 'laptop', 'woman_laptop', 'inactive', 'empty']
    builder.setupGlyphOrder(names)
    glyphs = {}
    for name in names:
        pen = TTGlyphPen(None)
        if name not in ('zwj', 'empty', '.notdef'):
            pen.moveTo((0, 0)); pen.lineTo((300, 0)); pen.lineTo((300, 500)); pen.closePath()
        glyphs[name] = pen.glyph()
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics({name: (500, 0) for name in names})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupCharacterMap({65: 'A', 0x1F469: 'woman', 0x200D: 'zwj', 0x1F4BB: 'laptop', 0x2600: 'empty'})
    builder.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
    builder.setupNameTable({'familyName': 'Fixture', 'styleName': 'Regular'})
    builder.setupPost()
    addOpenTypeFeaturesFromString(builder.font, 'feature ccmp { sub woman zwj laptop by woman_laptop; } ccmp; feature dlig { sub woman laptop by inactive; } dlig;')
    builder.save(path)
    return builder.font


class CoverageTests(unittest.TestCase):
    def test_ranges_preserve_sparse_mapping(self):
        self.assertEqual(ranges([8, 2, 3, 2, 9, 15]), [[2, 3], [8, 9], [15, 15]])

    def test_output_requires_visible_payload_and_ccmp_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'fixture.ttf'
            font = font_fixture(path)
            rows = [{'codepoints': cp} for cp in [[65], [0x2600], [0x1F469, 0x200D, 0x1F4BB], [0x1F469, 0x1F4BB], [0x1F600], [65, 0xFE0F]]]
            report = font_report(path, rows)
            self.assertEqual(report['states'], ['outline', 'empty', 'outline', 'missing', 'missing', 'outline'])
            self.assertEqual(report['glyph_count'], 8)
            self.assertEqual(len(report['sha256']), 64)
            self.assertIn((0x1F469, 0x200D, 0x1F4BB), candidates(font))
            self.assertNotIn((0x200D,), candidates(font))
            font.close()

    def test_extension_ligatures_are_counted(self):
        table = NS(ligatures={'first': [NS(Component=['second'], LigGlyph='out')]})
        gsub = NS(LookupList=NS(Lookup=[NS(LookupType=7, SubTable=[NS(ExtensionLookupType=4, ExtSubTable=table)])]),
                  FeatureList=NS(FeatureRecord=[NS(FeatureTag='ccmp', Feature=NS(LookupListIndex=[0]))]))
        font = {'GSUB': NS(table=gsub)}
        self.assertEqual(ligatures(font, 'ccmp'), {('first', 'second'): 'out'})


if __name__ == '__main__':
    unittest.main()
