#!/usr/bin/env python3
"""news-image-20261119 variant 3: Thursday 19 November 2026 as a timeline.

Draws a 1024x1024 PNG, "the day in hours": six verified news stories of
Thursday 19 November 2026, earliest at the top, latest at the bottom, on a
vertical timeline spine with a UTC time badge per entry. Pure Python 3.13
standard library only (zlib + struct for the PNG encoder); no network, no
external files, fully deterministic: the same bytes on every run.
"""

import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

# ---------------------------------------------------------------- font -----
# A 5x7 bitmap font, drawn from scratch. Each glyph is 7 rows of 5 bits,
# written as strings of '1' (ink) and '0' (blank). Uppercase, lowercase,
# digits and the punctuation the copy needs.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "11110", "10001", "11110", "10000", "10000"),
    "q": ("00000", "00000", "01111", "10001", "01111", "00001", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11100", "01000", "01000", "01001", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
}

# -------------------------------------------------------------- canvas -----
class Canvas:
    """A plain RGB canvas held as one bytearray, row-major, 3 bytes/px."""

    def __init__(self, width, height, colour):
        self.width = width
        self.height = height
        self.pixels = bytearray(colour * (width * height))

    def set_pixel(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i:i + 3] = colour

    def rect(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        row = bytes(colour) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.width + x0) * 3
            self.pixels[i:i + len(row)] = row

    def disc(self, cx, cy, r, colour):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set_pixel(xx, yy, colour)

    def hline(self, x, y, w, colour, thick=1):
        self.rect(x, y - thick // 2, w, thick, colour)

    def vline(self, x, y, h, colour, thick=1):
        self.rect(x - thick // 2, y, thick, h, colour)


def text_width(text, scale):
    """Pixel width of text drawn at the given scale (6 units per glyph)."""
    return len(text) * 6 * scale


def draw_text(canvas, x, y, text, scale, colour):
    """Draw one line of text; returns the x just past the last glyph."""
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT["?"])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    canvas.rect(cx + col * scale, y + row * scale,
                                scale, scale, colour)
        cx += 6 * scale
    return cx


def draw_wrapped(canvas, x, y, text, scale, colour, max_width):
    """Word-wrap text to max_width and draw it; returns total height used."""
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    line_h = 9 * scale
    for i, line in enumerate(lines):
        draw_text(canvas, x, y + i * line_h, line, scale, colour)
    return len(lines) * line_h


# ------------------------------------------------------------------ png -----
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(canvas):
    """Encode the canvas as a deterministic PNG (filter 0, level 9)."""
    header = struct.pack(">IIBBBBB", canvas.width, canvas.height, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = canvas.width * 3
    for y in range(canvas.height):
        raw.append(0)
        raw += canvas.pixels[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", header)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return png


# --------------------------------------------------------------- stories ----
# Six stories verified as news of Thursday 19 November 2026, in UTC order.
# Times are the time each event happened or was first reported (UTC).
#   05:00  GTA VI goes live in the US at midnight Eastern (People, CNN).
#   06:30  Trump-Xi-Putin trilateral, 14:30 Shenzhen time, White House
#          schedule via Newsquawk; first ever meeting of the three.
#   09:00  ICJ reading begins, 10:00 CET, The Hague (ICJ / Reuters).
#          The ruling itself is the event; no outcome is claimed here.
#   14:00  Atmospheric river: heaviest rain reaches Los Angeles on
#          Thursday morning, 30 million under flash-flood threat
#          (Fox Weather / National Weather Service).
#   17:00  NASA Voyager 1 briefing, noon EST, JPL (NASA).
#   18:00  Cyclone Akvan becomes a very severe storm, 23:30 IST,
#          winds 120-130 km/h gusting 145 (India Met Department).
STORIES = [
    {
        "time": "05:00",
        "tag": "CULTURE",
        "colour": (178, 34, 52),
        "headline": "GTA VI IS OUT",
        "summary": "After 13 years, Rockstar's sequel launches at midnight "
                   "local time. US players join at midnight Eastern.",
    },
    {
        "time": "06:30",
        "tag": "DIPLOMACY",
        "colour": (26, 84, 144),
        "headline": "THREE PRESIDENTS, ONE TABLE",
        "summary": "Trump, Xi and Putin meet in Shenzhen, a first ever "
                   "trilateral. Nuclear arms in focus, no deal expected.",
    },
    {
        "time": "09:00",
        "tag": "JUSTICE",
        "colour": (120, 72, 20),
        "headline": "WORLD COURT RULES ON ROHINGYA",
        "summary": "Judges in The Hague deliver the verdict in The Gambia's "
                   "genocide case against Myanmar, seven years on.",
    },
    {
        "time": "14:00",
        "tag": "WEATHER",
        "colour": (14, 110, 110),
        "headline": "STORM SOAKS CALIFORNIA",
        "summary": "An atmospheric river brings the week's heaviest rain to "
                   "Los Angeles. 30 million face a flash-flood threat.",
    },
    {
        "time": "17:00",
        "tag": "SPACE",
        "colour": (74, 52, 130),
        "headline": "VOYAGER 1, ONE LIGHT-DAY OUT",
        "summary": "NASA briefs the world on the probe, 16 billion miles "
                   "away, the first craft ever that far from home.",
    },
    {
        "time": "18:00",
        "tag": "WEATHER",
        "colour": (14, 110, 110),
        "headline": "CYCLONE AKVAN STRENGTHENS",
        "summary": "The storm off India's east coast turns very severe, "
                   "winds to 145 km/h. Landfall is due on Friday.",
    },
]

# --------------------------------------------------------------- colours ----
PAPER = (250, 247, 240)
INK = (24, 28, 38)
MUTED = (90, 96, 110)
NAVY = (16, 32, 64)
NAVY_LIGHT = (30, 52, 96)
GOLD = (212, 160, 44)
SPINE = (150, 158, 172)
WHITE = (255, 255, 255)
FOOTER_BG = (232, 228, 218)


def draw_header(canvas):
    """Navy header naming the day, with a gold rule beneath it."""
    canvas.rect(0, 0, WIDTH, 132, NAVY)
    canvas.rect(0, 132, WIDTH, 4, GOLD)
    draw_text(canvas, 48, 26, "THURSDAY 19 NOVEMBER 2026", 4, WHITE)
    draw_text(canvas, 48, 78, "THE WORLD IN ONE DAY, HOUR BY HOUR",
              3, (196, 205, 224))
    draw_text(canvas, 48, 106, "ALL TIMES UTC", 2, GOLD)


def draw_footer(canvas):
    """One-sentence summary of the day, plus a source line."""
    y = 936
    canvas.rect(0, y, WIDTH, HEIGHT - y, FOOTER_BG)
    canvas.rect(0, y, WIDTH, 3, GOLD)
    draw_wrapped(
        canvas, 48, y + 16,
        "A day of firsts: a record game launch, a first three-way summit, "
        "a landmark court ruling, and a probe farther from home than any "
        "craft before it.",
        2, INK, WIDTH - 96)
    draw_text(canvas, 48, 996,
              "Six stories, verified as news of 19 November 2026.",
              2, MUTED)


def draw_timeline(canvas):
    """The vertical spine with one entry per story, earliest on top."""
    spine_x = 118
    top = 168
    bottom = 912
    canvas.vline(spine_x, top, bottom - top, SPINE, 4)
    slot_h = (bottom - top) // len(STORIES)
    for i, story in enumerate(STORIES):
        cy = top + slot_h * i + slot_h // 2
        colour = story["colour"]
        # Time badge on the spine, dot marking the hour.
        canvas.disc(spine_x, cy, 13, colour)
        canvas.disc(spine_x, cy, 6, WHITE)
        badge_x = 28
        badge_y = cy - 28
        canvas.rect(badge_x, badge_y, 72, 56, colour)
        draw_text(canvas, badge_x + 18, badge_y + 7, story["time"][:2], 3,
                  WHITE)
        draw_text(canvas, badge_x + 18, badge_y + 30, story["time"][3:], 3,
                  WHITE)
        # Tag, headline and one-line summary to the right of the spine.
        tx = spine_x + 34
        draw_text(canvas, tx, cy - 44, story["tag"], 2, colour)
        draw_text(canvas, tx, cy - 20, story["headline"], 3, INK)
        draw_wrapped(canvas, tx, cy + 12, story["summary"], 2, MUTED, 800)


def render():
    """Build the whole image and return its PNG bytes."""
    canvas = Canvas(WIDTH, HEIGHT, PAPER)
    draw_header(canvas)
    draw_timeline(canvas)
    draw_footer(canvas)
    return encode_png(canvas)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as handle:
        handle.write(render())


if __name__ == "__main__":
    main()
