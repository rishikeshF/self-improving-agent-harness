"""Behaviour evals: run every case in golden.jsonl through the agent and grade the answers.

  uv run python -m evals.run_evals          # real model (needs ANTHROPIC_API_KEY and: uv sync --extra llm)
  uv run python -m evals.run_evals --fake   # fake model: checks the eval pipeline works, not answer quality

Graders run cheapest first: contains / not_contains / regex checks, then the LLM judge.
Results go to evals/results/<timestamp>.json, and a pass rate per tag is printed.
"""
import json
import pathlib
import re
import sys
import time

from app.graph import run_agent
from app.llm import LLM, parse_json_object_from_model_reply
from app.tracing import Tracer

EVALS_DIRECTORY = pathlib.Path(__file__).resolve().parent
MINIMUM_JUDGE_SCORE_TO_PASS = 4


def ask_llm_judge(judge_llm: LLM, eval_case: dict, agent_answer: str, agent_error: str | None) -> tuple[int, str]:
    """Ask the judge model to score the answer 1-5 against the case's judge criterion."""
    judge_prompt = (EVALS_DIRECTORY / "rubric.md").read_text()
    rubric_values = {
        "input": eval_case["input"],
        "criterion": eval_case["expected"]["judge"],
        "answer": agent_answer,
        "error": agent_error,
    }
    for placeholder_name, placeholder_value in rubric_values.items():
        judge_prompt = judge_prompt.replace("{{" + placeholder_name + "}}", str(placeholder_value))

    judge_verdict = parse_json_object_from_model_reply(judge_llm.complete(judge_prompt))
    if judge_verdict is None:
        return 0, "judge output could not be parsed"
    return int(judge_verdict.get("score", 0)), str(judge_verdict.get("reason"))


def grade_eval_case(eval_case: dict, final_state: dict, judge_llm: LLM) -> tuple[bool, list[str]]:
    """Return (passed, notes). A case passes only if every check it defines passes."""
    expected = eval_case["expected"]
    agent_answer = final_state.get("final") or ""
    grading_notes: list[str] = []
    passed = True

    if "contains" in expected and expected["contains"].lower() not in agent_answer.lower():
        passed = False
        grading_notes.append(f"missing {expected['contains']!r}")

    if "not_contains" in expected and expected["not_contains"].lower() in agent_answer.lower():
        passed = False
        grading_notes.append(f"contains forbidden {expected['not_contains']!r}")

    if "regex" in expected and not re.search(expected["regex"], agent_answer):
        passed = False
        grading_notes.append(f"regex {expected['regex']!r} not matched")

    if "judge" in expected:
        judge_score, judge_reason = ask_llm_judge(judge_llm, eval_case, agent_answer, final_state.get("error"))
        grading_notes.append(f"judge {judge_score}/5: {judge_reason}")
        if judge_score < MINIMUM_JUDGE_SCORE_TO_PASS:
            passed = False

    return passed, grading_notes


def create_agent_and_judge_models(use_fake_models: bool) -> tuple[LLM, LLM]:
    if use_fake_models:
        from tests.fakes import FakeLLM, make_replies_per_node

        fake_agent_llm = FakeLLM(make_replies_per_node(
            planner_reply="look up the capital",
            act_replies_in_order=['{"tool": "example_lookup", "args": {"key": "capital_of_france"}}', '{"done": true}'],
            finish_reply="Paris",
        ))
        fake_judge_llm = FakeLLM(['{"score": 5, "reason": "fake judge always passes"}'])
        return fake_agent_llm, fake_judge_llm

    from app.llm import AnthropicLLM

    return AnthropicLLM(), AnthropicLLM()


def print_pass_rate_per_tag(eval_results: list[dict], results_file_path: pathlib.Path) -> None:
    passed_and_total_count_by_tag: dict[str, list[int]] = {}
    for eval_result in eval_results:
        for tag in eval_result["tags"]:
            counts_for_tag = passed_and_total_count_by_tag.setdefault(tag, [0, 0])
            if eval_result["pass"]:
                counts_for_tag[0] += 1
            counts_for_tag[1] += 1

    print(f"\n{'tag':<16}pass rate")
    for tag in sorted(passed_and_total_count_by_tag):
        passed_count, total_count = passed_and_total_count_by_tag[tag]
        print(f"{tag:<16}{passed_count}/{total_count}")

    total_passed = sum(1 for eval_result in eval_results if eval_result["pass"])
    relative_results_path = results_file_path.relative_to(EVALS_DIRECTORY.parent)
    print(f"{'ALL':<16}{total_passed}/{len(eval_results)}   -> {relative_results_path}")


def main() -> int:
    use_fake_models = "--fake" in sys.argv
    agent_llm, judge_llm = create_agent_and_judge_models(use_fake_models)

    golden_file_lines = (EVALS_DIRECTORY / "golden.jsonl").read_text().splitlines()
    eval_cases = [json.loads(golden_line) for golden_line in golden_file_lines if golden_line.strip()]

    eval_results = []
    for eval_case in eval_cases:
        tracer = Tracer(run_id=f"eval-{eval_case['id']}")
        try:
            final_state = run_agent(agent_llm, eval_case["input"], tracer=tracer)
            passed, grading_notes = grade_eval_case(eval_case, final_state, judge_llm)
        except Exception as agent_crash:  # a crash is a failed case, not a reason to stop the whole eval run
            final_state = {}
            passed = False
            grading_notes = [f"crashed: {agent_crash!r}"]

        eval_results.append({
            "id": eval_case["id"],
            "tags": eval_case["tags"],
            "pass": passed,
            "notes": grading_notes,
            "final": final_state.get("final"),
            "trace": str(tracer.trace_file_path),
        })
        verdict_label = "PASS" if passed else "FAIL"
        print(f"{verdict_label}  {eval_case['id']:<14} {'; '.join(grading_notes)}")

    results_directory = EVALS_DIRECTORY / "results"
    results_directory.mkdir(exist_ok=True)
    results_file_path = results_directory / f"{time.strftime('%Y%m%d-%H%M%S')}.json"
    results_file_path.write_text(json.dumps(eval_results, indent=2, default=str))

    print_pass_rate_per_tag(eval_results, results_file_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
