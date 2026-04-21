"""
Step 1. Concept Extraction from Docs
Step 2. Concept Graph Construction
"""
import os
import json, fire, re

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
        print("*** topic example: ", list(self.all_topics_freq.keys())[0])
        print('\n')

        print("number of edges kp 2 kp", len(self.all_knowledge2knowledge_edge))

        # trim knowledge points edges
        self.all_topic2knowledge_point = self.trim_edges(self.all_topic2knowledge_point, self.all_topics_freq, self.all_knowledge_points_freq)
        self.all_knowledge2knowledge = self.trim_edges(self.all_knowledge2knowledge, self.all_knowledge_points_freq, self.all_knowledge_points_freq)
        self.all_knowledge2knowledge_edge = self.trim_edges_tuple_key(self.all_knowledge2knowledge_edge, self.all_knowledge_points_freq, self.all_knowledge_points_freq)

        print(f"kp are trimed to {len(self.all_knowledge_points_freq)} | # topic2kp {len(self.all_topic2knowledge_point)} | # kp2kp edges {len(self.all_knowledge2knowledge_edge)} | # kp2kp {len(self.all_knowledge2knowledge)}")
        print(list(self.all_knowledge_points_freq.keys())[0:3])


def remove_para(text):
    s_pos = text.find("(")
    e_pos = text.find(")", s_pos)
    if s_pos != -1 and e_pos != -1:
        return text[:s_pos] + text[e_pos+1:]
    else:
        return text

def remove_boldface(text):
    if text.startswith("**"):
        text = text[2:]
    if text.endswith("**"):
        text = text[0:-2]
    
    return text.strip()

def remove_fullstop(lst):
    return [item[0:-1] if item.endswith('.') else item for item in lst]


def parse_subject_level(data):
    """
    Parses XML-like data using regex and returns a dictionary with 'level' and 'subject'.

    Args:
        data (str): The XML-like data string to parse.

    Returns:
        dict: A dictionary with keys 'level' and 'subject'. Values are None if parsing fails.
    """
    patterns = {
        'level': r'<level>\s*(.*?)\s*</level>',
        'subject': r'<subject>\s*(.*?)\s*</subject>'
    }
    result = {}
    
    for key, pattern in patterns.items():
        match = re.search(pattern, data, re.IGNORECASE | re.DOTALL)
        if match:
            value = match.group(1).strip()
            result[key] = value if value else None
        else:
            result[key] = None
    
    return result


def parse_concept_extraction_completion(completion):
    parsed_item = parse_subject_level(completion)
    try:
        completion = completion.strip()
        if completion.startswith('"') and completion.endswith('"'):
            completion = completion[1:-1]
        if completion.startswith('```') and completion.endswith('```'):
            lines = completion.splitlines()
            out_lines = [line for line in lines if not line.startswith('```')]
            completion = '\n'.join(out_lines)
        if "**Topics:**" in completion:
            completion = completion.replace("**Topics:**", "Topics:")
        # Key Concepts:
        # simplify "Specific Key Concepts"
        if "**Key Concepts:**" in completion:
            completion = completion.replace("**Key Concepts:**", "Key Concepts:")
        if "### Key Concepts:" in completion:
            completion = completion.replace("### Key Concepts:", "Key Concepts:")
        if "- Key Concepts:" in completion:
            completion = completion.replace("- Key Concepts:", "Key Concepts:")
        
        completion = completion.replace('"', '').replace('#', '')
        
        pos = completion.find("Topics:")
        if pos == -1:
            parsed_item['topics'] = None
            parsed_item['knowledge_points'] = None
            return parsed_item

        kp_pos = completion.find("Key Concepts:")
        if kp_pos == -1:
            parsed_item['topics'] = None
            parsed_item['knowledge_points'] = None
            return parsed_item

        completion = completion[pos:]

        topics = completion.split("Key Concepts:")[0].replace("Topics:", "").strip()
        topics = topics.split("\n")
        # more robust
        topics_tmp = []
        for t in topics:
            if not ". " in t:
                continue
            topic = remove_para(t.split(". ")[1]).strip()
            topic = remove_boldface(topic)
            if len(topic) > 0:
                topics_tmp.append(topic)
        topics = topics_tmp

        knowledge_points = completion.split("Key Concepts:")[1].strip()
        pos = knowledge_points.find("\n\n")
        if pos != -1:
            knowledge_points = knowledge_points[:pos]
        knowledge_points = knowledge_points.split("\n")
        knowledge_points_tmp = []
        for t in knowledge_points:
            pos = t.find(". ")
            if pos != -1:
                t = t[pos + 2:]
            pos = t.find(":")
            if pos != -1:
                t = t[:pos]
            t = remove_para(t).strip()
            t = remove_boldface(t)
            if len(t) > 0:
                knowledge_points_tmp.append(t)
        
        # remove "."
        topics = remove_fullstop(topics)
        knowledge_points = remove_fullstop(knowledge_points_tmp)

        parsed_item['topics'] = topics
        parsed_item['knowledge_points'] = knowledge_points
        return parsed_item
    except Exception as e:
        print(e)
        print('+'*30 + "completion" + '+'*30)
        print(completion)
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
        parsed_item = parse_concept_extraction_completion(example["completion"])
        topics, knowledge_points = parsed_item["topics"], parsed_item["knowledge_points"]
        if topics is None:
            continue

        example["topics"] = topics
        example["knowledge_points"] = knowledge_points
        example["level"] = parsed_item["level"]
        example["subject"] = parsed_item["subject"]

        all_examples.append(example)
        graph.add(topics, knowledge_points)

        if len(all_examples) <= 10:
            print(f"example {len(all_examples)} - {parsed_item}")

        all_topics_len.append(len(topics))
        all_knowledge_points_len.append(len(knowledge_points))
    
    print("\n**** # topics dist ****")
    print( pd.Series(all_topics_len).value_counts() )
    print('\n')
    print("**** # knowledge_points dist ****")
    print( pd.Series(all_knowledge_points_len).value_counts() )
    print('\n\n\n')

    count_all_topics = Counter(graph.all_topics)
    print( "raw num of topics:", len(count_all_topics) )

    print( f"num of topics after removing freq <= {topic_freq_cut}", len([(k, v) for k, v in count_all_topics.items() if v >= topic_freq_cut + 1]) )

    graph.finalize()

    return all_examples


def create_demonstrations(all_examples, graph, few_shot_file):
    new_all_topic_num = []
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
            new_all_topic_num.append(len(example["topics"]))
            example = json.dumps(example)
            fw.write(example + "\n")

    print("** new_all_knowledge_point_num ** | dist **")
    print( pd.Series(new_all_knowledge_point_num).value_counts() )
    print("** new_all_topic_num ** | dist **")
    print( pd.Series(new_all_topic_num).value_counts() )


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


def my_random_process(touched_nodes, count_dict, all_nodes, rng, disable_eps=True):
    if len(count_dict) == 0:
        return []
    neighbors = []
    for t, c in count_dict.items():
        neighbors.append( (t, c) )

    if not disable_eps:
        touched_nodes = set(touched_nodes + [n for n, c in neighbors])
        rest_nodes = [n for n in all_nodes if n not in touched_nodes]
    else:
        rest_nodes = []
    
    next_node = weighted_choice(neighbors, rest_nodes, rng)
    return next_node


def sample_concepts(i, seed, max_num_topics=3, min_num_kp=5, max_num_kp=12):
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

    path_length = rng.choice(list(range(min_num_kp, max_num_kp+1)))

    path = weighted_random_dfs(starting_node, graph.all_knowledge2knowledge_edge, graph.all_knowledge_points_freq, path_length, rng=rng, all_adjlist=graph.all_knowledge2knowledge)
    if path is not None:
        dump = {"topics": [current_topic], "knowledge_points": path}
        dump = json.dumps(dump)
        outputs.append(dump)
    
    # multiple topics DFS
    cur_topics = [current_topic]
    cur_intersect_nodes = list(current_topic2knowledge_point_count.keys())
    cur_intersect_topic2knowledge_point_count = dict(current_topic2knowledge_point_count)
    for _ in range(1, max_num_topics):
        current_topic2topic_count = graph.all_topic2topic[cur_topics[-1]]
        other_topic = my_random_process(cur_topics, current_topic2topic_count, graph.all_topics_freq, rng=rng)
        if other_topic == []:
            return outputs
        other_topic2knowledge_point_count = graph.all_topic2knowledge_point[other_topic]
        cur_topics.append(other_topic)
        
        intersect_nodes = [cur_2kp for cur_2kp in cur_intersect_nodes if cur_2kp in other_topic2knowledge_point_count]
        if len(intersect_nodes) == 0:
            return outputs
        cur_intersect_nodes = intersect_nodes

        intersect_topic2knowledge_point_count = {}
        for node in intersect_nodes:
            count = cur_intersect_topic2knowledge_point_count[node] + other_topic2knowledge_point_count[node]
            intersect_topic2knowledge_point_count[node] = count
        cur_intersect_topic2knowledge_point_count = intersect_topic2knowledge_point_count

        starting_node = my_random_process(cur_topics, intersect_topic2knowledge_point_count, graph.all_knowledge_points_freq, rng=rng)
        path_length = rng.choice(list(range(min_num_kp, max_num_kp+1)))
        path = weighted_random_dfs(starting_node, graph.all_knowledge2knowledge_edge, graph.all_knowledge_points_freq, path_length, rng=rng, all_adjlist=graph.all_knowledge2knowledge)
        if path is not None:
            dump = {"topics": cur_topics, "knowledge_points": path}
            dump = json.dumps(dump)
            outputs.append(dump)

    return outputs


def sample_concepts_driver(args):
    return sample_concepts(*args)

def main(
    concept_comp_file="data_local/CC-MAIN-2013-20.48.completion.jsonl",
    few_shot_file="data_local/CC-MAIN-2013-20.48.fewshot_demonstration.jsonl",
    sampled_concept_file="data_local/CC-MAIN-2013-20.48.concept_graph.jsonl",
    start_epoch=0,
    end_epoch=1000,
    topic_freq_cut=1, knowledge_point_freq_cut=1,
    ncpus=32,
    max_num_topics=3, min_num_kp=3, max_num_kp=10,
):
    if ncpus < 0:
        ncpus = None
    print(locals())

    all_examples = build_graph(concept_comp_file, topic_freq_cut, knowledge_point_freq_cut)
    create_demonstrations(all_examples, graph, few_shot_file)
    print( sample_concepts(0, 42, max_num_topics, min_num_kp, max_num_kp) )
    print( sample_concepts(1, 42, max_num_topics, min_num_kp, max_num_kp) )
    print( sample_concepts(2, 42, max_num_topics, min_num_kp, max_num_kp) )

    fw = open(sampled_concept_file, "w")

    for seed in tqdm(range(42 + start_epoch, 42 + end_epoch), desc="global"):
        pbar = tqdm([(i, seed, max_num_topics, min_num_kp, max_num_kp) for i in range(len(graph.all_topics_freq))], desc=f"Iter {seed - 41}")
        with Pool(ncpus) as p:
            for outputs in p.imap(sample_concepts_driver, pbar):
                for output in outputs:
                    fw.write(output + "\n")

    fw.close()


if __name__ == "__main__":
    fire.Fire(main)
