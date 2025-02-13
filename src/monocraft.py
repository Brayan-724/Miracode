# Monocraft, a monospaced font for developers who like Minecraft a bit too much.
# Copyright (C) 2022-2023 Idrees Hassan
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import math

from generateFont import Font
from polygonizer import PixelImage, generatePolygons

# PIXEL_SIZE = 120

# ligatures += generate_continuous_ligatures("./continuous_ligatures.json")

SIZES = {
    # "Thin": 1000,
    # "ExtraLight": 464,
    # "Light": 420,
    # "Normal": 120,
    # "Medium": 332,
    # "SemiBold": 288,
    # "Bold": 244,
    "Black": 10,
}

class MonocraftFont(Font):
    def __init__(self):
        super().__init__("Monocraft", SIZES)

    def drawChar(self, size, font, character):
        font.createChar(character["codepoint"], character["name"])
        pen = font[character["name"]].glyphPen()

        image, kw = self.generateImage(character)
        self.drawImage(size, image, pen, **kw)
        font[character["name"]].width = size * 6

    def drawLigature(self, size, font, ligature):
        lig = font.createChar(-1, ligature["name"])
        pen = font[ligature["name"]].glyphPen()
        image, kw = self.generateImage(ligature)
        self.drawImage(size, image, pen, **kw)
        font[ligature["name"]].width = size * len(ligature["sequence"]) * 6
        lig.addPosSub("ligatures-subtable", tuple(map(lambda codepoint: self.charactersByCodepoint[codepoint]["name"], ligature["sequence"])))

    def generateImage(self, character):
        image = PixelImage()
        kw = {}
        if "pixels" in character:
            arr = character["pixels"]
            leftMargin = character["leftMargin"] if "leftMargin" in character else 0
            x = math.floor(leftMargin)
            kw['dx'] = leftMargin - x
            descent = -character["descent"] if "descent" in character else 0
            y = math.floor(descent)
            kw['dy'] = descent - y
            image = image | self.imageFromArray(arr, x, y)

        if "reference" in character:
            other = self.generateImage(self.charactersByCodepoint[character["reference"]])
            kw.update(other[1])
            image = image | other[0]

        if "diacritic" in character:
            diacritic = self.diacritics[character["diacritic"]]
            arr = diacritic["pixels"]
            x = image.x
            y = self.findHighestY(image) + 1

            if "diacriticSpace" in character:
                y += int(character["diacriticSpace"])

            image = image | self.imageFromArray(arr, x, y)

        return (image, kw)

    def findHighestY(self, image):
        for y in range(image.y_end - 1, image.y, -1):
            for x in range(image.x, image.x_end):
                if image[x, y]:
                    return y
        return image.y

    def imageFromArray(self, arr, x=0, y=0):
        return PixelImage(
            x=x,
            y=y,
            width=len(arr[0]),
            height=len(arr),
            data=bytes(x for a in reversed(arr) for x in a),
        )

    def drawImage(self, size, image, pen, *, dx=0, dy=0):
        for polygon in generatePolygons(image):
            start = True
            for x, y in polygon:
                x = (x + dx) * size
                y = (y + dy) * size
                if start:
                    pen.moveTo(x, y)
                    start = False
                else:
                    pen.lineTo(x, y)
            pen.closePath()

MonocraftFont().build()
