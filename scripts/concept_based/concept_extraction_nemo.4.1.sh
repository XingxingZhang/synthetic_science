
#!/bin/bash

set -e

. pt

# PROMPT_FILE="concept_based/prompts/concept_extraction_science.md"
PROMPT_FILE="concept_based/prompts/concept_extraction_science_simple.md"
WORKDIR=/data/xingxing/gpqa_dataset


# python concept_based/concept_extraction.py \
#     --seed_question_file ${WORKDIR}/Nemotron-Science-v1_problems.jsonl \
#     --prompt_file ${PROMPT_FILE} \
#     --output_file ${WORKDIR}/prompts/Nemotron-Science-v1_concept_extraction_prompts.jsonl \
#     --data_option nemotron


# crawl using GPT-4.1
codedir=/home/xizhang/projects/gpt_crawler_trapi

model=gpt-4.1_2025-04-14
reason_effort=none


ncpus=32

curdir=`pwd`

promptfile=${WORKDIR}/prompts/Nemotron-Science-v1_concept_extraction_prompts.jsonl
outfile=${WORKDIR}/prompts/Nemotron-Science-v1_concept_extraction_completions.${model}_${reason_effort}.jsonl

cd $codedir

# . azure/gpt_api/setup.sh

python -u azure/gpt_crawler_mp.py $promptfile $outfile --model $model --num_processes $ncpus \
    --temperature 0.7 --top_p 0.95 \
    --max_num_tries 123456789 --max_text_tokens 128000 --max_gen_tokens 8192  2>&1 | tee ${outfile}.log.txt

cd $curdir
