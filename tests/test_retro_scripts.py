"""Tests for the hill-climbing helpers: the evidence collector and the eval regression check."""
import importlib.util
import json
import pathlib
import subprocess

SCRIPTS_DIRECTORY = pathlib.Path(__file__).resolve().parent.parent / "scripts"


def import_script(script_name: str):
    """Scripts are not a package, so load them by file path."""
    script_spec = importlib.util.spec_from_file_location(script_name, SCRIPTS_DIRECTORY / f"{script_name}.py")
    script_module = importlib.util.module_from_spec(script_spec)
    script_spec.loader.exec_module(script_module)
    return script_module


compare_eval_runs_script = import_script("compare_eval_runs")
collect_retro_evidence_script = import_script("collect_retro_evidence")


def make_eval_result(case_id: str, tags: list[str], passed: bool) -> dict:
    return {"id": case_id, "tags": tags, "pass": passed, "notes": [], "trace": f"traces/{case_id}.jsonl"}


def test_no_regression_when_results_improve():
    results_before = [make_eval_result("case-a", ["happy"], True), make_eval_result("case-b", ["edge"], False)]
    results_after = [make_eval_result("case-a", ["happy"], True), make_eval_result("case-b", ["edge"], True)]

    no_regression, report_lines = compare_eval_runs_script.compare_eval_runs(results_before, results_after)

    assert no_regression is True
    assert any("edge" in report_line and "improved" in report_line for report_line in report_lines)


def test_regression_when_a_tag_pass_rate_drops():
    results_before = [make_eval_result("case-a", ["happy"], True)]
    results_after = [make_eval_result("case-a", ["happy"], False)]

    no_regression, report_lines = compare_eval_runs_script.compare_eval_runs(results_before, results_after)

    assert no_regression is False
    assert any("REGRESSED" in report_line for report_line in report_lines)


def test_regression_when_a_case_flips_even_if_tag_rate_is_flat():
    # case-a breaks while case-b gets fixed: the 'edge' rate stays 50%, but it is still a regression.
    results_before = [make_eval_result("case-a", ["edge"], True), make_eval_result("case-b", ["edge"], False)]
    results_after = [make_eval_result("case-a", ["edge"], False), make_eval_result("case-b", ["edge"], True)]

    no_regression, report_lines = compare_eval_runs_script.compare_eval_runs(results_before, results_after)

    assert no_regression is False
    assert "newly failing cases: case-a" in report_lines


def test_evidence_digest_collects_qa_fails_eval_fails_and_log(tmp_path):
    project_root = tmp_path
    subprocess.run(["git", "init", "-q"], cwd=project_root, check=True)

    qa_reports_directory = project_root / "_docs" / "qa"
    qa_reports_directory.mkdir(parents=True)
    (qa_reports_directory / "02.md").write_text(
        "## QA: FAIL  (round 1, 10:00)\n- [ ] tool raises on empty key\n\n## QA: PASS  (round 2, 10:20)\n- [x] all good\n"
    )
    (project_root / "_docs" / "agent-log.md").write_text(
        "# Agent log\nFormat: `HH:MM | who | what | change`\n10:05 | me | engineer edited state.py | reverted\n"
    )
    eval_results_directory = project_root / "evals" / "results"
    eval_results_directory.mkdir(parents=True)
    (eval_results_directory / "20261111-1000.json").write_text(json.dumps([
        make_eval_result("happy-1", ["happy"], True),
        make_eval_result("adv-1", ["adversarial"], False),
    ]))

    evidence_digest = collect_retro_evidence_script.build_evidence_digest(project_root)

    assert "## QA failures (1)" in evidence_digest
    assert "tool raises on empty key" in evidence_digest
    assert "all good" not in evidence_digest  # PASS sections are left out
    assert "engineer edited state.py" in evidence_digest
    assert "- adv-1 ['adversarial']" in evidence_digest
    assert "happy-1" not in evidence_digest
