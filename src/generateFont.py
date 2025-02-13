import os
import fontforge
import json

from generate_diacritics import generateDiacritics
# from generate_examples import generateExamples
# from polygonizer import PixelImage, generatePolygons
# from generate_continuous_ligatures import generate_continuous_ligatures 

characters = json.load(open("./characters.json"))
diacritics = json.load(open("./diacritics.json"))
ligatures = json.load(open("./ligatures.json"))
# ligatures += generate_continuous_ligatures("./continuous_ligatures.json")

characters = generateDiacritics(characters, diacritics)
charactersByCodepoint = {}
for character in characters:
    charactersByCodepoint[character["codepoint"]] = character

class Font:
    def __init__(self, name, sizes):
        self.name = name
        self.sizes = sizes

        self.charactersByCodepoint = charactersByCodepoint
        self.diacritics = diacritics

        self.output = "../dist/"
        if not os.path.exists(self.output):
            os.makedirs(self.output)

    def build(self):
        font = self.setup_font()

        for weight, size in self.sizes.items():
            print("Building %s (%s)" % (self.name, weight))
            self.buildFont(font, weight, size)

    def setup_font(self):
        font = fontforge.font()
        font.fontname = self.name
        font.familyname = self.name
        font.fullname = self.name
        font.copyright = "Idrees Hassan, https://github.com/IdreesInc/" + self.name
        font.encoding = "UnicodeFull"
        font.version = "1.0"
        font.addLookup("ligatures", "gsub_ligature", (), (("liga",(("dflt",("dflt")),("latn",("dflt")))),))
        font.addLookupSubtable("ligatures", "ligatures-subtable")

        return font

    def buildFont(self, font, weight, size):
        font.weight = weight
        font.ascent = size * 8
        font.descent = size
        font.em = size * 9
        font.upos = -size # Underline position

        for character in characters:
            self.drawChar(size = size, character = character, font = font)

        print(f"Generated {len(characters)} characters")

        # Generate the font without ligatures
        # print("Generating TTF font without ligatures...")
        # font.generate(self.output + self.name + weight + "-no-ligatures.ttf")

        for ligature in ligatures:
            self.drawLigature(size = size, ligature = ligature, font = font)

        print(f"Generated {len(ligatures)} ligatures")

        print("Generating TTF font...")
        font.generate(self.output + self.name + weight + ".ttf")
        print("Generating OTF font...")
        font.generate(self.output + self.name + weight + ".otf")
