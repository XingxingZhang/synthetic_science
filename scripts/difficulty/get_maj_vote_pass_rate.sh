#!/usr/bin/env bash

set -euo pipefail

. pt

python difficulty/get_maj_vote_pass_rate.py \
  /data/xingxing/gpqa_dataset/Nemotron-Science-v1_problems.fixed.completions \
  /data/xingxing/gpqa_dataset/Nemotron-Science-v1_problems.fixed.completions.n9.maj_vote_pass_rate.jsonl
