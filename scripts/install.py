#!/usr/bin/env python3
"""Install this harness into a target folder (e.g. the interview folder) without clobbering it.

  python3 /path/to/harness/scripts/install.py /path/to/interview [--no-skeleton]

- Copies files that do not exist yet; never overwrites (kit README.md, BRIEF.md, .mcp.json stay untouched).
- Merges .claude/settings.json (keeps any hooks/permissions the kit's setup added).
- Appends harness entries to .gitignore, including .interview/ (never commit the recorder).
- git init + first commit if the folder is not a repo yet.
- --no-skeleton: skip src/, tests/, evals/, prompts/, pyproject.toml, Makefile (if the brief dictates another stack).
"""
import json
import pathlib
import shutil
import subprocess
import sys

SRC = pathlib.Path(__file__).resolve().parent.parent
SKIP_ALWAYS = {
    ".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".harness", ".worktrees",
    "HARNESS_SETUP.md", "uv.lock", "traces", "results", "LICENSE", ".github", "install.sh",
}
SKELETON = {"src", "tests", "evals", "prompts", "pyproject.toml", "Makefile"}
IGNORE = [".interview/", ".worktrees/", ".harness/", ".venv/", "__pycache__/", ".pytest_cache/", "traces/", "evals/results/", ".env"]


def merge_settings(dst: pathlib.Path, src: pathlib.Path) -> None:
    mine = json.loads(src.read_text())
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(mine, indent=2))
        return
    theirs = json.loads(dst.read_text())
    hooks = theirs.setdefault("hooks", {})
    for event, entries in mine.get("hooks", {}).items():
        existing = json.dumps(hooks.get(event, []))
        for e in entries:
            if json.dumps(e) not in existing:
                hooks.setdefault(event, []).append(e)
    allow = theirs.setdefault("permissions", {}).setdefault("allow", [])
    for rule in mine.get("permissions", {}).get("allow", []):
        if rule not in allow:
            allow.append(rule)
    dst.write_text(json.dumps(theirs, indent=2))


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 1
    dst_root = pathlib.Path(args[0]).resolve()
    skip = SKIP_ALWAYS | (SKELETON if "--no-skeleton" in sys.argv else set())
    copied, kept = [], []

    for f in sorted(SRC.rglob("*")):
        rel = f.relative_to(SRC)
        if f.is_dir() or rel.parts[0] in skip or any(p in SKIP_ALWAYS for p in rel.parts):
            continue
        if rel.as_posix() in (".claude/settings.json", "README.md", ".gitignore"):
            continue
        out = dst_root / rel
        if out.exists():
            kept.append(rel.as_posix())
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, out)
        copied.append(rel.as_posix())

    # harness README goes in as HARNESS.md so the kit README.md is never touched
    if not (dst_root / "HARNESS.md").exists():
        shutil.copy2(SRC / "README.md", dst_root / "HARNESS.md")
        copied.append("HARNESS.md")

    merge_settings(dst_root / ".claude" / "settings.json", SRC / ".claude" / "settings.json")

    gi = dst_root / ".gitignore"
    lines = gi.read_text().splitlines() if gi.exists() else []
    gi.write_text("\n".join(lines + [x for x in IGNORE if x not in lines]) + "\n")

    for s in (dst_root / "scripts").glob("*"):
        s.chmod(0o755)

    if shutil.which("uv") and (dst_root / "pyproject.toml").exists() and not (dst_root / "uv.lock").exists():
        subprocess.run(["uv", "lock", "-q"], cwd=dst_root, check=False)  # lanes must share one tracked lock file

    if not (dst_root / ".git").exists():
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=dst_root, check=True)
        subprocess.run(["git", "add", "-A"], cwd=dst_root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "process: add agent harness"], cwd=dst_root, check=False)
    print(f"copied {len(copied)} files, kept {len(kept)} existing: {', '.join(kept) or '-'}")
    print("merged .claude/settings.json and .gitignore")
    if subprocess.run(["git", "status", "--porcelain"], cwd=dst_root, capture_output=True, text=True).stdout.strip():
        print("uncommitted changes: run  git add -A && git commit -m 'process: add agent harness'  before opening lanes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
