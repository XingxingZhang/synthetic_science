#!/bin/bash

set -e

. pt

codedir=/home/xizhang/projects/gpt_crawler_tc_pro

model=gpt-5.4
reason_effort=medium

ncpus=8

curdir=`pwd`

for name in gpqa_diamond gpqa_extended-diamond; do
    promptfile=$curdir/concept_based/outputs_simple/${name}.concept_completions.${model}_${reason_effort}.no_completion.jsonl
    outfile=$curdir/concept_based/outputs_simple/${name}.concept_completions.${model}_${reason_effort}.leftovers.jsonl

    if [ ! -s "$promptfile" ]; then
        echo "Skipping ${name}: no leftovers in ${promptfile}"
        continue
    fi

    cd $codedir

    . azure/gpt_api/setup.sh

    python -u azure/gpt_crawler_mp.py $promptfile $outfile --model $model --num_processes $ncpus \
        --temperature 1.0 --top_p 1.0  --reasoning_effort ${reason_effort} \
        --max_num_tries 123456789 --max_text_tokens 128000 --max_gen_tokens 16000  2>&1 | tee ${outfile}.log.txt

    cd $curdir
done
