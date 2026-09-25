import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from stamp_readme import stamp  # noqa: E402

BASE = "https://raw.githubusercontent.com/noorgx/noorgx/output"


def test_stamp_adds_a_version_to_each_card_url():
    text = f'<img src="{BASE}/record.svg" /> <img src="{BASE}/snake.svg" />'
    assert stamp(text, 57) == f'<img src="{BASE}/record.svg?v=57" /> <img src="{BASE}/snake.svg?v=57" />'


def test_stamp_replaces_an_old_version():
    assert stamp(f'src="{BASE}/honours.svg?v=12"', 13) == f'src="{BASE}/honours.svg?v=13"'


def test_stamp_leaves_other_urls_alone():
    text = 'src="assets/header.svg" src="https://streak-stats.demolab.com/?user=noorgx"'
    assert stamp(text, 5) == text
