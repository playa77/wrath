# Version: 0.2.0 | 2026-11-02
"""Exercise the packaged SDL path, including bundled assets and save/continue."""

import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory


def main():
    executable = Path("dist/cradle") / ("cradle.exe" if os.name == "nt" else "cradle")
    with TemporaryDirectory(prefix="cradle-bundle-smoke-") as home:
        env = {
            **os.environ,
            "CRADLE_HOME": home,
            "SDL_VIDEODRIVER": "dummy",
            "SDL_RENDER_DRIVER": "software",
        }
        subprocess.run(
            [str(executable.resolve()), "--smoke"], env=env, check=True, timeout=60
        )


if __name__ == "__main__":
    main()
