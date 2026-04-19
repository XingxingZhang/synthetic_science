
"""
Implementation of MathScale

Step 1. Concept Extraction
"""

import os, sys, fire, json
import random
random.seed(42)


GPQA_QUESTION_TEMPLATE = """
{Question}

A) {A}
B) {B}
C) {C}
D) {D}
"""


def make_gpqa_multi_choice_question(data):
    gold_index = random.randint(0, 3)
    choices = [data["Incorrect Answer 1"], data["Incorrect Answer 2"], data["Incorrect Answer 3"]]
    choices.insert(gold_index, data["Correct Answer"])
    mc_question = GPQA_QUESTION_TEMPLATE.format(
        A=choices[0], B=choices[1], C=choices[2], D=choices[3], Question=data["Question"]
    )

    return mc_question


def concept_extraction(
    seed_question_file="",
    prompt_file="concept_based/prompts/concept_extraction.md",
    output_file="",
    data_option="gpqa", # can be gpqa, nemotron
):
    assert data_option in ["gpqa", "nemotron"]
    
    prompttemplate = open(prompt_file, encoding="utf8").read()
    fout = open(output_file, "w", encoding="utf8")

    cnt = 0
    for line in open(seed_question_file, encoding="utf8"):
        cnt += 1
        data = json.loads(line)
        if data_option == "gpqa":
            question = make_gpqa_multi_choice_question(data)
        elif data_option == "nemotron":
            question = data["problem"]
        else:
            raise Exception(f"{data_option} not suported yet!!!")
        
        prompt = prompttemplate.replace("{{ question }}", question)
        data["prompt"] = prompt
        if cnt <= 5:
            print(prompt)
            print('-' * 30)

        fout.write(json.dumps(data) + "\n")
    
    fout.close()


if __name__ == "__main__":
    fire.Fire(concept_extraction)

