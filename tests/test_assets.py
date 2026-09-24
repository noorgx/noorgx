import xml.etree.ElementTree as ET
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
SIZES = {"header.svg": ("1200", "260"), "divider.svg": ("1200", "24"), "footer.svg": ("1200", "120")}


def test_static_svgs_parse_and_have_the_right_size():
    for name, (width, height) in SIZES.items():
        root = ET.parse(ASSETS / name).getroot()
        assert root.get("width") == width and root.get("height") == height, name


def test_static_svgs_have_no_emoji_and_use_only_system_fonts():
    for name in SIZES:
        text = (ASSETS / name).read_text(encoding="utf-8")
        assert all(ord(ch) < 0x2190 for ch in text), name
        assert "@import" not in text and "font-face" not in text, name


def test_header_uses_the_name_noor_zakaria():
    header = (ASSETS / "header.svg").read_text(encoding="utf-8")
    assert ">NOOR ZAKARIA<" in header and "OSSAMA" not in header.upper()
    assert "steps(12" in header
