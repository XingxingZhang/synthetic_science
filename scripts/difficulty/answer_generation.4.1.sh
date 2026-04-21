


# crawl using GPT-4.1
codedir=/home/xizhang/projects/gpt_crawler_tc_pro
codedir=/home/xizhang/projects/gpt_crawler_trapi

model=gpt-4.1_2025-04-14
reason_effort=none

ncpus=64

curdir=`pwd`

promptfile=/data/xingxing/gpqa_dataset/Nemotron-Science-v1_problems.fixed.prompt.jsonl
outdir=/data/xingxing/gpqa_dataset/Nemotron-Science-v1_problems.fixed.completions

mkdir -p ${outdir}

for id in `seq 0 7`
do

    outfile=${outdir}/${id}.${model}_${reason_effort}.jsonl

    cd $codedir

    # . azure/gpt_api/setup.sh

    python -u azure/gpt_crawler_mp.py $promptfile $outfile --model $model --num_processes $ncpus \
        --temperature 0.7 --top_p 0.95 \
        --max_num_tries 123456789 --max_text_tokens 128000 --max_gen_tokens 16384  2>&1 | tee ${outfile}.log.txt

    cd $curdir

done
