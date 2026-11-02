# Version: 0.2.0 | 2026-11-02
"""SDL-backed 120x40 CP437 renderer; keyboard input only (C-1/2)."""

from pathlib import Path
import tcod
import tcod.context
import tcod.tileset
import tcod.event
from cradle.ui.symbolmap import resolve
from cradle.ui.colors import Colors


class TextRenderer:
    def __init__(self, cfg, regs):
        self.regs = regs
        self.colors = Colors(regs)
        self.closed = False
        sheet = Path(__file__).resolve().parents[1] / "assets/cp437.png"
        # Map sheet indices to literal CP437 IDs, matching the Frame contract.
        self.tileset = tcod.tileset.load_tilesheet(sheet, 16, 16, list(range(256)))
        self.console = tcod.console.Console(120, 40, order="C")
        self.context = tcod.context.new(
            columns=120,
            rows=40,
            width=960 * cfg.window_scale,
            height=640 * cfg.window_scale,
            tileset=self.tileset,
            vsync=True,
            renderer=tcod.constants.RENDERER_SDL2,
            title="The Cradle Plateau: The Wrath of Doctor Voss",
        )
        self.queue = []

    def render(self, frame):
        self.console.clear(fg=self.colors.rgb("parchment"), bg=self.colors.rgb("ink"))
        for y, row in enumerate(frame["cells"]):
            for x, cell in enumerate(row):
                for layer in cell["layers"]:
                    symbol = layer["symbol_id"]
                    glyph, fg, bg = resolve(symbol, layer["flags"], self.regs)
                    if symbol < 256:
                        fg, bg = layer["fg"], layer["bg"]
                    self.console.ch[y, x] = glyph
                    self.console.fg[y, x] = self.colors.rgb(fg)
                    self.console.bg[y, x] = self.colors.rgb(bg)
        self.context.present(self.console, integer_scaling=True, keep_aspect=True)

    def poll(self):
        self.queue.extend(tcod.event.get())
        while self.queue:
            event = self.queue.pop(0)
            if isinstance(event, tcod.event.Quit):
                return "QUIT"
            if isinstance(event, tcod.event.KeyDown):
                return event
        return None

    def close(self):
        if not self.closed:
            self.context.close()
            self.closed = True

    def save_frame(self, path):
        """Export the logical CP437 frame without driver-specific screenshot APIs."""
        import struct
        import zlib

        rows = []
        for y in range(40):
            tiles = [
                self.tileset.get_tile(int(self.console.ch[y, x])) for x in range(120)
            ]
            for ty in range(16):
                scan = bytearray([0])
                for x, tile in enumerate(tiles):
                    fg = self.console.fg[y, x]
                    bg = self.console.bg[y, x]
                    for tx in range(8):
                        alpha = int(tile[ty, tx, 3])
                        scan.extend(
                            (int(fg[c]) * alpha + int(bg[c]) * (255 - alpha)) // 255
                            for c in range(3)
                        )
                rows.append(bytes(scan))

        def chunk(tag, data):
            return (
                struct.pack("!I", len(data))
                + tag
                + data
                + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            )

        Path(path).write_bytes(
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack("!2I5B", 960, 640, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"".join(rows)))
            + chunk(b"IEND", b"")
        )
