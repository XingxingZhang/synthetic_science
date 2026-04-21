

concept_comp_file=concept_based/outputs_simple/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.jsonl
few_shot_file=concept_based/outputs_simple/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.fewshot_demonstration.jsonl.jsonl
sampled_concept_file=concept_based/outputs_simple/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.concept_graph.jsonl

python concept_based/graph_construction_gpqa_seed.py \
    --concept_comp_file ${concept_comp_file} --few_shot_file ${few_shot_file} \
    --sampled_concept_file ${sampled_concept_file} \
    --num_epochs 10 --topic_freq_cut=0 --knowledge_point_freq_cut=0 \
    --ncpu=32




