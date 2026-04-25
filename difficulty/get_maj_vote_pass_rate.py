import glob
import json
import re
from collections import Counter
from contextlib import ExitStack
from itertools import zip_longest
from pathlib import Path

import fire


MC_PROMPT_PREFIXES = (
    "Answer the following multiple choice question. The last line",
    "Help me with this mutliple-choice question.",
    "Solve the following multiple-choice problem.",
    "Read carefully and return one letter.",
    "Analyze the following multiple-choice problem. Explain your reasoning thoroughly, then conclude with the selected option using the exact format:",
)

OPTION_LETTERS = "ABCDEFGHIJ"


STRICT_ANSWER_PATTERNS = (
    re.compile(
        rf"(?im)^\s*\**\s*(?:final\s+answer|answer)\s*:\s*(?:\\boxed\{{\s*)?[\(\[]?\s*([{OPTION_LETTERS}])\s*[\)\]]?(?:\s*\}})?\s*\.?\s*\**\s*$"
    ),
    re.compile(
        rf"(?i)\bthe\s+final\s+answer\s+is\s*(?:\\boxed\{{\s*)?[\(\[]?\s*([{OPTION_LETTERS}])\s*[\)\]]?(?:\s*\}})?\s*\**"
    ),
    re.compile(rf"(?i)\\boxed\{{\s*([{OPTION_LETTERS}])\s*\}}"),
    re.compile(rf"(?i)\bboxed\{{\s*([{OPTION_LETTERS}])\s*\}}"),
)

LOOSE_ANSWER_PATTERNS = (
    re.compile(rf"(?im)^\s*[\(\[]?\s*([{OPTION_LETTERS}])\s*[\)\]]?\s*\.?\s*$"),
    re.compile(rf"(?i)\b(?:option|choice|letter)\s*[\(\[]?\s*([{OPTION_LETTERS}])\s*[\)\]]?"),
    re.compile(rf"(?i)\b(?:answer|final\s+answer)\s+is\s*[\(\[]?\s*([{OPTION_LETTERS}])\s*[\)\]]?"),
)


def is_multi_choice_prompt(prompt):
    prompt = prompt.lstrip()
    return any(prompt.startswith(prefix) for prefix in MC_PROMPT_PREFIXES)


def _last_regex_match(pattern, text):
    matches = list(pattern.finditer(text))
    if not matches:
        return None
    return matches[-1].group(1).upper()


def extract_multi_choice_answer(completion):
    text = str(completion).strip()
    if not text:
        return None

    for pattern in STRICT_ANSWER_PATTERNS:
        answer = _last_regex_match(pattern, text)
        if answer is not None:
            return answer

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    tail_text = "\n".join(lines[-5:])
    for pattern in LOOSE_ANSWER_PATTERNS:
        answer = _last_regex_match(pattern, tail_text)
        if answer is not None:
            return answer

    return None


def _completion_values(completion):
    if isinstance(completion, list):
        return completion
    return [completion]


def _expand_input_paths(input_paths):
    if isinstance(input_paths, (list, tuple)):
        raw_paths = input_paths
    else:
        raw_paths = str(input_paths).split(",")

    paths = []
    for raw_path in raw_paths:
        raw_path = raw_path.strip()
        if not raw_path:
            continue
        path = Path(raw_path)
        if path.is_dir():
            matches = sorted(str(path_match) for path_match in path.glob("*.jsonl"))
        else:
            matches = sorted(glob.glob(raw_path))
        paths.extend(matches or [raw_path])

    if not paths:
        raise ValueError("No input paths provided.")
    return [Path(path) for path in paths]


def _iter_jsonl(path):
    with path.open() as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


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
                lengths = []
                for path in input_paths:
                    with path.open() as f:
                        lengths.append(sum(1 for line in f if line.strip()))
                raise ValueError(
                    f"Input row-count mismatch at 1-based line {row_idx}: "
                    f"{dict(zip([str(path) for path in input_paths], lengths))}"
                )

            prompt = grouped_rows[0]["prompt"]
            for path, row in zip(input_paths[1:], grouped_rows[1:]):
                if row["prompt"] != prompt:
                    raise ValueError(f"Prompt mismatch at 1-based line {row_idx} in {path}.")
            yield row_idx, grouped_rows


def _vote_stats(completions):
    answers = []
    failed = 0
    for completion in completions:
        answer = extract_multi_choice_answer(completion)
        if answer is None:
            failed += 1
        else:
            answers.append(answer)

    freqs = Counter(answers)
    if not freqs:
        return {}, None, None, 0, failed

    max_count = max(freqs.values())
    maj_answers = sorted(answer for answer, count in freqs.items() if count == max_count)
    maj_answer = maj_answers[0]
    pass_rate = max_count / sum(freqs.values())
    sorted_freqs = {answer: freqs[answer] for answer in sorted(freqs)}
    return sorted_freqs, maj_answer, pass_rate, sum(freqs.values()), failed


def compute_maj_vote_pass_rate(
    input_paths,
    output_path,
    keep_non_mc=True,
    max_failure_examples=20,
):
    input_paths = _expand_input_paths(input_paths)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    mc_rows = 0
    extracted_vote_count = 0
    failed_vote_count = 0
    failure_examples = []

    with output_path.open("w") as out:
        for row_idx, grouped_rows in _iter_aligned_rows(input_paths):
            total_rows += 1
            base_row = dict(grouped_rows[0])
            prompt = base_row["prompt"]
            base_row["prompt"] = prompt
            is_mc = is_multi_choice_prompt(prompt)

            if not is_mc:
                if keep_non_mc:
                    base_row["is_multi_choice"] = False
                    base_row["answer_freqs"] = {}
                    base_row["maj_voted_answer"] = None
                    base_row["maj_vote_pass_rate"] = None
                    base_row["num_extracted_votes"] = 0
                    base_row["num_failed_answer_extractions"] = 0
                    base_row["num_completion_files"] = len(input_paths)
                    out.write(json.dumps(base_row, ensure_ascii=False) + "\n")
                continue

            mc_rows += 1
            completions = []
            for row in grouped_rows:
                completions.extend(_completion_values(row["completion"]))

            freqs, maj_answer, pass_rate, num_votes, num_failed = _vote_stats(completions)
            extracted_vote_count += num_votes
            failed_vote_count += num_failed

            if num_failed and len(failure_examples) < max_failure_examples:
                for completion in completions:
                    if extract_multi_choice_answer(completion) is None:
                        failure_examples.append(
                            {
                                "line": row_idx,
                                "completion_preview": str(completion)[:500],
                            }
                        )
                        break

            base_row["is_multi_choice"] = True
            base_row["answer_freqs"] = freqs
            base_row["maj_voted_answer"] = maj_answer
            base_row["maj_vote_pass_rate"] = pass_rate
            base_row["num_extracted_votes"] = num_votes
            base_row["num_failed_answer_extractions"] = num_failed
            base_row["num_completion_files"] = len(input_paths)
            out.write(json.dumps(base_row, ensure_ascii=False) + "\n")

    summary = {
        "input_paths": [str(path) for path in input_paths],
        "num_input_files": len(input_paths),
        "output_path": str(output_path),
        "total_rows": total_rows,
        "multi_choice_rows": mc_rows,
        "extracted_vote_count": extracted_vote_count,
        "failed_answer_extraction_count": failed_vote_count,
        "failure_examples": failure_examples,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    fire.Fire(compute_maj_vote_pass_rate)
