#!/usr/bin/env bash
set -euo pipefail

curdir=$(pwd)
outdir=${curdir}/concept_based/outputs_simple

diamond_p1=${outdir}/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.p1.completions.gpt-5.4_high.jsonl
diamond_p2=${outdir}/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.p2.completions.gpt-5.4_high.jsonl
diamond_out=${outdir}/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.p1_p2.questions.jsonl
diamond_out_redo=${outdir}/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.p1_p2.redo.prompts.jsonl

all_p0=${outdir}/gpqa_extended_all.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.completions.gpt-5.4_high.jsonl
all_p1=${outdir}/gpqa_extended_all.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.p1.completions.gpt-5.4_high.jsonl
all_out=${outdir}/gpqa_extended_all.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.p0_p1.questions.jsonl
all_out_redo=${outdir}/gpqa_extended_all.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.p0_p1.redo.prompts.jsonl

. pt

python -u concept_based/parse_questions.py --input_paths "${diamond_p1},${diamond_p2}" --output_path "${diamond_out}" --output_path_redo ${diamond_out_redo}

python -u concept_based/parse_questions.py --input_paths "${all_p0},${all_p1}" --output_path "${all_out}" --output_path_redo ${all_out_redo}
