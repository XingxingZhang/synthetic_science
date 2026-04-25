import glob
import json
import re
from contextlib import ExitStack
from itertools import zip_longest
from pathlib import Path

import fire


QUESTION_PATTERN = re.compile(r"<question>\s*(.*?)\s*</question>", re.DOTALL)


def _read_jsonl_rows(path):
    with path.open() as f:
        return sum(1 for line in f if line.strip())


def _iter_aligned_rows(input_paths):
    sentinel = object()
    with ExitStack() as stack:
        files = [stack.enter_context(path.open()) for path in input_paths]
        iterators = (
            (json.loads(line) for line in f if line.strip())
            for f in files
        )
        for row_idx, grouped_rows in enumerate(zip_longest(*iterators, fillvalue=sentinel), 1):
            if any(row is sentinel for row in grouped_rows):
                lengths = {str(path): _read_jsonl_rows(path) for path in input_paths}
                raise ValueError(
                    f"Input row-count mismatch at 1-based line {row_idx}: {lengths}"
                )

            base_uuid = grouped_rows[0]["uuid"]
            for path, row in zip(input_paths[1:], grouped_rows[1:]):
                if row["uuid"] != base_uuid:
                    raise ValueError(f"UUID mismatch at 1-based line {row_idx} in {path}.")

            yield row_idx, grouped_rows


def _extract_questions(completion):
    completions = completion if isinstance(completion, list) else [completion]
    questions = []
    for item in completions:
        questions.extend(
            match.group(1).strip()
            for match in QUESTION_PATTERN.finditer(str(item))
        )
    return questions

def extract_question(completion):
    questions = []
    for m in QUESTION_PATTERN.finditer(completion):
        q = m.group(1).strip()
        if len(q) > 0:
            questions.append(q)
    
    assert len(questions) <= 1

    return questions

def parse_questions(input_paths="", output_path="", output_path_redo=""):
    print(locals())
    input_paths = input_paths.strip().split(",")
    input_paths = [Path(path) for path in input_paths]

    output_path = Path(output_path)
    if len(output_path_redo.strip()) > 0:
        fout_redo = Path(output_path_redo).open("w")

    total_rows = 0
    rows_with_questions = 0
    total_questions = 0
    missing_completion_count = 0

    with output_path.open("w") as out:
        for _, grouped_rows in _iter_aligned_rows(input_paths):
            total_rows += 1
            questions = []
            for row in grouped_rows:
                if "completion" not in row:
                    missing_completion_count += 1
                    continue

                questions.extend(_extract_questions(row["completion"]))

            if questions:
                rows_with_questions += 1
            else:
                if len(output_path_redo.strip()) > 0:
                    row = grouped_rows[0]
                    
                    if "completion" in row:
                        del row["completion"]
                    fout_redo.write(json.dumps(row) + "\n")

            total_questions += len(questions)

            output_row = {
                "uuid": grouped_rows[0]["uuid"],
                "questions": questions,
            }
            out.write(json.dumps(output_row, ensure_ascii=False) + "\n")

    summary = {
        "input_paths": [str(path) for path in input_paths],
        "num_input_files": len(input_paths),
        "output_path": str(output_path),
        "total_rows": total_rows,
        "rows_with_questions": rows_with_questions,
        "total_questions": total_questions,
        "missing_completion_count": missing_completion_count,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    fire.Fire(parse_questions)
