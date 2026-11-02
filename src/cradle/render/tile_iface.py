# Version: 0.2.0 | 2026-11-02
"""Renderer swap contract (ADR-1); no tile implementation is in scope."""

from typing import Protocol
from cradle.ui.frame import Frame


class RendererProtocol(Protocol):
    def render(self, frame: Frame) -> None: ...
    def poll(self): ...
    def close(self) -> None: ...
