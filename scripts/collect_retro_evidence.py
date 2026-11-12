#!/usr/bin/env python3
"""Gather the evidence a retro needs into one markdown digest.

Collects: QA FAIL reports, the agent log, failing cases from the latest eval run,
recent process: commits, and earlier retro proposals (so the retro does not repeat itself).

  python3 scripts/collect_retro_evidence.py                 # prints the digest
  python3 scripts/collect_retro_evidence.py --root <dir>    # for another project folder
"""
import argparse
import json
import pathlib
import re
import subprocess

DEFAULT_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_AGENT_LOG_LINES = 80
MAX_PROCESS_COMMITS = 20


def collect_qa_failures(project_root: pathlib.Path) -> list[str]:
    """Return every '## QA: FAIL' section from _docs/qa/*.md, labelled with its issue file."""
    qa_failure_sections = []
    qa_reports_directory = project_root / "_docs" / "qa"
    for qa_report_path in sorted(qa_reports_directory.glob("[0-9]*.md")):
        qa_report_text = qa_report_path.read_text()

        # Split the report into its '## QA:' sections and keep only the FAIL ones.
        report_sections = re.split(r"(?m)^(?=## QA:)", qa_report_text)
        for report_section in report_sections:
            if report_section.startswith("## QA: FAIL"):
                qa_failure_sections.append(f"### {qa_report_path.name}\n{report_section.strip()}")
    return qa_failure_sections


def collect_agent_log_tail(project_root: pathlib.Path) -> list[str]:
    agent_log_path = project_root / "_docs" / "agent-log.md"
    if not agent_log_path.exists():
        return []

    # Only event lines, which start with a time like "10:05 |"; skip the header and instructions.
    event_line_pattern = re.compile(r"^\d{1,2}:\d{2}\s*\|")
    event_lines = [log_line for log_line in agent_log_path.read_text().splitlines() if event_line_pattern.match(log_line)]
    return event_lines[-MAX_AGENT_LOG_LINES:]


def collect_latest_eval_failures(project_root: pathlib.Path) -> tuple[str | None, list[dict]]:
    """Return (name of the latest eval results file, its failing cases)."""
    eval_results_directory = project_root / "evals" / "results"
    eval_result_files = sorted(eval_results_directory.glob("*.json"))
    if not eval_result_files:
        return None, []

    latest_eval_results_path = eval_result_files[-1]
    latest_eval_results = json.loads(latest_eval_results_path.read_text())
    failing_eval_cases = [eval_result for eval_result in latest_eval_results if not eval_result["pass"]]
    return latest_eval_results_path.name, failing_eval_cases


def collect_recent_process_commits(project_root: pathlib.Path) -> list[str]:
    git_log_process = subprocess.run(
        ["git", "log", f"-{MAX_PROCESS_COMMITS}", "--grep=^process:", "--format=%h %s"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return [commit_line for commit_line in git_log_process.stdout.splitlines() if commit_line.strip()]


def collect_previous_retro_titles(project_root: pathlib.Path) -> list[str]:
    retros_directory = project_root / "_docs" / "retros"
    previous_retro_titles = []
    for retro_path in sorted(retros_directory.glob("[0-9]*.md")):
        retro_lines = retro_path.read_text().splitlines()
        retro_title = retro_lines[0].lstrip("# ") if retro_lines else "(empty)"
        previous_retro_titles.append(f"{retro_path.name}: {retro_title}")
    return previous_retro_titles


def build_evidence_digest(project_root: pathlib.Path) -> str:
    qa_failure_sections = collect_qa_failures(project_root)
    agent_log_lines = collect_agent_log_tail(project_root)
    latest_eval_file_name, failing_eval_cases = collect_latest_eval_failures(project_root)
    process_commit_lines = collect_recent_process_commits(project_root)
    previous_retro_titles = collect_previous_retro_titles(project_root)

    digest_parts = ["# Retro evidence\n"]

    digest_parts.append(f"## QA failures ({len(qa_failure_sections)})")
    digest_parts.append("\n\n".join(qa_failure_sections) if qa_failure_sections else "none")

    digest_parts.append(f"\n## Agent log (last {len(agent_log_lines)} events)")
    digest_parts.append("\n".join(agent_log_lines) if agent_log_lines else "none")

    digest_parts.append(f"\n## Failing eval cases ({len(failing_eval_cases)}) from {latest_eval_file_name or 'no eval run yet'}")
    for failing_eval_case in failing_eval_cases:
        case_notes = "; ".join(failing_eval_case.get("notes", []))
        digest_parts.append(f"- {failing_eval_case['id']} {failing_eval_case['tags']}: {case_notes} (trace: {failing_eval_case['trace']})")
    if not failing_eval_cases:
        digest_parts.append("none")

    digest_parts.append("\n## Recent process: commits (fixes already made)")
    digest_parts.append("\n".join(process_commit_lines) if process_commit_lines else "none")

    digest_parts.append("\n## Previous retros (do not repeat these)")
    digest_parts.append("\n".join(previous_retro_titles) if previous_retro_titles else "none")

    return "\n".join(digest_parts) + "\n"


def main() -> None:
    argument_parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argument_parser.add_argument("--root", type=pathlib.Path, default=DEFAULT_PROJECT_ROOT)
    parsed_arguments = argument_parser.parse_args()
    print(build_evidence_digest(parsed_arguments.root.resolve()))


if __name__ == "__main__":
    main()
