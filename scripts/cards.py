"""Draw the noir profile cards from GitHub data. Standard library only.

Run: python scripts/cards.py --user noorgx --out dist   (needs GITHUB_TOKEN)
"""
import argparse
import json
import os
import sys
import textwrap
import urllib.request
from datetime import date, datetime
from pathlib import Path
from xml.sax.saxutils import escape

BLACK, INK, LINE = "#0b0b0b", "#161616", "#2a2a2a"
BONE, ASH, BLOOD, DRIED = "#e8e2d6", "#8a8378", "#a31515", "#7a0f0f"
SERIF = "Georgia, 'Times New Roman', serif"
MONO = "'Courier New', monospace"

RANKS = ["Associate", "Soldier", "Capo", "Underboss", "Boss", "Don"]
THRESHOLDS = {  # value needed for each rank above Associate
    "Commits": [100, 500, 1000, 2500, 5000],
    "Pull requests": [5, 25, 50, 100, 250],
    "Stars": [5, 25, 100, 250, 1000],
    "Followers": [10, 50, 100, 250, 1000],
    "Repositories": [5, 15, 30, 50, 100],
    "Years on GitHub": [1, 2, 4, 6, 10],
}
EXCLUDED_LANGUAGES = {"Jupyter Notebook"}  # notebooks store outputs, so their byte count swamps real code
HONOUR_KEYS = {
    "Commits": "commits", "Pull requests": "pull_requests", "Stars": "stars",
    "Followers": "followers", "Repositories": "repositories", "Years on GitHub": "years",
}
QUOTES = [
    ("I'm gonna make him an offer he can't refuse.", "The Godfather"),
    ("Leave the gun. Take the cannoli.", "The Godfather"),
    ("Never tell anybody outside the family what you're thinking.", "The Godfather"),
    ("Great men are not born great, they grow great.", "The Godfather"),
    ("Keep your friends close, but your enemies closer.", "The Godfather Part II"),
    ("Just when I thought I was out, they pull me back in.", "The Godfather Part III"),
    ("As far back as I can remember, I always wanted to be a gangster.", "Goodfellas"),
    ("Never rat on your friends, and always keep your mouth shut.", "Goodfellas"),
    ("Say hello to my little friend.", "Scarface"),
    ("The world is yours.", "Scarface"),
    ("All I have in this world is my word, and I don't break it for nobody.", "Scarface"),
    ("The greatest trick the devil ever pulled was convincing the world he didn't exist.", "The Usual Suspects"),
    ("Forget it, Jake. It's Chinatown.", "Chinatown"),
    ("Round up the usual suspects.", "Casablanca"),
    ("The stuff that dreams are made of.", "The Maltese Falcon"),
    ("I am the one who knocks.", "Breaking Bad"),
    ("You talkin' to me?", "Taxi Driver"),
    ("Get busy living, or get busy dying.", "The Shawshank Redemption"),
    ("What we've got here is failure to communicate.", "Cool Hand Luke"),
    ("Why so serious?", "The Dark Knight"),
    ("You either die a hero, or you live long enough to see yourself become the villain.", "The Dark Knight"),
    ("By order of the Peaky Blinders.", "Peaky Blinders"),
    ("You come at the king, you best not miss.", "The Wire"),
    ("All in the game, yo. All in the game.", "The Wire"),
    ("Money never sleeps, pal.", "Wall Street"),
    ("Greed, for lack of a better word, is good.", "Wall Street"),
    ("Made it, Ma! Top of the world!", "White Heat"),
]


def esc(value) -> str:
    return escape(str(value), {'"': "&quot;"})


def rank_for(category: str, value: int) -> str:
    return RANKS[sum(value >= t for t in THRESHOLDS[category])]


def quote_for(day: date) -> tuple[str, str]:
    return QUOTES[day.toordinal() % len(QUOTES)]


STYLE = f"""
  .t {{ font: 700 15px {SERIF}; fill: {BLOOD}; letter-spacing: 4px; }}
  .l {{ font: 400 15px {SERIF}; fill: {BONE}; }}
  .n {{ font: 700 15px {MONO}; fill: {BONE}; }}
  .s {{ font: 400 11px {MONO}; fill: {ASH}; letter-spacing: 2px; }}
  .big {{ font: 700 20px {SERIF}; fill: {BONE}; }}
  .don {{ fill: {BLOOD}; }}
  .q {{ font: italic 400 19px {SERIF}; fill: {BONE}; }}
  .in {{ opacity: 0; animation: in 0.6s ease-out forwards; }}
  .bar {{ transform-box: fill-box; transform-origin: left; transform: scaleX(0); animation: grow 1s ease-out forwards; }}
  .rule {{ stroke-dasharray: 1000; stroke-dashoffset: 1000; animation: draw 1.2s ease-out forwards; }}
  @keyframes in {{ to {{ opacity: 1; }} }}
  @keyframes grow {{ to {{ transform: scaleX(1); }} }}
  @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
  .cur {{ animation: blink 1s steps(2, start) infinite; }}
  @keyframes blink {{ to {{ visibility: hidden; }} }}
"""


def frame(width: int, height: int, title: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">'
        f"<style>{STYLE}</style>"
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="3" fill="{BLACK}" stroke="{LINE}"/>'
        f'<text x="25" y="38" class="t">{esc(title.upper())}</text>'
        f'<line x1="25" y1="50" x2="{width - 25}" y2="50" stroke="{BLOOD}" stroke-width="1" class="rule"/>'
        f"{body}</svg>"
    )


def delay(i: int, start: float = 0.3, step: float = 0.15) -> str:
    return f'style="animation-delay:{start + i * step:.2f}s"'


def render_record(stats: dict) -> str:
    rows = [
        ("Commits, past year", stats["commits"]),
        ("Pull requests", stats["pull_requests"]),
        ("Issues", stats["issues"]),
        ("Stars earned", stats["stars"]),
        ("Repos contributed to", stats["contributed_to"]),
    ]
    body = "".join(
        f'<g class="in" {delay(i)}>'
        f'<text x="25" y="{78 + i * 24}" class="l">{esc(label)}</text>'
        f'<text x="470" y="{78 + i * 24}" text-anchor="end" class="n">{esc(f"{value:,}")}</text>'
        f"</g>"
        for i, (label, value) in enumerate(rows)
    )
    return frame(495, 195, "The Record", body)


def render_languages(languages: dict[str, int]) -> str:
    languages = {name: size for name, size in languages.items() if name not in EXCLUDED_LANGUAGES}
    total = sum(languages.values())
    top = sorted(languages.items(), key=lambda kv: -kv[1])[:6]
    if not top:
        return frame(495, 210, "Weapons of Choice", '<text x="25" y="90" class="l">No public code yet.</text>')
    shares = [round(size / total * 100, 1) for _, size in top]
    body = ""
    for i, ((name, _), share) in enumerate(zip(top, shares)):
        y = 78 + i * 22
        width = max(2, round(share / max(shares) * 250))
        body += (
            f'<g class="in" {delay(i)}>'
            f'<text x="25" y="{y}" class="l">{esc(name)}</text>'
            f'<rect x="165" y="{y - 11}" width="250" height="10" fill="{INK}"/>'
            f'<rect x="165" y="{y - 11}" width="{width}" height="10" fill="{BLOOD if i == 0 else DRIED}" class="bar" {delay(i, 0.5)}/>'
            f'<text x="470" y="{y}" text-anchor="end" class="n">{share}%</text>'
            f"</g>"
        )
    return frame(495, 210, "Weapons of Choice", body)


def render_honours(stats: dict) -> str:
    body = ""
    for i, (category, key) in enumerate(HONOUR_KEYS.items()):
        col, row = i % 3, i // 3
        x, y = 25 + col * 265, 70 + row * 78
        value = stats[key]
        rank = rank_for(category, value)
        klass = "big don" if rank == "Don" else "big"
        body += (
            f'<g class="in" {delay(i, 0.3, 0.2)}>'
            f'<rect x="{x}" y="{y}" width="250" height="64" fill="{INK}" stroke="{LINE}"/>'
            f'<rect x="{x}" y="{y}" width="3" height="64" fill="{BLOOD}"/>'
            f'<text x="{x + 16}" y="{y + 20}" class="s">{esc(category.upper())}</text>'
            f'<text x="{x + 16}" y="{y + 47}" class="{klass}">{esc(rank)}</text>'
            f'<text x="{x + 236}" y="{y + 47}" text-anchor="end" class="n">{esc(f"{value:,}")}</text>'
            f"</g>"
        )
    return frame(830, 240, "Honours", body)


def render_word(day: date) -> str:
    text, source = quote_for(day)
    lines = textwrap.wrap(f"“{text}”", width=70)
    spans = "".join(
        f'<tspan x="415" dy="{0 if i == 0 else 28}">{esc(line)}</tspan>' for i, line in enumerate(lines)
    )
    body = (
        f'<text x="415" y="{88 if len(lines) == 1 else 80}" text-anchor="middle" class="q in" {delay(0)}>{spans}</text>'
        f'<text x="415" y="{128 if len(lines) == 1 else 140}" text-anchor="middle" class="s in" {delay(1, 0.9)}>{esc(source.upper())}</text>'
    )
    return frame(830, 160, "The Word", body)


EVENTS_URL = "https://api.github.com/users/{login}/events/public?per_page=100"
MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()


def fetch_events(login: str, token: str, opener=urllib.request.urlopen) -> list[dict] | None:
    """Latest public events, or None if GitHub can't be reached. The card then says it's quiet."""
    request = urllib.request.Request(
        EVENTS_URL.format(login=login),
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                 "User-Agent": "noorgx-profile-cards"},
    )
    try:
        with opener(request, timeout=60) as response:
            events = json.load(response)
    except (OSError, ValueError) as e:
        print(f"Could not read public events: {e}", file=sys.stderr)
        return None
    return events if isinstance(events, list) else None


def describe(event: dict) -> str | None:
    kind, payload = event.get("type"), event.get("payload") or {}
    action = payload.get("action")
    if kind == "PushEvent":
        return "Pushed to"
    if kind == "PullRequestEvent":
        if action == "opened":
            return "Opened a pull request in"
        if action == "closed" and (payload.get("pull_request") or {}).get("merged"):
            return "Merged a pull request in"
    if kind == "CreateEvent" and payload.get("ref_type") == "repository":
        return "Created repository"
    if kind == "ReleaseEvent" and action == "published":
        return f"Released {(payload.get('release') or {}).get('tag_name') or 'a version'} of"
    if kind == "IssuesEvent" and action in ("opened", "closed"):
        return f"{action.capitalize()} an issue in"
    if kind == "PublicEvent":
        return "Made public"
    if kind == "ForkEvent":
        return "Forked"
    if kind == "WatchEvent":
        return "Starred"
    return None


def summarize_events(events: list[dict] | None, limit: int = 6) -> list[tuple[str, str, str]]:
    """(date, action, repo) lines, newest first. Real work is picked first; stars only fill empty slots."""
    work, stars, pushes = [], [], set()
    for event in events or []:
        text = describe(event)
        if not text:
            continue
        when = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
        repo = (event.get("repo") or {}).get("name", "")
        if text == "Pushed to":
            if (repo, when.date()) in pushes:
                continue
            pushes.add((repo, when.date()))
        (stars if text == "Starred" else work).append((when, text, repo))
    chosen = sorted((work + stars)[:limit], key=lambda line: line[0], reverse=True)
    return [(f"{when.day:02d} {MONTHS[when.month - 1]}", text, repo) for when, text, repo in chosen]


def render_moves(moves: list[tuple[str, str, str]]) -> str:
    if not moves:
        return frame(830, 130, "Last Moves", '<text x="25" y="90" class="l">Quiet lately.</text>')
    body = ""
    for i, (day, text, repo) in enumerate(moves):
        y = 82 + i * 26
        body += (
            f'<g class="in" {delay(i, 0.3, 0.35)}>'
            f'<text x="25" y="{y}" class="n" style="fill:{ASH}">{esc(day)}</text>'
            f'<text x="110" y="{y}" class="l">{esc(text)} <tspan style="fill:{BLOOD}">{esc(repo)}</tspan></text>'
            f"</g>"
        )
    y = 82 + len(moves) * 26
    body += (f'<g class="in" {delay(len(moves), 0.3, 0.35)}>'
             f'<rect x="110" y="{y - 13}" width="9" height="15" fill="{BLOOD}" class="cur"/></g>')
    return frame(830, y + 22, "Last Moves", body)


QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]) { totalCount }
    contributionsCollection { totalCommitContributions restrictedContributionsCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
      }
    }
  }
}
"""


def fetch(login: str, token: str, opener=urllib.request.urlopen) -> dict:
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "noorgx-profile-cards"},
    )
    with opener(request, timeout=60) as response:
        body = json.load(response)
    user = (body.get("data") or {}).get("user")
    if not user:
        sys.exit(f"GitHub API error: {body.get('errors')}")
    if body.get("errors"):
        # A token may be refused one field (for example repositoriesContributedTo); draw the rest.
        print(f"Some fields were not returned: {body['errors']}", file=sys.stderr)
    return user


def total(user: dict, field: str) -> int:
    return (user.get(field) or {}).get("totalCount") or 0


def summarize(user: dict, today: date) -> dict:
    languages: dict[str, int] = {}
    stars = 0
    for repo in (user.get("repositories") or {}).get("nodes") or []:
        stars += repo.get("stargazerCount") or 0
        for edge in (repo.get("languages") or {}).get("edges") or []:
            name = edge["node"]["name"]
            languages[name] = languages.get(name, 0) + edge["size"]
    created = datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00")).date()
    contributions = user.get("contributionsCollection") or {}
    return {
        "commits": (contributions.get("totalCommitContributions") or 0)
                   + (contributions.get("restrictedContributionsCount") or 0),
        "pull_requests": total(user, "pullRequests"),
        "issues": total(user, "issues"),
        "stars": stars,
        "contributed_to": total(user, "repositoriesContributedTo"),
        "followers": total(user, "followers"),
        "repositories": total(user, "repositories"),
        "years": (today - created).days // 365,
        "languages": languages,
    }


def main(argv: list[str] | None = None, opener=urllib.request.urlopen, today: date | None = None) -> int:
    parser = argparse.ArgumentParser(description="Draw the noir profile cards.")
    parser.add_argument("--user", required=True)
    parser.add_argument("--out", default="dist")
    args = parser.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN is not set.")
    today = today or date.today()
    stats = summarize(fetch(args.user, token, opener), today)
    moves = summarize_events(fetch_events(args.user, token, opener))
    cards = {
        "moves.svg": render_moves(moves),
        "record.svg": render_record(stats),
        "languages.svg": render_languages(stats["languages"]),
        "honours.svg": render_honours(stats),
        "word.svg": render_word(today),
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, svg in cards.items():
        (out / name).write_text(svg, encoding="utf-8")
    print(f"Wrote {len(cards)} cards to {out}: {stats['commits']} commits, {stats['stars']} stars.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
