# Version: 0.2.0 | 2026-11-02
"""Semantic color-token lookup with fail-fast diagnostics."""

from cradle.engine.errors import ContentError


class Colors:
    def __init__(self, regs):
        self.tokens = {
            r["id"]: tuple(r["rgb"]) for r in regs["text/color_tokens.json"]["rows"]
        }

    def rgb(self, token):
        if token not in self.tokens:
            raise ContentError("color_tokens.json", token, "unknown token")
        return self.tokens[token]
