


# extended-diamond
few_shot_file=concept_based/outputs_simple/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.fewshot_demonstration.epoch0-100.jsonl
sampled_concept_file=concept_based/outputs_simple/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.jsonl
prompt_template_file=concept_based/prompts/concept2prompts_science_simple.md
output_prompt_file=concept_based/outputs_simple/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.prompts.jsonl

python concept_based/concept2prompts.py \
    --few_shot_file ${few_shot_file} --sampled_concept_file ${sampled_concept_file} \
    --prompt_template_file ${prompt_template_file} --output_prompt_file ${output_prompt_file} \
    --ncpus 32



# extended all, but only use extended-diamond seeds
few_shot_file=concept_based/outputs_simple/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.fewshot_demonstration.epoch0-100.jsonl
sampled_concept_file=concept_based/outputs_simple/gpqa_extended_all.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.jsonl
prompt_template_file=concept_based/prompts/concept2prompts_science_simple.md
output_prompt_file=concept_based/outputs_simple/gpqa_extended_all.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.prompts.jsonl

python concept_based/concept2prompts.py \
    --few_shot_file ${few_shot_file} --sampled_concept_file ${sampled_concept_file} \
    --prompt_template_file ${prompt_template_file} --output_prompt_file ${output_prompt_file} \
    --ncpus 32
