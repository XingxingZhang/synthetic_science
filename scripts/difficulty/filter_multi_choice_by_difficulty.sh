#!/usr/bin/env bash

set -euo pipefail

. pt

python difficulty/filter_multi_choice_by_difficulty.py \
  --input_path /data/xingxing/gpqa_dataset/Nemotron-Science-v1_problems.fixed.completions.n9.maj_vote_pass_rate.jsonl \
  --source_pattern '/data/xingxing/gpqa_dataset/shaohan/Nemotron-Science-v1_k25_stem*/*.jsonl' \
  --output_dir /data/xingxing/gpqa_dataset/difficulty_filtered \
  --sample_size 10000 \
  --random_seed 0
