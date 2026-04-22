

concept_comp_file=concept_based/outputs_simple/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.jsonl
few_shot_file=concept_based/outputs_simple/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.fewshot_demonstration.jsonl.jsonl
sampled_concept_file=concept_based/outputs_simple/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.concept_graph.jsonl

# python concept_based/graph_construction_gpqa_seed.py \
#     --concept_comp_file ${concept_comp_file} --few_shot_file ${few_shot_file} \
#     --sampled_concept_file ${sampled_concept_file} \
#     --num_epochs 10 --topic_freq_cut=0 --knowledge_point_freq_cut=0 \
#     --ncpu=32



concept_comp_file=concept_based/outputs_simple/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.jsonl
epoch_start=0
epoch_end=100

few_shot_file=concept_based/outputs_simple/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.fewshot_demonstration.epoch${epoch_start}-${epoch_end}.jsonl
sampled_concept_file=concept_based/outputs_simple/gpqa_extended-diamond.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch${epoch_start}-${epoch_end}.jsonl

# python concept_based/graph_construction_gpqa_seed_dist.py \
#     --concept_comp_file ${concept_comp_file} --few_shot_file ${few_shot_file} \
#     --sampled_concept_file ${sampled_concept_file} \
#     --start_epoch 0 --end_epoch 100 --topic_freq_cut=0 --knowledge_point_freq_cut=0 --ncpus=32





concept_comp_file=concept_based/outputs_simple/gpqa_extended_all.concept_completions.gpt-5.4_medium.v2.jsonl
epoch_start=0
epoch_end=100

few_shot_file=concept_based/outputs_simple/gpqa_extended_all.concept_completions.gpt-5.4_medium.v2.fewshot_demonstration.epoch${epoch_start}-${epoch_end}.jsonl
sampled_concept_file=concept_based/outputs_simple/gpqa_extended_all.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch${epoch_start}-${epoch_end}.jsonl

python concept_based/graph_construction_gpqa_seed_dist.py \
    --concept_comp_file ${concept_comp_file} --few_shot_file ${few_shot_file} \
    --sampled_concept_file ${sampled_concept_file} \
    --start_epoch 0 --end_epoch 100 --topic_freq_cut=0 --knowledge_point_freq_cut=0 --ncpus=32


