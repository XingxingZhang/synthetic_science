import glob
import json
import random
from pathlib import Path

import fire


def _iter_jsonl(path):
    with Path(path).open() as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def _source_paths(pattern):
    paths = [Path(path) for path in sorted(glob.glob(pattern))]
    if not paths:
        raise ValueError(f"No source files matched pattern: {pattern}")
    return paths


def _load_multi_choice_rows(input_path):
    rows = []
    skipped_missing_pass_rate = 0
    for row_idx, row in enumerate(_iter_jsonl(input_path)):
        if not row["is_multi_choice"]:
            continue
        if row["maj_vote_pass_rate"] is None:
            skipped_missing_pass_rate += 1
            continue
        difficulty = 1.0 - row["maj_vote_pass_rate"]
        enriched_row = dict(row)
        enriched_row["difficulty"] = difficulty
        enriched_row["_row_idx"] = row_idx
        rows.append(enriched_row)
    if not rows:
        raise ValueError(f"No multi-choice rows found in {input_path}")
    return rows, skipped_missing_pass_rate


def _select_rows(rows, sample_size, seed):
    if len(rows) < sample_size:
        raise ValueError(
            f"Requested {sample_size} rows, but only found {len(rows)} multi-choice rows."
        )

    hardest = sorted(
        rows,
        key=lambda row: (-row["difficulty"], row["_row_idx"]),
    )[:sample_size]
    easiest = sorted(
        rows,
        key=lambda row: (row["difficulty"], row["_row_idx"]),
    )[:sample_size]

    random_indices = random.Random(seed).sample(range(len(rows)), sample_size)
    random_indices.sort()
    random_rows = [rows[idx] for idx in random_indices]

    return {
        "hardest": hardest,
        "easiest": easiest,
        "random": random_rows,
    }


def _build_messages_lookup(problem_texts, source_pattern):
    pending = set(problem_texts)
    messages_by_problem = {}
    source_files_scanned = 0
    source_rows_scanned = 0

    for path in _source_paths(source_pattern):
        source_files_scanned += 1
        with path.open() as f:
            for line in f:
                if not pending:
                    return messages_by_problem, source_files_scanned, source_rows_scanned

                if not line.strip():
                    continue

                source_rows_scanned += 1
                row = json.loads(line)
                problem = row["messages"][0]["content"]
                if problem not in pending:
                    continue

                messages = row["messages"]
                if problem in messages_by_problem and messages_by_problem[problem] != messages:
                    raise ValueError(f"Conflicting messages found for problem: {problem[:200]!r}")

                messages_by_problem[problem] = messages
                pending.remove(problem)

    if pending:
        missing_preview = sorted(pending)[:3]
        raise ValueError(
            "Failed to find source messages for "
            f"{len(pending)} selected problems. Sample missing problems: {missing_preview}"
        )

    return messages_by_problem, source_files_scanned, source_rows_scanned


def _write_jsonl(rows, output_path, messages_by_problem):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as out:
        for row in rows:
            output_row = {k: v for k, v in row.items() if k != "_row_idx"}
            output_row["messages"] = messages_by_problem[row["problem"]]
            out.write(json.dumps(output_row, ensure_ascii=False) + "\n")


def filter_multi_choice_by_difficulty(
    input_path="/data/xingxing/gpqa_dataset/Nemotron-Science-v1_problems.fixed.completions.n9.maj_vote_pass_rate.jsonl",
    source_pattern="/data/xingxing/gpqa_dataset/shaohan/Nemotron-Science-v1_k25_stem*/*.jsonl",
    output_dir="/data/xingxing/gpqa_dataset/difficulty_filtered",
    sample_size=10000,
    random_seed=0,
):
    rows, skipped_missing_pass_rate = _load_multi_choice_rows(input_path)
    selections = _select_rows(rows, sample_size=sample_size, seed=random_seed)

    all_selected_problems = {
        row["problem"]
        for selected_rows in selections.values()
        for row in selected_rows
    }
    messages_by_problem, source_files_scanned, source_rows_scanned = _build_messages_lookup(
        all_selected_problems,
        source_pattern=source_pattern,
    )

    output_dir = Path(output_dir)
    output_paths = {}
    for name, selected_rows in selections.items():
        output_path = output_dir / f"{name}.{sample_size}.jsonl"
        _write_jsonl(selected_rows, output_path, messages_by_problem)
        output_paths[name] = str(output_path)

    summary = {
        "input_path": str(input_path),
        "source_pattern": source_pattern,
        "output_dir": str(output_dir),
        "sample_size": sample_size,
        "random_seed": random_seed,
        "multi_choice_row_count": len(rows),
        "skipped_multi_choice_rows_missing_pass_rate": skipped_missing_pass_rate,
        "unique_selected_problem_count": len(all_selected_problems),
        "source_files_scanned": source_files_scanned,
        "source_rows_scanned": source_rows_scanned,
        "outputs": output_paths,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    fire.Fire(filter_multi_choice_by_difficulty)
