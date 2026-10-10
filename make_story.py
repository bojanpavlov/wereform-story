"""Draw the availability story (1080x1920 PNG) on the mockup background.

The mockup already has the title and footer. This script erases the old table
and date line, then draws the date and a table with one row per slot.
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MOCKUP = os.path.join(HERE, "assets", "mockup.png")

# Table geometry, measured from the mockup.
TABLE_X = (158, 333, 689, 910)
TABLE_TOP = 628
HEADER_H = 141
ROW_H = 125
DATE_CENTER = (540, 478)
ERASE_TABLE = (150, 620, 930, 1210)  # covers the old table; table is sized to fit below
ERASE_DATE = (340, 440, 740, 515)

FONT_REGULAR = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
FONT_BOLD = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_SIZE = 40

MONTHS_MK = [
    "", "ЈАНУАРИ", "ФЕВРУАРИ", "МАРТ", "АПРИЛ", "МАЈ", "ЈУНИ",
    "ЈУЛИ", "АВГУСТ", "СЕПТЕМВРИ", "ОКТОМВРИ", "НОЕМВРИ", "ДЕКЕМВРИ",
]
CLASS_NAME = {
    "morning": "Утрински\nреформер",
    "afternoon": "Попладневен\nреформер",
}


def load_font(candidates, size):
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    raise FileNotFoundError(f"No font found in {candidates}")


def date_text(day):
    return f"{day.day} {MONTHS_MK[day.month]}"


def render(day, kind, slots, out_path):
    """slots: [{"time", "free"}] for one kind, already sorted by time."""
    img = Image.open(MOCKUP).convert("RGB")
    draw = ImageDraw.Draw(img)
    bg = img.getpixel((1000, 1400))

    draw.rectangle(ERASE_TABLE, fill=bg)
    draw.rectangle(ERASE_DATE, fill=bg)

    regular = load_font(FONT_REGULAR, FONT_SIZE)
    bold = load_font(FONT_BOLD, FONT_SIZE)

    draw.multiline_text(DATE_CENTER, date_text(day), font=regular, fill="black",
                        anchor="mm", align="center")

    x0, x1, x2, x3 = TABLE_X
    rows = len(slots)
    bottom = TABLE_TOP + HEADER_H + rows * ROW_H
    draw.rectangle((x0, TABLE_TOP, x3, TABLE_TOP + HEADER_H), fill="white")
    for x in TABLE_X:
        draw.line([(x, TABLE_TOP), (x, bottom)], fill="black", width=2)
    horizontal_ys = [TABLE_TOP, TABLE_TOP + HEADER_H]
    horizontal_ys += [TABLE_TOP + HEADER_H + ROW_H * (i + 1) for i in range(rows)]
    for y in horizontal_ys:
        draw.line([(x0, y), (x3, y)], fill="black", width=2)

    def center(x_left, x_right, y_top, y_bottom):
        return ((x_left + x_right) / 2, (y_top + y_bottom) / 2)

    header_y = (TABLE_TOP, TABLE_TOP + HEADER_H)
    draw.multiline_text(center(x0, x1, *header_y), "Време", font=bold, fill="black", anchor="mm", align="center")
    draw.multiline_text(center(x1, x2, *header_y), "Час", font=bold, fill="black", anchor="mm", align="center")
    draw.multiline_text(center(x2, x3, *header_y), "Слободни\nместа", font=bold, fill="black", anchor="mm", align="center")

    for i, slot in enumerate(slots):
        top = TABLE_TOP + HEADER_H + i * ROW_H
        row_y = (top, top + ROW_H)
        draw.multiline_text(center(x0, x1, *row_y), slot["time"], font=regular, fill="black", anchor="mm", align="center")
        draw.multiline_text(center(x1, x2, *row_y), CLASS_NAME[kind], font=regular, fill="black", anchor="mm", align="center")
        draw.multiline_text(center(x2, x3, *row_y), str(slot["free"]), font=regular, fill="black", anchor="mm", align="center")

    img.save(out_path, "PNG")
    return out_path
