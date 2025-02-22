# Miracode
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

SIZES = {
    "Thin": 508,
    "ExtraLight": 464,
    "Light": 420,
    "Normal": 376,
    "Medium": 332,
    "SemiBold": 288,
    "Bold": 244,
    "Black": 200,
}

SQRT_TWO = math.sqrt(2)

class MiraCodeFont(Font):
    def __init__(self):
        super().__init__("Miracode", SIZES)

    def drawChar(self, size, font, character):
        font.createChar(character["codepoint"], character["name"])
        pen = font[character["name"]].glyphPen()

        if character.get("reference"):
            referencedCharacter = self.charactersByCodepoint[character["reference"]]
            self.drawCharacter(size, referencedCharacter, font[character["name"]], pen)
        else:
            self.drawCharacter(size, character, font[character["name"]], pen)

        font[character["name"]].width = size * 6

    def drawLigature(self, size, font, ligature):
        lig = None
        if ligature.get("pixels"):
            # Basic ligature
            lig = font.createChar(-1, ligature["name"])
            pen = font[ligature["name"]].glyphPen()
            self.drawCharacter(size, ligature, lig, pen)
            font[ligature["name"]].width = size * len(ligature["sequence"]) * 6
        elif ligature.get("chain"):
            # Chain ligature
            chain = ligature["chain"]
            lig = font.createChar(-1, ligature["name"])
            pen = font[ligature["name"]].glyphPen()
            xOffset = 0
            for character in chain:
                if character.get("pixels"):
                    xOffset = self.drawCharacter(size, character, lig, pen, xOffset)
                elif character.get("reference"):
                    linkedCharacter = self.charactersByCodepoint[character["reference"]]
                    xOffset = self.drawCharacter(size, linkedCharacter, lig, pen, xOffset)
                else:
                    print(f"Unexpected character in ligature {ligature['name']}: {character}")
                xOffset += size
        else:
            print(f"Unexpected ligature type: {ligature}")
            return

        font[ligature["name"]].width = size * len(ligature["sequence"]) * 6
        lig.addPosSub("ligatures-subtable", tuple(map(lambda codepoint: self.charactersByCodepoint[codepoint]["name"], ligature["sequence"])))

    
    def drawCharacter(self, size, character, glyph, pen, xOffset = 0):
        # print("Drawing character", character["name"])
        if not character.get("pixels"):
            # print(f"Character {character['name']} has no pixels")
            return xOffset

        drawDiagonals = True
        if "diagonals" in character:
            drawDiagonals = character["diagonals"]
        edges = generateEdges(character["pixels"], drawDiagonals)

        edgesPerPoint = getEdgesPerPoint(edges)

        descent = 0
        if "descent" in character:
            descent = character["descent"]
        top = (len(character["pixels"]) - descent) * size

        leftMargin = 0
        if "leftMargin" in character:
            leftMargin += character["leftMargin"]
        left = leftMargin * size + xOffset

        STROKE = 192
        HALF = STROKE / 2
        DOT_RADIUS = HALF * 1.5

        # Draw the paths
        for edge in edges:
            startX = edge[0][0] * size + size / 2 + left
            startY = top - (edge[0][1] * size - size / 2)
            endX = edge[1][0] * size + size / 2 + left
            endY = top - (edge[1][1] * size - size / 2)
            if startX == endX:
                # Down
                pen.moveTo(startX - HALF, startY)
                pen.lineTo(startX + HALF, startY)
                pen.lineTo(startX + HALF, endY)
                pen.lineTo(startX - HALF, endY)
                pen.closePath()
            elif startY == endY:
                # Right
                pen.moveTo(startX, startY - HALF)
                pen.lineTo(startX, startY + HALF)
                pen.lineTo(endX, startY + HALF)
                pen.lineTo(endX, startY - HALF)
                pen.closePath()
            elif startX < endX:
                # Diagonal right
                pen.moveTo(startX - HALF / SQRT_TWO, startY - HALF / SQRT_TWO)
                pen.lineTo(startX + HALF / SQRT_TWO, startY + HALF / SQRT_TWO)
                pen.lineTo(endX + HALF / SQRT_TWO, endY + HALF / SQRT_TWO)
                pen.lineTo(endX - HALF / SQRT_TWO, endY - HALF / SQRT_TWO)
                pen.closePath()
            else:
                # Diagonal left
                pen.moveTo(startX - HALF / SQRT_TWO, startY + HALF / SQRT_TWO)
                pen.lineTo(startX + HALF / SQRT_TWO, startY - HALF / SQRT_TWO)
                pen.lineTo(endX + HALF / SQRT_TWO, endY - HALF / SQRT_TWO)
                pen.lineTo(endX - HALF / SQRT_TWO, endY + HALF / SQRT_TWO)
                pen.closePath()


        jointAtPoint = {}
        # Calculate if each point has any joints that aren't in a straight line
        # For instance, a joint coming from the left and a joint coming from the top or just a joint coming from the left
        for point, edges in edgesPerPoint.items():
            if len(edges) == 1:
                # End cap
                jointAtPoint[point] = 1
            elif len(edges) == 2:
                # Determine if the edges are in a straight line
                edge1 = edges[0]
                edge2 = edges[1]
                if edge1[0][0] == edge1[1][0] and edge2[0][0] == edge2[1][0]:
                    # Vertical
                    jointAtPoint[point] = 0
                elif edge1[0][1] == edge1[1][1] and edge2[0][1] == edge2[1][1]:
                    # Horizontal
                    jointAtPoint[point] = 0
            else:
                # Joint
                jointAtPoint[point] = 1

        # Draw the dots
        pixels = character["pixels"]
        for row in range(len(pixels)):
            for col in range(len(pixels[0])):
                x = col * size + size / 2 + left
                y = top - row * size + size / 2
                if pixels[row][col] == 1:
                    if countNeighbors(pixels, row, col) == 0:
                        # Isolated dot
                        drawCircle(pen, x, y, DOT_RADIUS)
                        continue
                    elif jointAtPoint.get((col, row)) == 0:
                        # No joint or end cap
                        continue
                    drawOctagon(pen, x, y, HALF)
                elif pixels[row][col] == 2:
                    # Heart
                    drawHeart(pen, x, y, HALF)

        # Merge intersecting paths
        glyph.simplify()
        glyph.round()
        glyph.removeOverlap()

        # Return the rightmost edge of the character
        return xOffset + len(pixels[0]) * size

def generateEdges(pixels, drawDiagonals = True):
    edges = []

    numOfCols = len(pixels[0])
    numOfRows = len(pixels)
    for row in range(numOfRows):
        for col in range(numOfCols):
            if pixels[row][col] == 1:
                # Check if there is a pixel to the right
                if col < numOfCols - 1 and pixels[row][col + 1] == 1:
                    if drawDiagonals and ignoreRight(pixels, row, col):
                        pass
                    else:
                        edges.append(((col, row), (col + 1, row)))
                # Check if there is a pixel below
                if row < numOfRows - 1 and pixels[row + 1][col] == 1:
                    if drawDiagonals and ignoreDown(pixels, row, col):
                        pass
                    else:
                        edges.append(((col, row), (col, row + 1)))
                # Check diagonals
                if not drawDiagonals:
                    continue
                # Check if there is a pixel to the bottom right
                if col < numOfCols - 1 and row < numOfRows - 1 and pixels[row + 1][col + 1] == 1:
                    if not ignoreDiagonal(pixels, row, col, False):
                        edges.append(((col, row), (col + 1, row + 1)))
                # Check if there is a pixel to the bottom left
                if col > 0 and row < numOfRows - 1 and pixels[row + 1][col - 1] == 1:
                    if not ignoreDiagonal(pixels, row, col, True):
                        edges.append(((col, row), (col - 1, row + 1)))
    return edges

def ignoreRight(pixels, row, col):
    ignorePatterns = [
        # "W" left
        (
            ("1", "0", "1"),
            ("X", "1", "0"),
            ("1", "0", "~"),
        ),
        # "W" right
        (
            ("1", "0", "1"),
            ("0", "X", "1"),
            ("0", "0", "1"),
        ),
        # "0"
        (
            ("0", "0", "1"),
            ("0", "X", "1"),
            ("1", "0", "1"),
        ),
        # "M"
        (
            ("1", "0", "0"),
            ("X", "1", "0"),
            ("1", "0", "1"),
        ),
        # "1"
        (
            ("0", "0", "0"),
            ("0", "1", "0"),
            ("X", "1", "0"),
            ("0", "1", "0"),
            ("0", "1", "0"),
        ),
    ]
    for pattern in ignorePatterns:
        if matchPattern(pixels, row, col, pattern):
            return True
    return False

def ignoreDown(pixels, row, col):
    ignorePatterns = [
        # "z" top
        (
            ("1", "X", "1"),
            ("0", "1", "0"),
            ("1", "0", "0"),
        ),
        # "z" bottom
        (
            ("0", "0", "1", "0"),
            ("0", "X", "0", "0"),
            ("1", "1", "1", "~"),
        ),
        # "→", "->"
        (
            ("1", "0", "0"),
            ("0", "X", "0"),
            ("1", "1", "1"),
            ("0", "1", "0"),
            ("1", "0", "0"),
        ),
        # "←"
        (
            ("0", "0", "1"),
            ("0", "X", "0"),
            ("1", "1", "1"),
            ("0", "1", "0"),
            ("0", "0", "1"),
        ),
    ]
    for pattern in ignorePatterns:
        if matchPattern(pixels, row, col, pattern):
            return True
    return False

def flipPattern(pattern):
    return list(map(lambda row: list(reversed(row)), pattern))

def ignoreDiagonal(pixels, row , col, flipped):
    whitelist = [
        # "z"
        (
            ("X", "1", "1"),
            ("0", "1", "0"),
            ("0", "0", "1"),
        ),
        # "↑"
        (
            ("0", "0", "X", "0", "0"),
            ("0", "1", "1", "1", "0"),
            ("1", "0", "1", "0", "1"),
        ),
        # "→", "->"
        (
            ("1", "0", "0"),
            ("0", "X", "0"),
            ("1", "1", "1"),
            ("0", "1", "0"),
            ("1", "0", "0"),
        ),
        # "↓"
        (
            ("1", "0", "1", "0", "1"),
            ("0", "X", "1", "1", "0"),
            ("0", "0", "1", "0", "0"),
        ),
    ]
    blacklist = [
        (
            ("0", "0", "0"),
            ("X", "1", "0"),
            ("0", "1", "0"),
        ),
        # "H" left
        (
            ("X", "0", "0"),
            ("1", "1", "1"),
            ("1", "0", "0"),
        ),
        # "H" right and "#"
        (
            ("~", "0", "1"),
            ("1", "X", "1"),
            ("~", "0", "1"),
        ),
        # "f"
        (
            ("0", "X", "0"),
            ("1", "1", "1"),
            ("0", "1", "0"),
        ),
        # "z" top
        (
            ("X", "1", "1"),
            ("0", "1", "0"),
            ("1", "0", "0"),
        ),
        # "z" bottom
        (
            ("0", "0", "1"),
            ("0", "X", "0"),
            ("1", "1", "1"),
        ),
        # "k" and "h"
        (
            ("X", "0", "1"),
            ("1", "1", "~"),
            ("1", "~", "~"),
        ),
        # "l"
        (
            ("0", "0", "0"),
            ("0", "X", "1"),
            ("0", "0", "1"),
            ("0", "0", "1"),
        ),
        # "u" and "w"
        (
            ("0", "1", "0"),
            ("0", "X", "0"),
            ("~", "1", "1"),
        ),
        # "0"
        (
            ("0", "0", "1"),
            ("~", "X", "1"),
            ("~", "0", "1"),
        ),
        # "F", "E", "P", etc.
        (
            ("1", "X", "1"),
            ("0", "0", "1"),
            ("~", "~", "1"),
        ),
        # "5"
        (
            ("1", "1"),
            ("X", "0"),
            ("1", "1"),
        ),
        # "Z"
        (
            ("0", "0", "1", "0"),
            ("0", "X", "0", "0"),
            ("0", "1", "1", "1"),
        ),
        # "$" top
        (
            ("0", "0", "0"),
            ("0", "X", "0"),
            ("1", "1", "1"),
        ),
        # "$" bottom
        (
            ("X", "1", "1"),
            ("0", "1", "0"),
            ("0", "0", "0"),
        ),
        # "e"
        (
            ("0", "1", "1"),
            ("X", "0", "0"),
            ("1", "1", "1"),
        ),
        # "2"
        (
            ("0", "0", "0"),
            ("0", "X", "0"),
            ("0", "1", "1"),
            ("0", "0", "0"),
        ),
    ]
    for pattern in whitelist:
        pat = pattern
        if flipped:
            pat = flipPattern(pattern)
        if matchPattern(pixels, row, col, pat):
            return False
    for pattern in blacklist:
        pat = pattern
        if flipped:
            pat = flipPattern(pattern)
        if matchPattern(pixels, row, col, pat):
            return True
    return False

def countNeighbors(pixels, row, col):
    count = 0
    if get(pixels, row - 1, col) == 1:
        count += 1
    if get(pixels, row, col - 1) == 1:
        count += 1
    if get(pixels, row + 1, col) == 1:
        count += 1
    if get(pixels, row, col + 1) == 1:
        count += 1
    if get(pixels, row - 1, col - 1) == 1:
        count += 1
    if get(pixels, row - 1, col + 1) == 1:
        count += 1
    if get(pixels, row + 1, col - 1) == 1:
        count += 1
    if get(pixels, row + 1, col + 1) == 1:
        count += 1
    return count

def drawCircle(pen, x, y, radius):
    # Draw clockwise
    VAL = 0.5522847498 # This is (4/3) * (sqrt(2) - 1)
    pen.moveTo(x, y + radius)
    pen.curveTo(x + radius * VAL, y + radius, x + radius, y + radius * VAL, x + radius, y)
    pen.curveTo(x + radius, y - radius * VAL, x + radius * VAL, y - radius, x, y - radius)
    pen.curveTo(x - radius * VAL, y - radius, x - radius, y - radius * VAL, x - radius, y)
    pen.curveTo(x - radius, y + radius * VAL, x - radius * VAL, y + radius, x, y + radius)
    pen.closePath()


def drawOctagon(pen, x, y, radius):
    # Draw clockwise
    VAL = (1 + SQRT_TWO) / 2
    sideLength = radius / VAL
    OCTAGON = [
        (1/2, VAL),
        (VAL, 1/2),
        (VAL, -1/2),
        (1/2, -VAL),
        (-1/2, -VAL),
        (-VAL, -1/2),
        (-VAL, 1/2),
        (-1/2, VAL)
    ]
    pen.moveTo(x + sideLength * OCTAGON[0][0], y + sideLength * OCTAGON[0][1])
    for i in range(1, len(OCTAGON)):
        pen.lineTo(x + sideLength * OCTAGON[i][0], y + sideLength * OCTAGON[i][1])
    pen.closePath()

def drawHeart(pen, x, y, radius):
    # Draw clockwise
    HEART = [
        (0, 0.9),
        (0.8, 1.6),
        (1.6, 0.9),
        (1.6, 0.2),
        (0, -1),
        (-1.6, 0.2),
        (-1.6, 0.9),
        (-0.8, 1.6)
    ]
    SCALE = 1.3
    radius *= SCALE
    pen.moveTo(x + radius * HEART[0][0], y + radius * HEART[0][1])
    for i in range(1, len(HEART)):
        pen.lineTo(x + radius * HEART[i][0], y + radius * HEART[i][1])
    pen.closePath()

def getEdgesPerPoint(edges):
    edgesPerPoint = {}
    for edge in edges:
        if edge[0] not in edgesPerPoint:
            edgesPerPoint[edge[0]] = []
        edgesPerPoint[edge[0]].append(edge)
        if edge[1] not in edgesPerPoint:
            edgesPerPoint[edge[1]] = []
        edgesPerPoint[edge[1]].append(edge)
    return edgesPerPoint

def get(pixel, row , col):
    if row < 0 or col < 0:
        return 0
    if row >= len(pixel) or col >= len(pixel[0]):
        return 0
    return pixel[row][col]

def compare(expected, actual):
    if expected == "~":
        return True
    elif expected == "1":
        return actual == 1
    elif expected == "0":
        return actual == 0
    return False

def matchPattern(pixels, row, col, pattern):
    cursorRow = None
    cursorCol = None
    for i in range(len(pattern)):
        for j in range(len(pattern[0])):
            if pattern[i][j] == "X":
                cursorRow = i
                cursorCol = j
                break
        if cursorRow != None:
            break
    if cursorRow == None or cursorCol == None:
        raise ValueError("Pattern must contain a cursor (X)")
    
    for i in range(len(pattern)):
        for j in range(len(pattern[0])):
            if i == cursorRow and j == cursorCol:
                continue
            if not compare(pattern[i][j], get(pixels, row + i - cursorRow, col + j - cursorCol)):
                return False
    return True

MiraCodeFont().build()
