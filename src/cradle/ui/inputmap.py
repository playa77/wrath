# Version: 0.2.0 | 2026-11-02
"""Keyboard normalization; interpretation is contextual in MenuSession."""


def translate(k):
    if isinstance(k, str):
        name = k
    elif hasattr(k, "text"):
        return dict(kind="text", value=k.text)
    elif hasattr(k, "sym"):
        name = k.sym.name
    else:
        return None
    name = name.upper()
    if len(name) == 2 and name[0] == "N" and name[1].isdigit():
        name = name[1]
    if name in ["UP", "KP_8"]:
        return dict(kind="direction", value="N")
    if name in ["RIGHT", "KP_6"]:
        return dict(kind="direction", value="E")
    if name in ["DOWN", "KP_2"]:
        return dict(kind="direction", value="S")
    if name in ["LEFT", "KP_4"]:
        return dict(kind="direction", value="W")
    if name in ["RETURN", "ENTER", "KP_ENTER"]:
        return dict(kind="enter", value="ENTER")
    if name == "ESCAPE":
        return dict(kind="escape", value="ESC")
    if name == "SPACE":
        return dict(kind="text", value=" ")
    if name == "MINUS":
        return dict(kind="key", value="-")
    if name == "EQUALS":
        return dict(kind="key", value="=")
    if name == "BACKSPACE":
        return dict(kind="backspace", value="")
    if name in ["PAGEUP", "PAGEDOWN", "TAB"]:
        return dict(kind="page", value=-1 if name == "PAGEUP" else 1)
    if len(name) == 1:
        return dict(kind="key", value=name)
    return None
