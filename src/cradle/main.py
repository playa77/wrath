# Version: 0.1.0 | 2026-11-02
"""Application entry point; composition is completed in WP-6.2."""
import argparse
from importlib.metadata import version
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="The Cradle Plateau: The Wrath of Doctor Voss")
    parser.add_argument("--version", action="version", version=version("cradle-wrath"))
    parser.parse_args(argv)
    print("The application loop is not implemented yet. See README.md for work-package status.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
