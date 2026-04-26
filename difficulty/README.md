# Difficulty Estimation And Filtering

This directory contains the post-processing code for the difficulty-estimation workflow on the Nemotron Science problem set.

## Overview

The pipeline has three stages:

1. Generate multiple independent model completions for each problem.
2. Aggregate those completions into a majority-vote pass rate for multiple-choice questions.
3. Filter the multiple-choice questions by estimated difficulty and attach the original `messages` field from the source shards.

Difficulty is defined as:

```text
difficulty = 1 - maj_vote_pass_rate
```

So:

- `maj_vote_pass_rate = 1.0` means easiest under this definition
- lower `maj_vote_pass_rate` means more difficult

## Files

- [get_maj_vote_pass_rate.py](/home/xizhang/projects/synthetic_science/difficulty/get_maj_vote_pass_rate.py): computes majority-vote answer statistics from multiple completion files
- [filter_multi_choice_by_difficulty.py](/home/xizhang/projects/synthetic_science/difficulty/filter_multi_choice_by_difficulty.py): selects hardest/easiest/random subsets and attaches source `messages`
- [../scripts/difficulty/answer_generation.4.1.sh](/home/xizhang/projects/synthetic_science/scripts/difficulty/answer_generation.4.1.sh): generation wrapper, original version
- [../scripts/difficulty/answer_generation.4.1.rev.sh](/home/xizhang/projects/synthetic_science/scripts/difficulty/answer_generation.4.1.rev.sh): generation wrapper, revised version
- [../scripts/difficulty/get_maj_vote_pass_rate.sh](/home/xizhang/projects/synthetic_science/scripts/difficulty/get_maj_vote_pass_rate.sh): wrapper for majority-vote scoring
- [../scripts/difficulty/filter_multi_choice_by_difficulty.sh](/home/xizhang/projects/synthetic_science/scripts/difficulty/filter_multi_choice_by_difficulty.sh): wrapper for filtering

## Step 1: Generate Completions

The generation wrappers produce multiple JSONL completion files under:

```text
/data/xingxing/gpqa_dataset/Nemotron-Science-v1_problems.fixed.completions
```

Run:

```bash
bash scripts/difficulty/answer_generation.4.1.sh
```

or:

```bash
bash scripts/difficulty/answer_generation.4.1.rev.sh
```

These scripts call `azure/gpt_crawler_mp.py` from the crawler repo and write one completion JSONL per run id.

## Step 2: Compute Majority-Vote Pass Rate

Run:

```bash
bash scripts/difficulty/get_maj_vote_pass_rate.sh
```

This reads:

```text
/data/xingxing/gpqa_dataset/Nemotron-Science-v1_problems.fixed.completions
```

and writes:

```text
/data/xingxing/gpqa_dataset/Nemotron-Science-v1_problems.fixed.completions.n9.maj_vote_pass_rate.jsonl
```

For each row it adds fields such as:

- `is_multi_choice`
- `answer_freqs`
- `maj_voted_answer`
- `maj_vote_pass_rate`
- `num_extracted_votes`
- `num_failed_answer_extractions`
- `num_completion_files`

For non-multiple-choice rows, the vote-related fields are left empty or `null`.

## Step 3: Filter By Difficulty

Run:

```bash
bash scripts/difficulty/filter_multi_choice_by_difficulty.sh
```

This script activates `. pt` and runs:

```bash
python difficulty/filter_multi_choice_by_difficulty.py \
  --input_path /data/xingxing/gpqa_dataset/Nemotron-Science-v1_problems.fixed.completions.n9.maj_vote_pass_rate.jsonl \
  --source_pattern '/data/xingxing/gpqa_dataset/shaohan/Nemotron-Science-v1_k25_stem*/*.jsonl' \
  --output_dir /data/xingxing/gpqa_dataset/difficulty_filtered \
  --sample_size 10000 \
  --random_seed 0
```

### What It Does

1. Keeps only rows with `is_multi_choice == true`
2. Skips rows where `maj_vote_pass_rate == null`
3. Computes `difficulty = 1 - maj_vote_pass_rate`
4. Selects:
   - hardest 10K
   - easiest 10K
   - random 10K
5. Preserves all existing fields in each selected row
6. Adds:
   - `difficulty`
   - `messages`

### Output Files

The filtered outputs are written to:

- `/data/xingxing/gpqa_dataset/difficulty_filtered/hardest.10000.jsonl`
- `/data/xingxing/gpqa_dataset/difficulty_filtered/easiest.10000.jsonl`
- `/data/xingxing/gpqa_dataset/difficulty_filtered/random.10000.jsonl`

## Matching Logic For `messages`

The source `messages` field is looked up from:

```text
/data/xingxing/gpqa_dataset/shaohan/Nemotron-Science-v1_k25_stem*/*.jsonl
```

Matching is done by exact string equality:

```text
filtered_row["problem"] == source_row["messages"][0]["content"]
```

The full `messages` array from the matched source row is then attached to the filtered output record.

This is intentionally strict. If an exact match cannot be found, the script raises an error instead of silently writing incomplete rows.

## Selection Details

The script uses deterministic ordering:

- hardest: sort by `(-difficulty, original_row_index)`
- easiest: sort by `(difficulty, original_row_index)`
- random: sampled with `random_seed`

This makes the output reproducible as long as the input file does not change.

## Current Run Notes

On the current dataset version, the filtering script reported:

- `139793` scored multiple-choice rows
- `40` multiple-choice rows skipped because `maj_vote_pass_rate` was `null`

## Environment

Use the project virtualenv before running Python directly:

```bash
. pt
```

The shell wrappers in `scripts/difficulty/` already do this where needed.
