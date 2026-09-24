import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
TECH = ["C", "C++", "AssemblyScript", "Python", "Go", "Rust", "Java", "JavaScript", "TypeScript", "PHP",
        "Bash", "PowerShell", "HTML5", "CSS3", "GraphQL", "Markdown", "LaTeX", "Django", "Flask", "FastAPI",
        "Express.js", "Node.js", "Laravel", "RabbitMQ", "JWT", "Jinja", "Apache Airflow", "Twilio", "React",
        "React Native", "Tailwind CSS", "Bootstrap", "Electron", "Tauri", "Expo", "JavaFX", "OpenCV", "OpenGL",
        "FFmpeg", "NPM", "PostgreSQL", "MySQL", "MariaDB", "SQLite", "MongoDB", "Redis", "Neo4j", "Firebase",
        "Pandas", "NumPy", "AWS", "Azure", "Google Cloud", "Netlify", "Docker", "GitHub Actions", "Grafana",
        "Postman"]


def test_readme_has_no_emoji():
    assert all(ord(ch) < 0x2190 for ch in README)


def test_readme_keeps_the_facts():
    for fact in ("Top-Rated", "Upwork", "3+ years", "Python", "Cybersecurity", "Penetration Testing",
                 "Reverse Engineering", "Web Application Security", "Automation", "Backend",
                 "linkedin.com/in/noor-ossama", "medium.com/@noorossamazakaria", "noorossamazakaria@gmail.com"):
        assert fact in README, fact


def test_readme_lists_every_tech_item_once():
    alts = re.findall(r'alt="([^"]+)"', README)
    for item in TECH:
        assert alts.count(item) == 1, item


def test_readme_images_point_at_real_files():
    for path in re.findall(r'src="(assets/[^"]+)"', README):
        assert (ROOT / path).exists(), path
    for name in ("snake", "record", "languages", "honours", "word"):
        assert f"raw.githubusercontent.com/noorgx/noorgx/output/{name}.svg" in README, name
    assert "streak-stats.demolab.com" in README and "komarev.com/ghpvc" in README


def test_no_heading_repeats_the_card_title_under_it():
    for title in ("THE RECORD", "HONOURS", "THE WORD"):
        assert f">{title}</h3>" not in README, title
