"""Give each card URL in the README this run's version, so no cache can serve an old copy.

Run: python scripts/stamp_readme.py README.md <version>
"""
import re
import sys
from pathlib import Path

CARD_URL = re.compile(r"(https://raw\.githubusercontent\.com/noorgx/noorgx/output/[a-z]+\.svg)(\?v=\d+)?")


def stamp(text: str, version: int) -> str:
    return CARD_URL.sub(lambda match: f"{match.group(1)}?v={version}", text)


def main(argv: list[str] | None = None) -> int:
    path, version = argv if argv is not None else sys.argv[1:]
    readme = Path(path)
    readme.write_text(stamp(readme.read_text(encoding="utf-8"), int(version)), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
