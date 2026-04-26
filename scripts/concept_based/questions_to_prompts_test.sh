#!/usr/bin/env bash

. pt

python3 concept_based/questions_to_prompts.py \
  --input_path=concept_based/outputs_simple/gpqa_extended_all.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.p0_p1.questions.jsonl \
  --output_path=concept_based/outputs_simple/gpqa_extended_all.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.p0_p1.prompts_from_questions.jsonl \
  --seed=0

python3 concept_based/questions_to_prompts.py \
  --input_path=concept_based/outputs_simple/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.p1_p2.questions.jsonl \
  --output_path=concept_based/outputs_simple/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.p1_p2.prompts_from_questions.jsonl \
  --seed=0
