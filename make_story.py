"""Draw the availability story (1080x1920 PNG) on the mockup background.

The mockup already has the title and footer. This script erases the old table
and date line, then draws the date and a table with one row per slot.
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MOCKUP = os.path.join(HERE, "assets", "mockup.png")

# Column edges. Wider than the mockup's table so the text has room on every font.
TABLE_X = (90, 300, 690, 990)
CELL_PAD = 18  # minimum space between text and a cell border
TABLE_TOP = 628
HEADER_H = 141
ROW_H = 125  # used when there are few rows
TABLE_MAX_BOTTOM = 1620  # the footer "RE:FORM" starts around y=1690
DATE_CENTER = (540, 478)
ERASE_TABLE = (150, 620, 930, 1210)  # covers the table baked into the mockup
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


def _text_width(draw, text, font):
    left, _, right, _ = draw.multiline_textbbox((0, 0), text, font=font, align="center")
    return right - left


def date_text(day):
    return f"{day.day} {MONTHS_MK[day.month]}"


def render(day, kind, slots, out_path):
    """slots: [{"time", "free", "kind"}] sorted by time. kind sets the class name per row."""
    img = Image.open(MOCKUP).convert("RGB")
    draw = ImageDraw.Draw(img)
    bg = img.getpixel((1000, 1400))

    draw.rectangle(ERASE_TABLE, fill=bg)
    draw.rectangle(ERASE_DATE, fill=bg)

    rows = len(slots)
    row_h = min(ROW_H, (TABLE_MAX_BOTTOM - TABLE_TOP - HEADER_H) // rows)
    font_size = FONT_SIZE if row_h >= 110 else 32
    headers = ["Време", "Час", "Слободни\nместа"]
    columns = [
        [slot["time"] for slot in slots],
        [CLASS_NAME[slot["kind"]] for slot in slots],
        [str(slot["free"]) for slot in slots],
    ]
    # Fonts differ in width between machines, so shrink the text until every cell fits.
    while True:
        regular = load_font(FONT_REGULAR, font_size)
        bold = load_font(FONT_BOLD, font_size)
        fits = all(
            _text_width(draw, text, font) <= TABLE_X[i + 1] - TABLE_X[i] - 2 * CELL_PAD
            for i in range(3)
            for text, font in [(headers[i], bold)] + [(t, regular) for t in columns[i]]
        )
        if fits or font_size <= 20:
            break
        font_size -= 2

    draw.multiline_text(DATE_CENTER, date_text(day), font=load_font(FONT_REGULAR, FONT_SIZE), fill="black",
                        anchor="mm", align="center")

    x0, x1, x2, x3 = TABLE_X
    bottom = TABLE_TOP + HEADER_H + rows * row_h
    draw.rectangle((x0, TABLE_TOP, x3, TABLE_TOP + HEADER_H), fill="white")
    for x in TABLE_X:
        draw.line([(x, TABLE_TOP), (x, bottom)], fill="black", width=2)
    horizontal_ys = [TABLE_TOP, TABLE_TOP + HEADER_H]
    horizontal_ys += [TABLE_TOP + HEADER_H + row_h * (i + 1) for i in range(rows)]
    for y in horizontal_ys:
        draw.line([(x0, y), (x3, y)], fill="black", width=2)

    def center(x_left, x_right, y_top, y_bottom):
        return ((x_left + x_right) / 2, (y_top + y_bottom) / 2)

    header_y = (TABLE_TOP, TABLE_TOP + HEADER_H)
    draw.multiline_text(center(x0, x1, *header_y), "Време", font=bold, fill="black", anchor="mm", align="center")
    draw.multiline_text(center(x1, x2, *header_y), "Час", font=bold, fill="black", anchor="mm", align="center")
    draw.multiline_text(center(x2, x3, *header_y), "Слободни\nместа", font=bold, fill="black", anchor="mm", align="center")

    for i, slot in enumerate(slots):
        top = TABLE_TOP + HEADER_H + i * row_h
        row_y = (top, top + row_h)
        draw.multiline_text(center(x0, x1, *row_y), slot["time"], font=regular, fill="black", anchor="mm", align="center")
        draw.multiline_text(center(x1, x2, *row_y), CLASS_NAME[slot["kind"]], font=regular, fill="black", anchor="mm", align="center")
        draw.multiline_text(center(x2, x3, *row_y), str(slot["free"]), font=regular, fill="black", anchor="mm", align="center")

    img.save(out_path, "PNG")
    return out_path
