import json
import random
import re
from pathlib import Path

import fire


PROMPT_TEMPLATE = """Answer the following multiple choice question. The last line of your response should be of the following format: 'Answer: $LETTER' (without quotes) where LETTER is one of ABCD. Think step by step before answering.

{question}"""
CHOICE_RE = re.compile(r"(?m)^\s*([A-Z])[).]\s+")


def _is_valid_question(question):
    return isinstance(question, str) and CHOICE_RE.findall(question) == ["A", "B", "C", "D"]


def main(input_path, output_path, seed=0):
    rng = random.Random(seed)
    input_path = Path(input_path)
    output_path = Path(output_path)

    total = 0
    written = 0
    skipped = 0

    with input_path.open() as fin, output_path.open("w") as fout:
        for line in fin:
            if not line.strip():
                continue
            total += 1
            row = json.loads(line)
            valid_questions = [q for q in row["questions"] if _is_valid_question(q)]
            if not valid_questions:
                skipped += 1
                continue

            row["prompt"] = PROMPT_TEMPLATE.format(question=rng.choice(valid_questions))
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            written += 1

    print(
        json.dumps(
            {
                "input_path": str(input_path),
                "output_path": str(output_path),
                "seed": seed,
                "total_rows": total,
                "written_rows": written,
                "skipped_rows": skipped,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    fire.Fire(main)
