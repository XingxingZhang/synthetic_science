
# crawl using GPT-5.4
codedir=/home/xizhang/projects/gpt_crawler_tc_pro
codedir=/home/xizhang/projects/gpt_crawler_tc_pro3

model=gpt-5.4
reason_effort=high

ncpus=32

curdir=`pwd`

promptfile=${curdir}/concept_based/outputs_simple/gpqa_extended_all.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.prompts.jsonl
outfile=${curdir}/concept_based/outputs_simple/gpqa_extended_all.concept_completions.gpt-5.4_medium.v2.concept_graph.epoch0-100.20k.p1.completions.${model}_${reason_effort}.jsonl

cd $codedir

. azure/gpt_api/setup.sh

python -u azure/gpt_crawler_mp.py $promptfile $outfile --model $model --num_processes $ncpus \
    --temperature 1.0 --top_p 1.0  --reasoning_effort ${reason_effort} \
    --max_num_tries 123456789 --max_text_tokens 128000 --max_gen_tokens 96000  2>&1 | tee ${outfile}.log.txt

cd $curdir


