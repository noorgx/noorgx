import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import cards  # noqa: E402

STATS = {
    "commits": 1234, "pull_requests": 56, "issues": 7, "stars": 89, "contributed_to": 12,
    "followers": 14, "repositories": 31, "years": 5,
    "languages": {"Python": 600, "C++": 200, "JavaScript": 100, "Go": 50, "Rust": 30, "HTML": 15, "Shell": 5},
}


def parse(svg):
    return ET.fromstring(svg)


def text_of(svg):
    return " ".join(t for t in parse(svg).itertext())


def test_record_shows_every_number():
    svg = cards.render_record(STATS)
    body = text_of(svg)
    for value in ("1,234", "56", "7", "89", "12"):
        assert value in body
    assert "THE RECORD" in body


def test_record_with_zeros_still_renders():
    empty = {k: 0 for k in STATS} | {"languages": {}}
    assert "0" in text_of(cards.render_record(empty))


def test_languages_top_six_with_percentages_summing_to_about_100():
    body = text_of(cards.render_languages(STATS["languages"]))
    assert "Shell" not in body
    percents = [float(p.rstrip("%")) for p in body.split() if p.endswith("%")]
    assert len(percents) == 6
    assert 99.0 <= sum(percents) <= 100.0


def test_languages_escape_special_names():
    svg = cards.render_languages({"C++": 10, "C#": 5, "A<B&C": 1})
    names = "".join(parse(svg).itertext())
    assert "A<B&C" in names and "C++" in names and "C#" in names


def test_languages_empty_says_so():
    assert "No public code yet" in text_of(cards.render_languages({}))


def test_rank_thresholds():
    assert cards.rank_for("Commits", 0) == "Associate"
    assert cards.rank_for("Commits", 99) == "Associate"
    assert cards.rank_for("Commits", 100) == "Soldier"
    assert cards.rank_for("Commits", 5000) == "Don"
    assert cards.rank_for("Years on GitHub", 5) == "Underboss"


def test_honours_show_six_ranks():
    body = text_of(cards.render_honours(STATS))
    for category in cards.THRESHOLDS:
        assert category.upper() in body
    assert sum(body.count(rank) for rank in cards.RANKS) >= 6


def test_quote_is_stable_per_day_and_changes_between_days():
    assert cards.quote_for(date(2026, 9, 24)) == cards.quote_for(date(2026, 9, 24))
    assert cards.quote_for(date(2026, 9, 24)) != cards.quote_for(date(2026, 9, 25))


def test_every_quote_fits_on_the_card():
    for i in range(len(cards.QUOTES)):
        day = date.fromordinal(date(2026, 1, 1).toordinal() + i)
        svg = cards.render_word(day)
        lines = list(parse(svg).iter("{http://www.w3.org/2000/svg}tspan"))
        assert 1 <= len(lines) <= 2
        assert all(len(t.text or "") <= 70 for t in lines)


def test_no_emoji_in_any_card():
    for svg in (cards.render_record(STATS), cards.render_languages(STATS["languages"]),
                cards.render_honours(STATS), cards.render_word(date(2026, 9, 24))):
        assert all(ord(ch) < 0x2190 for ch in svg)


import io  # noqa: E402
import json  # noqa: E402

import pytest  # noqa: E402

USER = {
    "createdAt": "2020-03-01T10:00:00Z",
    "followers": {"totalCount": 14},
    "pullRequests": {"totalCount": 56},
    "issues": {"totalCount": 7},
    "repositoriesContributedTo": {"totalCount": 12},
    "contributionsCollection": {"totalCommitContributions": 1200, "restrictedContributionsCount": 34},
    "repositories": {"totalCount": 31, "nodes": [
        {"stargazerCount": 80, "languages": {"edges": [
            {"size": 600, "node": {"name": "Python"}}, {"size": 200, "node": {"name": "C++"}}]}},
        {"stargazerCount": 9, "languages": {"edges": [{"size": 100, "node": {"name": "Python"}}]}},
        {"stargazerCount": 0, "languages": {"edges": []}},
    ]},
}


def test_summarize_totals():
    stats = cards.summarize(USER, date(2026, 9, 24))
    assert stats["commits"] == 1234
    assert stats["stars"] == 89
    assert stats["languages"] == {"Python": 700, "C++": 200}
    assert stats["years"] == 6
    assert stats["repositories"] == 31 and stats["followers"] == 14


def test_summarize_tolerates_null_languages():
    user = json.loads(json.dumps(USER))
    user["repositories"]["nodes"][0]["languages"] = None
    assert cards.summarize(user, date(2026, 9, 24))["languages"] == {"Python": 100}


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def opener_returning(payload):
    def opener(request, timeout=None):
        opener.request = request
        return FakeResponse(json.dumps(payload).encode())
    return opener


def test_main_writes_every_card(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "tok")
    opener = opener_returning({"data": {"user": USER}})
    assert cards.main(["--user", "noorgx", "--out", str(tmp_path)], opener=opener, today=date(2026, 9, 24)) == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == ["honours.svg", "languages.svg", "moves.svg", "record.svg", "word.svg"]
    assert opener.request.get_header("Authorization") == "Bearer tok"


def test_main_api_error_writes_nothing_and_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "tok")
    opener = opener_returning({"errors": [{"message": "Could not resolve to a User"}], "data": {"user": None}})
    with pytest.raises(SystemExit) as exit_info:
        cards.main(["--user", "ghost", "--out", str(tmp_path)], opener=opener)
    assert exit_info.value.code != 0
    assert list(tmp_path.iterdir()) == []


def test_main_without_token_fails(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        cards.main(["--user", "noorgx", "--out", str(tmp_path)])


def test_honours_plaques_have_equal_side_margins():
    root = parse(cards.render_honours(STATS))
    width = int(root.get("width"))
    plaques = [r for r in root.iter("{http://www.w3.org/2000/svg}rect") if r.get("width") == "250"]
    left = min(int(r.get("x")) for r in plaques)
    right = max(int(r.get("x")) + 250 for r in plaques)
    assert left == 25 and width - right == 25


def test_languages_leave_out_jupyter_notebooks():
    body = text_of(cards.render_languages({"Jupyter Notebook": 9000, "Python": 100, "Go": 100}))
    assert "Jupyter" not in body
    assert "50.0%" in body


def test_main_uses_partial_data_when_one_field_is_refused(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "tok")
    user = json.loads(json.dumps(USER))
    user["repositoriesContributedTo"] = None
    payload = {"data": {"user": user}, "errors": [{"path": ["user", "repositoriesContributedTo"], "message": "Resource not accessible by integration"}]}
    assert cards.main(["--user", "noorgx", "--out", str(tmp_path)], opener=opener_returning(payload), today=date(2026, 9, 24)) == 0
    assert len(list(tmp_path.iterdir())) == 5


def test_record_says_past_year_and_matches_streak_card_height():
    svg = cards.render_record(STATS)
    assert "Commits, past year" in text_of(svg)
    assert "this year" not in text_of(svg)
    assert parse(svg).get("height") == "195"


def event(type_, repo, when, **payload):
    return {"type": type_, "repo": {"name": repo}, "created_at": when, "payload": payload}


def test_moves_describe_each_kind_of_event():
    events = [
        event("PushEvent", "noorgx/noorgx", "2026-09-24T17:36:16Z", ref="refs/heads/main"),
        event("PullRequestEvent", "a/b", "2026-09-23T10:00:00Z", action="opened", pull_request={}),
        event("PullRequestEvent", "a/c", "2026-09-22T10:00:00Z", action="closed", pull_request={"merged": True}),
        event("CreateEvent", "noorgx/tool", "2026-09-21T10:00:00Z", ref_type="repository"),
        event("ReleaseEvent", "noorgx/tool", "2026-09-20T10:00:00Z", action="published", release={"tag_name": "v1.0"}),
        event("IssuesEvent", "x/y", "2026-09-19T10:00:00Z", action="opened"),
    ]
    assert cards.summarize_events(events) == [
        ("24 SEP", "Pushed to", "noorgx/noorgx"),
        ("23 SEP", "Opened a pull request in", "a/b"),
        ("22 SEP", "Merged a pull request in", "a/c"),
        ("21 SEP", "Created repository", "noorgx/tool"),
        ("20 SEP", "Released v1.0 of", "noorgx/tool"),
        ("19 SEP", "Opened an issue in", "x/y"),
    ]


def test_moves_merge_pushes_to_the_same_repo_on_the_same_day():
    events = [event("PushEvent", "r/r", "2026-09-24T18:00:00Z"), event("PushEvent", "r/r", "2026-09-24T09:00:00Z"),
              event("PushEvent", "r/r", "2026-09-23T09:00:00Z")]
    assert [m[0] for m in cards.summarize_events(events)] == ["24 SEP", "23 SEP"]


def test_moves_put_real_work_first_and_use_stars_only_to_fill():
    events = [event("WatchEvent", f"s/{i}", f"2026-09-2{i}T10:00:00Z", action="started") for i in range(1, 9)]
    events.insert(3, event("ForkEvent", "f/f", "2026-08-31T19:34:18Z", action="forked"))
    moves = cards.summarize_events(events)
    assert len(moves) == 6
    assert moves[-1] == ("31 AUG", "Forked", "f/f")
    assert [text for _, text, _ in moves].count("Starred") == 5


def test_moves_skip_events_they_do_not_understand():
    events = [event("MemberEvent", "a/b", "2026-09-24T10:00:00Z"),
              event("PullRequestEvent", "a/b", "2026-09-24T10:00:00Z", action="labeled", pull_request={})]
    assert cards.summarize_events(events) == []


def test_moves_card_lists_lines_and_escapes_repo_names():
    svg = cards.render_moves([("24 SEP", "Pushed to", "a/<b>&c")])
    body = text_of(svg)
    assert "LAST MOVES" in body and "24 SEP" in body and "a/<b>&c" in body


def test_moves_card_when_quiet_or_fetch_failed():
    assert "Quiet lately." in text_of(cards.render_moves([]))
    assert cards.summarize_events(None) == []


def test_fetch_events_returns_none_on_network_error():
    def broken(request, timeout=None):
        raise OSError("down")
    assert cards.fetch_events("noorgx", "tok", broken) is None


def routed_opener(graphql_payload, events_payload):
    def opener(request, timeout=None):
        payload = graphql_payload if "graphql" in request.full_url else events_payload
        return FakeResponse(json.dumps(payload).encode())
    return opener


def test_main_writes_the_moves_card(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "tok")
    opener = routed_opener({"data": {"user": USER}}, [event("ForkEvent", "f/f", "2026-08-31T19:34:18Z")])
    cards.main(["--user", "noorgx", "--out", str(tmp_path)], opener=opener, today=date(2026, 9, 24))
    assert "f/f" in text_of((tmp_path / "moves.svg").read_text(encoding="utf-8"))


def test_moves_are_listed_newest_first_after_choosing_them():
    events = [event("WatchEvent", "s/new", "2026-09-24T10:00:00Z"),
              event("ForkEvent", "f/old", "2026-08-31T10:00:00Z")]
    assert [repo for _, _, repo in cards.summarize_events(events)] == ["s/new", "f/old"]
