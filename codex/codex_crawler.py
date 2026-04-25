from concurrent.futures import ProcessPoolExecutor
import json
import subprocess
from pathlib import Path
import tempfile

import fire


MODEL = "gpt-5.4"
WORKDIR = "/home/xizhang/projects/synthetic_science_test" # Path(__file__).resolve().parents[1]
PROMPT_TEMPLATE = """
I have two tasks for you. Here is a long instruction
```
{instruction}
```

Your tasks: 
1) find out which python file generate this instruction and output between two "```" (one file each line).
2) execute the long instruction.
"""


def _num_completed_rows(input_path, output_path):
    if not output_path.exists():
        return 0

    completed = 0
    with input_path.open(encoding="utf8") as fin_in, output_path.open(encoding="utf8") as fin_out:
        for output_line in fin_out:
            if not output_line.strip():
                continue

            input_line = next(fin_in)
            input_row = json.loads(input_line)
            output_row = json.loads(output_line)
            for key, value in input_row.items():
                if key == "completion":
                    continue
                assert output_row[key] == value
            completed += 1

    return completed


def _run_codex(prompt):
    with tempfile.NamedTemporaryFile(mode="r+", encoding="utf8") as fout:
        cmd = [
            "codex", "--ask-for-approval", "never", "exec", "--cd", str(WORKDIR),
            "--model", MODEL, "--sandbox", "read-only", "--ephemeral",
            "--output-last-message", fout.name, "-",
        ]
        wrapped_prompt = PROMPT_TEMPLATE.format(instruction=prompt)
        subprocess.run(cmd, input=wrapped_prompt, text=True, check=True)
        fout.seek(0)
        return fout.read()


def _complete_row(task):
    row_index, row = task
    try:
        row["completion"] = _run_codex(row["prompt"])
        status = "done"
    except Exception as exc:
        row["completion"] = None
        row["completion_error"] = repr(exc)
        status = "failed"
    return row_index, row, status


def _iter_remaining_rows(input_path, completed):
    with input_path.open(encoding="utf8") as fin:
        for row_index, line in enumerate(fin):
            if not line.strip():
                continue
            if row_index < completed:
                continue
            yield row_index, json.loads(line)


def main(input_file, output_file, ncpus=8):
    input_path = Path(input_file)
    output_path = Path(output_file)
    completed = _num_completed_rows(input_path, output_path)
    print(locals())
    print(f"completed {completed} examples")

    with output_path.open("a", encoding="utf8") as fout:
        with ProcessPoolExecutor(max_workers=ncpus) as executor:
            for row_index, row, status in executor.map(
                _complete_row,
                _iter_remaining_rows(input_path, completed),
                chunksize=1,
            ):
                assert row_index == completed
                completed += 1
                fout.write(json.dumps(row, ensure_ascii=False) + "\n")
                fout.flush()
                print({"row_index": row_index, "status": status})


if __name__ == "__main__":
    fire.Fire(main)
