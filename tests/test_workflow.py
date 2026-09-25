from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "profile.yml"


def test_workflow_builds_cards_and_snake_and_publishes_output_branch():
    text = WORKFLOW.read_text(encoding="utf-8")
    for needle in ('cron: "17 */6 * * *"', "workflow_dispatch", "contents: write",
                   "python scripts/cards.py --user ${{ github.repository_owner }} --out dist",
                   "Platane/snk/svg-only@v3",
                   "dist/snake.svg?color_snake=#a31515&color_dots=#161616,#3a0a0a,#5c0d0d,#7a0f0f,#a31515",
                   "crazy-max/ghaction-github-pages@v5", "target_branch: output"):
        assert needle in text, needle


def test_workflow_can_use_a_personal_token_when_one_is_added():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "GITHUB_TOKEN: ${{ secrets.PROFILE_TOKEN || secrets.GITHUB_TOKEN }}" in text


def test_workflow_stamps_the_readme_and_does_not_race():
    text = WORKFLOW.read_text(encoding="utf-8")
    for needle in ("concurrency:", "python scripts/stamp_readme.py README.md ${{ github.run_number }}",
                   "git pull --rebase", 'git commit -am "Refresh profile cards"'):
        assert needle in text, needle
