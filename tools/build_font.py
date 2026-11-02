# Version: 0.2.0 | 2026-11-02
"""Rasterize licensed DejaVu Sans Mono into the bundled 8x16 CP437 sheet.

Pillow is a generation-only dependency; the game loads the committed PNG.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
from tcod.tileset import CHARMAP_CP437


def main():
    root = Path(__file__).resolve().parents[1]
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 13)
    sheet = Image.new("RGBA", (128, 256))
    for index, code in enumerate(CHARMAP_CP437):
        tile = Image.new("RGBA", (8, 16))
        draw = ImageDraw.Draw(tile)
        draw.text((0, 12), chr(code), font=font, fill=(255, 255, 255, 255), anchor="ls")
        sheet.paste(tile, (index % 16 * 8, index // 16 * 16))
    info = PngImagePlugin.PngInfo()
    info.add_text("Version", "0.2.0 | 2026-11-02")
    sheet.save(root / "src/cradle/assets/cp437.png", pnginfo=info)


if __name__ == "__main__":
    main()
