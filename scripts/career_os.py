from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "career-os.json"


DEFAULT_CONFIG = {
    "name": "Shreyanshu Srivastava",
    "github": "shreyanshucodes",
    "positioning": "business-minded builder working across automation, marketing, and software",
    "focus_areas": [
        "software projects",
        "business growth",
        "LinkedIn proof-of-work",
        "coding practice",
        "academic recovery",
    ],
}


def today() -> dt.date:
    return dt.date.today()


def read_config() -> dict:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n", encoding="utf-8")
        return DEFAULT_CONFIG
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def slugify(value: str) -> str:
    cleaned = []
    for char in value.lower().strip():
        if char.isalnum():
            cleaned.append(char)
        elif char in {" ", "-", "_"}:
            cleaned.append("-")
    slug = "".join(cleaned)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "untitled"


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def ask_list(prompt: str) -> list[str]:
    print(f"{prompt} Enter one per line. Leave blank when done.")
    items: list[str] = []
    while True:
        value = input("- ").strip()
        if not value:
            break
        items.append(value)
    return items


def write_if_missing(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return False
    path.write_text(content, encoding="utf-8")
    return True


def daily(args: argparse.Namespace) -> list[Path]:
    config = read_config()
    date = args.date or today().isoformat()
    date_obj = dt.date.fromisoformat(date)
    path = ROOT / "logs" / f"{date_obj:%Y}" / f"{date_obj:%m}" / f"{date}.md"

    if path.exists() and not args.force:
        print(f"Daily log already exists: {path.relative_to(ROOT)}")
        return [path]

    if args.quick:
        shipped = [args.shipped] if args.shipped else []
        learned = [args.learned] if args.learned else []
        next_steps = [args.next_step] if args.next_step else []
    else:
        print("Daily proof-of-work check-in")
        print("Keep it honest and small. One real thing is enough.")
        shipped = ask_list("What did you ship, practice, test, or document today?")
        learned = ask_list("What did you learn?")
        next_steps = ask_list("What should happen next?")

    if not shipped and not learned and not next_steps:
        print("Nothing recorded. Add a real shipped item, lesson, or next step; no streak entry created.")
        return []

    linkedin_angle = args.linkedin_angle
    if not linkedin_angle and not args.quick:
        linkedin_angle = ask("Possible LinkedIn angle", "Small progress compounds when it is documented.")

    content = f"""# Daily Log - {date}

## Identity Signal

{config["name"]} is building as a {config["positioning"]}.

## Work Done

{format_bullets(shipped)}

## Lessons

{format_bullets(learned)}

## Next Steps

{format_bullets(next_steps)}

## LinkedIn Angle

{linkedin_angle or "No post angle selected yet."}

## Tags

`proof-of-work` `career-os` `daily-log`
"""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    update_dashboard()
    print(f"Wrote {path.relative_to(ROOT)}")
    return [path, ROOT / "README.md"]


def format_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def leetcode(args: argparse.Namespace) -> list[Path]:
    date = args.date or today().isoformat()
    title = args.title or ask("Problem title")
    difficulty = args.difficulty or ask("Difficulty", "Easy")
    topic = args.topic or ask("Topic", "Arrays")
    path = ROOT / "leetcode-notes" / f"{date}-{slugify(title)}.md"

    approach = args.approach or ask("Approach summary", "Document the pattern, edge cases, and complexity.")
    complexity = args.complexity or ask("Complexity", "Time: O(n), Space: O(n)")

    content = f"""# {title}

Date: {date}
Difficulty: {difficulty}
Topic: {topic}

## Problem Pattern

Describe the pattern in your own words.

## Approach

{approach}

## Complexity

{complexity}

## Mistakes / Notes

- Add what confused you or what you want to remember.

## Tags

`leetcode` `coding-practice` `{slugify(topic)}`
"""

    write_if_missing(path, content)
    update_dashboard()
    print(f"Wrote {path.relative_to(ROOT)}")
    return [path, ROOT / "README.md"]


def weekly(args: argparse.Namespace) -> list[Path]:
    date = args.date or today().isoformat()
    end = dt.date.fromisoformat(date)
    start = end - dt.timedelta(days=6)
    logs = []
    for i in range(7):
        day = start + dt.timedelta(days=i)
        log_path = ROOT / "logs" / f"{day:%Y}" / f"{day:%m}" / f"{day.isoformat()}.md"
        if log_path.exists():
            logs.append(log_path)

    path = ROOT / "weekly-reviews" / f"{start.isoformat()}-to-{end.isoformat()}.md"
    included = "\n".join(f"- [{p.stem}](../{p.relative_to(ROOT).as_posix()})" for p in logs)
    if not included:
        included = "- No daily logs found for this week yet."

    content = f"""# Weekly Review - {start.isoformat()} to {end.isoformat()}

## Logs Included

{included}

## Shipped

- Summarize real outputs from the week.

## Business / Marketing

- Summarize experiments, client work, or pharmacy growth actions.

## Coding

- Summarize problems solved, concepts learned, or projects advanced.

## LinkedIn Draft

This week I worked on:

- 

The useful lesson:

- 

Next I am building:

- 
"""
    write_if_missing(path, content)
    update_dashboard()
    print(f"Wrote {path.relative_to(ROOT)}")
    return [path, ROOT / "README.md"]


def update_dashboard() -> None:
    config = read_config()
    logs = sorted((ROOT / "logs").glob("*/*/*.md")) if (ROOT / "logs").exists() else []
    leetcode_notes = sorted((ROOT / "leetcode-notes").glob("*.md")) if (ROOT / "leetcode-notes").exists() else []
    weekly_reviews = sorted((ROOT / "weekly-reviews").glob("*.md")) if (ROOT / "weekly-reviews").exists() else []

    latest_logs = "\n".join(
        f"- [{p.stem}]({p.relative_to(ROOT).as_posix()})" for p in logs[-7:]
    ) or "- No daily logs yet."

    readme = f"""# Career OS

A public proof-of-work system for {config["name"]}.

## Positioning

Building as a {config["positioning"]}.

## Metrics

- Daily logs: {len(logs)}
- Weekly reviews: {len(weekly_reviews)}
- Coding notes: {len(leetcode_notes)}

## Focus Areas

{format_bullets(config["focus_areas"])}

## Latest Logs

{latest_logs}

## System

This repo is maintained with `scripts/career_os.py`. The automation creates structure, but the entries should describe real work only.
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")


def run_git(paths: list[Path], push: bool) -> None:
    subprocess.run(["git", "status", "--short"], cwd=ROOT, check=True)
    subprocess.run(["git", "add", *[str(p.relative_to(ROOT)) for p in paths if p.exists()]], cwd=ROOT, check=True)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if diff.returncode == 0:
        print("No staged changes to commit.")
        return
    message = f"docs: update proof-of-work log {today().isoformat()}"
    subprocess.run(["git", "commit", "-m", message], cwd=ROOT, check=True)
    if push:
        subprocess.run(["git", "push"], cwd=ROOT, check=True)


def init_dirs() -> None:
    for folder in [
        "logs",
        "weekly-reviews",
        "projects",
        "leetcode-notes",
        "linkedin-drafts",
        "business-growth",
        "scripts",
    ]:
        (ROOT / folder).mkdir(parents=True, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Career OS proof-of-work automation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    daily_parser = subparsers.add_parser("daily", help="Create a daily proof-of-work log")
    daily_parser.add_argument("--date")
    daily_parser.add_argument("--force", action="store_true")
    daily_parser.add_argument("--quick", action="store_true")
    daily_parser.add_argument("--shipped")
    daily_parser.add_argument("--learned")
    daily_parser.add_argument("--next-step")
    daily_parser.add_argument("--linkedin-angle")
    daily_parser.add_argument("--commit", action="store_true")
    daily_parser.add_argument("--push", action="store_true")

    leetcode_parser = subparsers.add_parser("leetcode", help="Create a coding practice note")
    leetcode_parser.add_argument("--date")
    leetcode_parser.add_argument("--title")
    leetcode_parser.add_argument("--difficulty")
    leetcode_parser.add_argument("--topic")
    leetcode_parser.add_argument("--approach")
    leetcode_parser.add_argument("--complexity")
    leetcode_parser.add_argument("--commit", action="store_true")
    leetcode_parser.add_argument("--push", action="store_true")

    weekly_parser = subparsers.add_parser("weekly", help="Create a weekly review")
    weekly_parser.add_argument("--date")
    weekly_parser.add_argument("--commit", action="store_true")
    weekly_parser.add_argument("--push", action="store_true")

    args = parser.parse_args()
    init_dirs()

    if args.command == "daily":
        changed = daily(args)
    elif args.command == "leetcode":
        changed = leetcode(args)
    else:
        changed = weekly(args)

    if args.commit or args.push:
        run_git(changed, push=args.push)


if __name__ == "__main__":
    main()
