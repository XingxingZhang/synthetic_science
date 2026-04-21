"""
Implementation of MathScale

Step 2. Concept Graph Construction
"""
import os
import json, fire

import pandas as pd
import numpy as np

from collections import Counter, defaultdict
from multiprocessing import Pool
from tqdm import tqdm

from scipy.special import softmax


import random
import math

graph = None

class ConceptGraph:

    def __init__(self, topic_freq_cut=1, knowledge_point_freq_cut=1):
        self.all_topics = []
        self.all_knowledge_points = []
        self.all_topics_freq = None
        self.all_knowledge_points_freq = None

        self.all_topic2topic = {}
        self.all_topic2knowledge_point = {}
        self.all_knowledge2knowledge = {}
        self.all_knowledge2knowledge_edge = {}

        self.topic_freq_cut = topic_freq_cut
        self.knowledge_point_freq_cut = knowledge_point_freq_cut
    
    def get_topics_freq(self):
        return list(self.all_topics_freq)
    
    def get_knowledgepoints_freq(self):
        return list(self.all_knowledge_points_freq)
    
    def add_edge(self, x2y, x, y):
        if not x in x2y:
            x2y[x] = {}
        if not y in x2y[x]:
            x2y[x][y] = 1
        else:
            x2y[x][y] += 1
    
    def add(self, topics, knowledge_points):
        self.all_topics.extend(topics)
        self.all_knowledge_points.extend(knowledge_points)

        for u_topic in topics:
            for v_topic in topics:
                if u_topic == v_topic:
                    continue
                self.add_edge(self.all_topic2topic, u_topic, v_topic)
        
        for u_topic in topics:
            for v_knowledge_point in knowledge_points:
                self.add_edge(self.all_topic2knowledge_point, u_topic, v_knowledge_point)
        
        for u_kp in knowledge_points:
            for v_kp in knowledge_points:
                if u_kp == v_kp:
                    continue
                self.add_edge(self.all_knowledge2knowledge, u_kp, v_kp)
                edge = (u_kp, v_kp)
                self.all_knowledge2knowledge_edge[edge] = (
                    1 if not edge in self.all_knowledge2knowledge_edge 
                    else self.all_knowledge2knowledge_edge[edge] + 1
                )

    
    def trim_nodes(self, node_list, node_freq_cut):
        node_freq_ = Counter(node_list)
        if node_freq_cut > 0:
            node_freq = {}
            for k, v in node_freq_.items():
                if v > node_freq_cut:
                    node_freq[k] = v
        else:
            node_freq = node_freq_
        
        return node_freq
    
    def trim_edges(self, edges, valid_from_nodes, valid_to_nodes):
        new_edges = {}
        for u, adjlist in edges.items():
            if not u in valid_from_nodes:
                continue
            new_adjlist = {}
            for v, wt in adjlist.items():
                if not v in valid_to_nodes:
                    continue
                new_adjlist[v] = wt
            new_edges[u] = new_adjlist
        return new_edges
    
    def trim_edges_tuple_key(self, edges, valid_from_nodes, valid_to_nodes):
        new_edges = {}
        for edge, weight in edges.items():
            u, v = edge
            if u in valid_from_nodes and v in valid_to_nodes:
                new_edges[edge] = weight
        return new_edges

    def finalize(self):
        # apply frequency cut to topics and knowledge points
        self.all_topics_freq = self.trim_nodes(self.all_topics, self.topic_freq_cut)
        self.all_knowledge_points_freq = self.trim_nodes(self.all_knowledge_points, self.knowledge_point_freq_cut)

        # trim topic to topic edges
        self.all_topic2topic = self.trim_edges(self.all_topic2topic, self.all_topics_freq, self.all_topics_freq)
        print(f"topics are trimed to {len(self.all_topics_freq)} | {len(self.all_topic2topic)}")
        print(list(self.all_topics_freq.keys())[0])

        print(len(self.all_knowledge2knowledge_edge))

        # trim knowledge points edges
        self.all_topic2knowledge_point = self.trim_edges(self.all_topic2knowledge_point, self.all_topics_freq, self.all_knowledge_points_freq)
        self.all_knowledge2knowledge = self.trim_edges(self.all_knowledge2knowledge, self.all_knowledge_points_freq, self.all_knowledge_points_freq)
        self.all_knowledge2knowledge_edge = self.trim_edges_tuple_key(self.all_knowledge2knowledge_edge, self.all_knowledge_points_freq, self.all_knowledge_points_freq)

        print(f"kp are trimed to {len(self.all_knowledge_points_freq)} | {len(self.all_topic2knowledge_point)} | {len(self.all_knowledge2knowledge_edge)} | {len(self.all_knowledge2knowledge)}")
        print(list(self.all_knowledge_points_freq.keys())[0:3])


def remove_para(text):
    s_pos = text.find("(")
    e_pos = text.find(")", s_pos)
    if s_pos != -1 and e_pos != -1:
        return text[:s_pos] + text[e_pos+1:]
    else:
        return text


def remove_fullstop(lst):
    return [item[0:-1] if item.endswith('.') else item for item in lst]


def parse_topics_and_knowledge_points(gpt3_output):
    try:
        # gpt3_output = gpt3_output.replace("### Analysis:", "")
        if "**Topics:**" in gpt3_output:
            gpt3_output = gpt3_output.replace("**Topics:**", "Topics:")
        if "**Specific Knowledge Points:**" in gpt3_output:
            gpt3_output = gpt3_output.replace("**Specific Knowledge Points:**", "Specific Knowledge Points:")
        if "### Specific Knowledge Points:" in gpt3_output:
            gpt3_output = gpt3_output.replace("### Specific Knowledge Points:", "Specific Knowledge Points:")
        if "- Specific Knowledge Points:" in gpt3_output:
            gpt3_output = gpt3_output.replace("- Specific Knowledge Points:", "Specific Knowledge Points:")
        
        gpt3_output = gpt3_output.replace('"', '').replace('#', '')
        
        pos = gpt3_output.find("Topics:")
        if pos == -1:
            return None, None

        kp_pos = gpt3_output.find("Specific Knowledge Points:")
        if kp_pos == -1:
            return None, None

        gpt3_output = gpt3_output[pos:]

        topics = gpt3_output.split("Specific Knowledge Points:")[0].replace("Topics:", "").strip()
        topics = topics.split("\n")
        # topics = [remove_para(t.split(". ")[1]).strip() for t in topics]
        # more robust
        topics_tmp = []
        for t in topics:
            if not ". " in t:
                continue
            topic = remove_para(t.split(". ")[1]).strip()
            if len(topic) > 0:
                topics_tmp.append(topic)
        topics = topics_tmp

        knowledge_points = gpt3_output.split("Specific Knowledge Points:")[1].strip()
        pos = knowledge_points.find("\n\n")
        if pos != -1:
            knowledge_points = knowledge_points[:pos]
        knowledge_points = knowledge_points.split("\n")
        knowledge_points_t = []
        for t in knowledge_points:
            pos = t.find(". ")
            if pos != -1:
                t = t[pos + 2:]
            pos = t.find(":")
            if pos != -1:
                t = t[:pos]
            t = remove_para(t).strip()
            knowledge_points_t.append(t)
        
        # remove "."
        topics = remove_fullstop(topics)
        knowledge_points_t = remove_fullstop(knowledge_points_t)
    
        return topics, knowledge_points_t
    except Exception as e:
        print(e)
        print('+'*30 + "gpt output" + '+'*30)
        print(gpt3_output)
        print('-' * 60)
        raise


def build_graph(concept_comp_file, topic_freq_cut, knowledge_point_freq_cut):
    global graph
    graph = ConceptGraph(topic_freq_cut, knowledge_point_freq_cut)

    all_examples = []
    all_topics_len = []
    all_knowledge_points_len = []

    for line in open(concept_comp_file, encoding="utf8"):
        example = json.loads(line)
        topics, knowledge_points = parse_topics_and_knowledge_points(example["completion"])
        if topics is None:
            continue

        example["topics"] = topics
        example["knowledge_points"] = knowledge_points

        all_examples.append(example)
        graph.add(topics, knowledge_points)

        all_topics_len.append(len(topics))
        all_knowledge_points_len.append(len(knowledge_points))
    
    print("**** # topics dist ****")
    print( pd.Series(all_topics_len).value_counts() )
    print("**** # knowledge_points dist ****")
    print( pd.Series(all_knowledge_points_len).value_counts() )

    
    count_all_topics = Counter(graph.all_topics)
    # print( count_all_topics )
    print( len(count_all_topics) )

    print( len([(k, v) for k, v in count_all_topics.items() if v >= 2]) )
    # print( sorted([(k, v) for k, v in count_all_topics.items() if v >= 2], key=lambda x: x[1])[:30] )

    graph.finalize()

    return all_examples


def create_demonstrations(all_examples, graph, few_shot_file):
    new_all_knowledge_point_num = []
    with open(few_shot_file, "w") as fw:
        for example in all_examples:
            topics = example.pop("topics")
            topics_t = []
            for t in topics:
                if (t in graph.all_topics_freq ) and (t not in topics_t):
                    topics_t.append(t)
                    
            knowledge_points = example.pop("knowledge_points")
            knowledge_points_t = []
            for t in knowledge_points:
                if (t in graph.all_knowledge_points_freq) and (t not in knowledge_points_t):
                    knowledge_points_t.append(t)

            example["topics"] = topics_t
            example["knowledge_points"] = knowledge_points_t
            
            if example["topics"] == []:
                continue
            if example["knowledge_points"] == []:
                continue
                
            new_all_knowledge_point_num.append(len(example["knowledge_points"]))
            example = json.dumps(example)
            fw.write(example + "\n")

    print("** new_all_knowledge_point_num ** | dist **")
    print( pd.Series(new_all_knowledge_point_num).value_counts() )


def weighted_choice(neighbors, rest_nodes, rng=None, eps=1e-5):
    full_neighbors = []
    for n, w in neighbors:
        full_neighbors.append( (n, math.log(w+eps)) )
    for n in rest_nodes:
        full_neighbors.append( (n, math.log(0+eps)) )
    
    nodes = []
    log_weights = []
    for n, log_w in full_neighbors:
        nodes.append(n)
        log_weights.append(log_w)
    softmax_probs = softmax(log_weights)
    if rng:
        return rng.choice(nodes, replace=False, p=softmax_probs).tolist()
    return np.random.choice(nodes, replace=False, p=softmax_probs).tolist()


def weighted_random_dfs(start, edges, all_nodes, target_length, path=None, rng=None, all_adjlist=None):
    if path is None:
        path = [start]

    if len(path) == target_length:
        return path
    
    if all_adjlist:
        adjlist = all_adjlist[start]
        neighbors = [(n, w) for n, w in adjlist.items() if n not in path]
    else:
        neighbors = [(n, w) for (s, n), w in edges.items() if s == start and n not in path]
    if neighbors == []:
        return None
    touched_nodes = set([n for n, w in neighbors] + path)
    rest_nodes = [n for n in all_nodes if n not in touched_nodes]

    next_node = weighted_choice(neighbors, rest_nodes, rng)

    return weighted_random_dfs(next_node, edges, all_nodes, target_length, path + [next_node], rng, all_adjlist=all_adjlist)


def my_random_process(touched_nodes, count_dict, all_nodes, rng):
    if len(count_dict) == 0:
        return []
    neighbors = []
    for t, c in count_dict.items():
        neighbors.append( (t, c) )
    touched_nodes = set(touched_nodes + [n for n, c in neighbors])
    rest_nodes = [n for n in all_nodes if n not in touched_nodes]
    
    next_node = weighted_choice(neighbors, rest_nodes, rng)
    return next_node


def sample_concepts(i, seed):
    global graph

    rng = np.random.RandomState(seed)

    current_topic = graph.get_topics_freq()[i]

    if current_topic not in graph.all_topic2topic:
        return []
    current_topic2topic_count = graph.all_topic2topic[current_topic]
    current_topic2knowledge_point_count = graph.all_topic2knowledge_point[current_topic]

    outputs = []
    
    # First single topic DFS
    if len(current_topic2knowledge_point_count) == 0:
        return []
    starting_node = my_random_process([current_topic], current_topic2knowledge_point_count, graph.all_knowledge_points_freq, rng=rng)

    path_length = rng.choice([1, 2, 3, 4, 5])

    path = weighted_random_dfs(starting_node, graph.all_knowledge2knowledge_edge, graph.all_knowledge_points_freq, path_length, rng=rng, all_adjlist=graph.all_knowledge2knowledge)
    if path is not None:
        dump = {"topics": [current_topic], "knowledge_points": path}
        dump = json.dumps(dump)
        outputs.append(dump)
    
    other_topic = my_random_process([current_topic], current_topic2topic_count, graph.all_topics_freq, rng=rng)
    if other_topic == []:
        return outputs
    other_topic2knowledge_point_count = graph.all_topic2knowledge_point[other_topic]
    
    # Second two topics DFS
    intersect_nodes = [cur_2kp for cur_2kp in current_topic2knowledge_point_count.keys() if cur_2kp in other_topic2knowledge_point_count]
    if len(intersect_nodes) == 0:
        return outputs
    intersect_topic2knowledge_point_count = {}
    for node in intersect_nodes:
        count = current_topic2knowledge_point_count[node] + other_topic2knowledge_point_count[node]
        intersect_topic2knowledge_point_count[node] = count
    starting_node = my_random_process([current_topic, other_topic], intersect_topic2knowledge_point_count, graph.all_knowledge_points_freq, rng=rng)
    path_length = rng.choice([1, 2, 3, 4, 5])
    path = weighted_random_dfs(starting_node, graph.all_knowledge2knowledge_edge, graph.all_knowledge_points_freq, path_length, rng=rng, all_adjlist=graph.all_knowledge2knowledge)
    if path is not None:
        dump = {"topics": [current_topic, other_topic], "knowledge_points": path}
        dump = json.dumps(dump)
        outputs.append(dump)
    return outputs

def sample_concepts_driver(args):
    return sample_concepts(*args)

def main(
    concept_comp_file="data_local/concept_extraction.4o.completion.jsonl",
    few_shot_file="data_local/concept_extraction.4o.refactor.fewshot_demonstration.jsonl",
    sampled_concept_file="data_local/concept_extraction.4o.refactor.concept_graph.jsonl",
    num_epochs=1000,
    topic_freq_cut=1, knowledge_point_freq_cut=1,
    ncpu=32,
):
    all_examples = build_graph(concept_comp_file, topic_freq_cut, knowledge_point_freq_cut)
    create_demonstrations(all_examples, graph, few_shot_file)
    print( sample_concepts(0, 42) )

    fw = open(sampled_concept_file, "w")

    for seed in tqdm(range(42, 42 + num_epochs), desc="global"):
        pbar = tqdm([(i, seed) for i in range(len(graph.all_topics_freq))], desc=f"Iter {seed - 41}")
        with Pool(ncpu) as p:
            for outputs in p.imap(sample_concepts_driver, pbar):
                for output in outputs:
                    fw.write(output + "\n")

    fw.close()


if __name__ == "__main__":
    fire.Fire(main)
