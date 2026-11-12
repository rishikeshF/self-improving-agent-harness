#!/usr/bin/env python3
"""Regression check: compare the two most recent eval runs.

Exits 1 if any tag's pass rate dropped, or any case that passed before now fails.
Used by /retro to decide whether a prompt or tool change is kept or reverted.

  python3 scripts/compare_eval_runs.py                          # latest vs the run before it
  python3 scripts/compare_eval_runs.py <before.json> <after.json>
"""
import json
import pathlib
import sys

EVAL_RESULTS_DIRECTORY = pathlib.Path(__file__).resolve().parent.parent / "evals" / "results"


def pass_rate_by_tag(eval_results: list[dict]) -> dict[str, float]:
    passed_count_by_tag: dict[str, int] = {}
    total_count_by_tag: dict[str, int] = {}
    for eval_result in eval_results:
        for tag in eval_result["tags"]:
            total_count_by_tag[tag] = total_count_by_tag.get(tag, 0) + 1
            if eval_result["pass"]:
                passed_count_by_tag[tag] = passed_count_by_tag.get(tag, 0) + 1

    return {tag: passed_count_by_tag.get(tag, 0) / total_count_by_tag[tag] for tag in total_count_by_tag}


def compare_eval_runs(results_before: list[dict], results_after: list[dict]) -> tuple[bool, list[str]]:
    """Return (no_regression, report_lines)."""
    report_lines = []
    no_regression = True

    pass_rates_before = pass_rate_by_tag(results_before)
    pass_rates_after = pass_rate_by_tag(results_after)
    for tag in sorted(set(pass_rates_before) | set(pass_rates_after)):
        rate_before = pass_rates_before.get(tag)
        rate_after = pass_rates_after.get(tag)
        if rate_before is None or rate_after is None:
            report_lines.append(f"{tag:<16} only in one run, not compared")
            continue

        if rate_after < rate_before:
            no_regression = False
            change_label = "REGRESSED"
        elif rate_after > rate_before:
            change_label = "improved"
        else:
            change_label = "same"
        report_lines.append(f"{tag:<16} {rate_before:.0%} -> {rate_after:.0%}  {change_label}")

    # A case can regress even if its tag's overall rate stays flat (another case improved).
    passed_case_ids_before = {eval_result["id"] for eval_result in results_before if eval_result["pass"]}
    failed_case_ids_after = {eval_result["id"] for eval_result in results_after if not eval_result["pass"]}
    newly_failing_case_ids = sorted(passed_case_ids_before & failed_case_ids_after)
    if newly_failing_case_ids:
        no_regression = False
        report_lines.append(f"newly failing cases: {', '.join(newly_failing_case_ids)}")

    return no_regression, report_lines


def main() -> int:
    if len(sys.argv) == 3:
        before_results_path = pathlib.Path(sys.argv[1])
        after_results_path = pathlib.Path(sys.argv[2])
    else:
        eval_result_files = sorted(EVAL_RESULTS_DIRECTORY.glob("*.json"))
        if len(eval_result_files) < 2:
            print("need at least two eval runs in evals/results/ to compare")
            return 1
        before_results_path, after_results_path = eval_result_files[-2], eval_result_files[-1]

    results_before = json.loads(before_results_path.read_text())
    results_after = json.loads(after_results_path.read_text())
    no_regression, report_lines = compare_eval_runs(results_before, results_after)

    print(f"before: {before_results_path.name}\nafter:  {after_results_path.name}\n")
    print("\n".join(report_lines))
    print("\nNO REGRESSION: keep the change" if no_regression else "\nREGRESSION: revert the change")
    return 0 if no_regression else 1


if __name__ == "__main__":
    sys.exit(main())
