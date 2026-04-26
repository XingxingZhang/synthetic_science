. pt

input_file=concept_based/outputs_simple/gpqa_extended_all.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.p0_p1.redo.prompts.jsonl
output_file=concept_based/outputs_simple/gpqa_extended_all.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.p0_p1.redo.completions.jsonl

# python codex/codex_crawler.py ${input_file} ${output_file} --ncpus 8

input_file=concept_based/outputs_simple/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.p1_p2.redo.prompts.jsonl
output_file=concept_based/outputs_simple/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.p1_p2.redo.completions.jsonl

python codex/codex_crawler.py ${input_file} ${output_file} --ncpus 8
