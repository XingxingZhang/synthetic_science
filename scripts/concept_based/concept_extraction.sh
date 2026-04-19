#!/bin/bash

set -e

. pt

# PROMPT_FILE="concept_based/prompts/concept_extraction_science.md"
PROMPT_FILE="concept_based/prompts/concept_extraction_science_simple.md"
OUTPUT_DIR="concept_based/outputs_simple"

mkdir -p "${OUTPUT_DIR}"

# for name in gpqa_diamond gpqa_extended-diamond; do
#     python concept_based/concept_extraction.py \
#         --seed_question_file "gpqa_jsonls/${name}.jsonl" \
#         --prompt_file "${PROMPT_FILE}" \
#         --output_file "${OUTPUT_DIR}/${name}.concept_prompts.jsonl"
# done


# crawl using GPT-5.4
codedir=/home/xizhang/projects/gpt_crawler_tc_pro

model=gpt-5.4
reason_effort=medium

ncpus=32

curdir=`pwd`

promptfile=$curdir/concept_based/outputs/gpqa_diamond.concept_prompts.jsonl
outfile=$curdir/concept_based/outputs/gpqa_diamond.concept_completions.${model}_${reason_effort}.jsonl

cd $codedir

. azure/gpt_api/setup.sh

python -u azure/gpt_crawler_mp.py $promptfile $outfile --model $model --num_processes $ncpus \
    --temperature 1.0 --top_p 1.0  --reasoning_effort ${reason_effort} \
    --max_num_tries 123456789 --max_text_tokens 128000 --max_gen_tokens 16000  2>&1 | tee ${outfile}.log.txt

cd $curdir




curdir=`pwd`

promptfile=$curdir/concept_based/outputs/gpqa_extended-diamond.concept_prompts.jsonl
outfile=$curdir/concept_based/outputs/gpqa_extended-diamond.concept_completions.${model}_${reason_effort}.jsonl

cd $codedir

. azure/gpt_api/setup.sh

python -u azure/gpt_crawler_mp.py $promptfile $outfile --model $model --num_processes $ncpus \
    --temperature 1.0 --top_p 1.0  --reasoning_effort ${reason_effort} \
    --max_num_tries 123456789 --max_text_tokens 128000 --max_gen_tokens 16000  2>&1 | tee ${outfile}.log.txt

cd $curdir

# ========================
# ========================

curdir=`pwd`

promptfile=$curdir/concept_based/outputs_simple/gpqa_diamond.concept_prompts.jsonl
outfile=$curdir/concept_based/outputs_simple/gpqa_diamond.concept_completions.${model}_${reason_effort}.jsonl

cd $codedir

. azure/gpt_api/setup.sh

python -u azure/gpt_crawler_mp.py $promptfile $outfile --model $model --num_processes $ncpus \
    --temperature 1.0 --top_p 1.0  --reasoning_effort ${reason_effort} \
    --max_num_tries 123456789 --max_text_tokens 128000 --max_gen_tokens 16000  2>&1 | tee ${outfile}.log.txt

cd $curdir



curdir=`pwd`

promptfile=$curdir/concept_based/outputs_simple/gpqa_extended-diamond.concept_prompts.jsonl
outfile=$curdir/concept_based/outputs_simple/gpqa_extended-diamond.concept_completions.${model}_${reason_effort}.jsonl

cd $codedir

. azure/gpt_api/setup.sh

python -u azure/gpt_crawler_mp.py $promptfile $outfile --model $model --num_processes $ncpus \
    --temperature 1.0 --top_p 1.0  --reasoning_effort ${reason_effort} \
    --max_num_tries 123456789 --max_text_tokens 128000 --max_gen_tokens 16000  2>&1 | tee ${outfile}.log.txt

cd $curdir
