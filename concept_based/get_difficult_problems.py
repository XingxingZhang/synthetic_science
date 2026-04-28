import json
import re
from pathlib import Path

import fire


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT_PATH = (
    BASE_DIR
    / "outputs_simple"
    / "gpqa_extended_all.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.p0_p1.prompts_from_questions.10k.jsonl"
)
DEFAULT_TEMPLATE_PATH = BASE_DIR / "prompts" / "more_difficult.md"
DEFAULT_OUTPUT_PATH = (
    BASE_DIR
    / "outputs_simple"
    / "gpqa_extended_all.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.p0_p1.prompts_from_questions.10k.more_diff.jsonl"
)
CHOICE_RE = re.compile(r"(?m)^\s*([A-Z])[).]\s+")


def _is_valid_question(question):
    return question.strip() and CHOICE_RE.findall(question) == ["A", "B", "C", "D"]


def _find_question_in_prompt(row, row_index):
    questions = row["questions"]
    old_prompt = row["prompt"]

    matches = [question for question in questions if _is_valid_question(question) and question in old_prompt]
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one question match at row {row_index} "
            f"(uuid={row['uuid']}), found {len(matches)}."
        )

    return matches[0]


def _replace_prompt(row, prompt):
    output_row = {}
    for key, value in row.items():
        if key == "prompt":
            output_row["old_prompt"] = value
            output_row["prompt"] = prompt
        else:
            output_row[key] = value

    return output_row


def get_prompt(
    input_path=DEFAULT_INPUT_PATH,
    prompt_template_file=DEFAULT_TEMPLATE_PATH,
    output_path=DEFAULT_OUTPUT_PATH,
):
    input_path = Path(input_path)
    prompt_template_file = Path(prompt_template_file)
    output_path = Path(output_path)

    prompt_template = prompt_template_file.read_text(encoding="utf8")
    total_rows = 0

    with input_path.open(encoding="utf8") as fin, output_path.open("w", encoding="utf8") as fout:
        for row_index, line in enumerate(fin, start=1):
            if not line.strip():
                continue

            row = json.loads(line)
            question = _find_question_in_prompt(row, row_index)
            prompt = prompt_template.replace("{{ question }}", question)
            fout.write(json.dumps(_replace_prompt(row, prompt), ensure_ascii=False) + "\n")
            total_rows += 1

    print(
        json.dumps(
            {
                "input_path": str(input_path),
                "prompt_template_file": str(prompt_template_file),
                "output_path": str(output_path),
                "written_rows": total_rows,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    fire.Fire()
