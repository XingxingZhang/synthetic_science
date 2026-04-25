import json
import subprocess
from pathlib import Path
import fire

PROMPT_FILE = (
    "concept_based/outputs_simple/"
    "gpqa_extended_all.concept_completions.gpt-5.4_medium.v2."
    "concept_graph.epoch0-100.20k.p0_p1.redo.prompts.jsonl"
)

PROMPT_TEMPLATE = """
I have two tasks for you. Here is a long instruction
```
{instruction}
```

Your tasks: 
1) find out which python file generate this instruction and output between two "```" (one file each line).
2) execute the long instruction.
"""

def main(row_index=0, model="gpt-5.4", workdir="/home/xizhang/projects/synthetic_science_test", output_file="codex/example.output.txt"):
    with open(PROMPT_FILE, encoding="utf8") as fin:
        for i, line in enumerate(fin):
            if i == row_index:
                prompt = json.loads(line)["prompt"]
                break

    cmd = [
        "codex", "--ask-for-approval", "never", "exec", "--cd", workdir,
        "--model", model, "--sandbox", "read-only", "--ephemeral",
        "--output-last-message", output_file, "-",
    ]
    # wrapped_prompt = PROMPT_TEMPLATE.format(instruction=prompt)
    wrapped_prompt = prompt
    subprocess.run(cmd, input=wrapped_prompt, text=True, check=True)

if __name__ == "__main__":
    fire.Fire(main)
