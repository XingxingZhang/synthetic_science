"""
Implementation of MathScale

Step 3. Sampled Concept to Q&A Generation Prompts
"""
import os
import re
import json
import random
import fire, hashlib

import pandas as pd
from tqdm import tqdm
import numpy as np

from typing import List, Dict, Tuple
from collections import OrderedDict, deque, defaultdict, Counter

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



def create_key(topics, knowledge_points):
    key_topics = [t.strip().lower() for t in topics if t.strip().lower() != ""]
    key_knowledge_points = [t.strip().lower() for t in knowledge_points if t.strip().lower() != ""]
    key = "\n".join(sorted(key_topics)) + "\n" + "\n".join(sorted(key_knowledge_points))
    return key


def load_demonstrations(few_shot_file):        
    corpus = defaultdict(list)
    train_examples = []
    with open(few_shot_file) as fd:
        for line in fd:
            example = json.loads(line)
            example["question"] = make_gpqa_multi_choice_question(example) # example["question"].replace("\n\n", "\n")
            keywords = tuple(sorted(example["knowledge_points"]))
            corpus[keywords].append(example)
            train_examples.append(example)
    print("# train_examples: ", len(train_examples))
    print("len(corpus): ", len(corpus))

    # Inverted index
    inverted_index = defaultdict(list)

    # Build the inverted index
    for keywords, values in corpus.items():
        for keyword in keywords:
            inverted_index[keyword].append((keywords, values))
    
    return train_examples, inverted_index


def jaccard_similarity(set1: set, set2: set) -> float:
    """
    Compute the Jaccard similarity between two sets.
    """
    intersection = len(set1.intersection(set2))
    union = len(set1) + len(set2) - intersection
    return intersection / union if union != 0 else 0


def query_index_topk(query: List[str], inverted_index: Dict[str, List[Tuple]], k: int) -> Dict[Tuple, List[int]]:
    """
    Query the inverted index and return the top-k results based on Jaccard similarity.
    """
    query_set = set(query)
    candidate_docs = {}
    
    # Retrieve candidate document sets based on the query
    for keyword in query:
        if keyword in inverted_index:
            for doc_keywords, doc_values in inverted_index[keyword]:
                candidate_docs[doc_keywords] = doc_values
    
    # Compute Jaccard similarity for each candidate document set
    jaccard_scores = {}
    for doc_keywords, doc_values in candidate_docs.items():
        jaccard_scores[doc_keywords] = jaccard_similarity(query_set, set(doc_keywords))
    
    # Sort by Jaccard similarity (in descending order) and select the top-k
    sorted_results = OrderedDict(sorted(jaccard_scores.items(), key=lambda x: x[1], reverse=True)[:k])
    
    # Return the sorted results along with their associated values
    return {k: candidate_docs[k] for k in sorted_results.keys()}


def load_sampled_concepts(sampled_concept_file):
    touched_key = set()
    test_examples = []
    cnt = 0
    with open(sampled_concept_file) as fd:
        for line in fd:
            cnt += 1
            example = json.loads(line)
            topics = example["topics"]
            knowledge_points = example["knowledge_points"]
            key = create_key(topics, knowledge_points)
            if key not in touched_key:
                test_examples.append(example)
                touched_key.add(key)
    print(f"original # test_examples {cnt} | real # test_examples: {len(test_examples)}")
    # random.seed(1024)
    # random.shuffle(test_examples)
    return test_examples


def round_robin_sort(elements):
    # Organize elements into separate lists for each domain
    domain_lists = defaultdict(deque)
    for element in elements:
        if 'data_source' in element:
            domain_lists[element['data_source']].append(element)
        elif 'source' in element:
            domain_lists[element['source']].append(element)
        else:
            domain_lists['UNIFIED_SOURCE'].append(element)

    # Interleave elements from these lists
    sorted_elements = []
    while domain_lists:
        for domain, elements_deque in list(domain_lists.items()):
            sorted_elements.append(elements_deque.popleft())
            
            # Remove the deque from the dictionary if it's empty
            if not elements_deque:
                del domain_lists[domain]

    return sorted_elements


def str2sha256(my_string):
    encoded_string = my_string.encode()
    sha256_hash = hashlib.sha256(encoded_string)
    hex_dig = sha256_hash.hexdigest()

    return hex_dig


def get_prompt(example_id, example, prompt_template):
    global train_examples, inverted_index
    rng = random.Random(example_id + 42)
    
    topics = "\n".join([f"{i+1}. {t}" for i, t in enumerate(example["topics"])])
    knowledge_points = "\n".join([f"{i+1}. {t}" for i, t in enumerate(example["knowledge_points"])])
    my_example = f"Topics:\n{topics}\nKnowledge Points:\n{knowledge_points}"

    top_k_few_shot_examples = query_index_topk(example["knowledge_points"], inverted_index, k=4)
    few_shot_examples = []
    for keywords, examples in top_k_few_shot_examples.items():
        examples = round_robin_sort(examples)
        few_shot_examples.extend(examples)
    few_shot_examples = few_shot_examples[:8]
    few_shot_num_to_add = 8 - len(few_shot_examples)
    if few_shot_num_to_add > 0:
        few_shot_examples.extend(rng.sample(train_examples, few_shot_num_to_add))
    rng.shuffle(few_shot_examples)

    few_shot_examples_t = []
    for fs_example in few_shot_examples:
        topics = fs_example["topics"]
        topics = [f"{i+1}. {t}" for i, t in enumerate(topics)]
        topics = "\n".join(topics)
        knowledge_points = fs_example["knowledge_points"]
        knowledge_points = [f"{i+1}. {t}" for i, t in enumerate(knowledge_points)]
        knowledge_points = "\n".join(knowledge_points)
        one_train_example = f"Topics:\n{topics}\nKnowledge Points:\n{knowledge_points}\nCreated Question:\n{fs_example['question'].strip()}"
        few_shot_examples_t.append(one_train_example)
    few_shot_examples_t = "\n\n".join(few_shot_examples_t)

    prompt = prompt_template.strip().replace("{{ few_shot_train_examples }}", few_shot_examples_t).replace("{{ my_example }}", my_example)
    uuid = str2sha256(create_key(example['topics'], example['knowledge_points']))
    data = {"prompt": prompt, "uuid": uuid}

    return json.dumps(data)


def get_prompt_driver(args):
    return get_prompt(*args)


def generate_prompts(sampled_concepts, prompt_template, output_prompt_file, ncpus):
    from multiprocessing import Pool

    with open(output_prompt_file, "w", encoding="utf8") as fout:
        parameters = []
        for example_id, example in enumerate(tqdm(sampled_concepts, desc="generating prompts")):
            parameters.append((example_id, example, prompt_template))
        
        pbar = tqdm(parameters, desc=f"Generate prompts")
        with Pool(ncpus) as p:
            for output in p.imap(get_prompt_driver, pbar):
                fout.write(output + "\n")


def main(
    few_shot_file="data_local/concept_extraction.4o.refactor.fewshot_demonstration.jsonl",
    sampled_concept_file="data_local/concept_extraction.4o.refactor.concept_graph.jsonl",
    prompt_template_file="glan/prompts/math/concept2prompts.md",
    output_prompt_file="data_local/concept_extraction.4o.refactor.concept_graph.prompts.jsonl",
    ncpus=-1,
):
    global train_examples, inverted_index
    train_examples, inverted_index = load_demonstrations(few_shot_file)
    sampled_concepts = load_sampled_concepts(sampled_concept_file)
    prompt_template = open(prompt_template_file, encoding="utf8").read()
    ncpus = None if ncpus <= 0 else ncpus
    generate_prompts(sampled_concepts, prompt_template, output_prompt_file, ncpus)


if __name__ == "__main__":
    fire.Fire(main)

