from utils.llm_prompts import *
import random
import os
from rapidfuzz import process

VH_ALL_STATES = [x for x in VH_graph_prompt_translation.split('The possible states include: [')[1].split(']')[0].split(', ')]
VH_ALL_RELATIONS = [x for x in VH_graph_prompt_translation.split('The possible relations include: [')[1].split(']')[0].split(', ')]

def call_api(API_client, llm_in, API_model_type="gpt-4o-mini"):
    completion = API_client.chat.completions.create(
        model=API_model_type,
        messages=[
            {
                "role": "user",
                "content": llm_in,
            }
        ]
    )
    llm_out = completion.choices[0].message.content
    return llm_out, completion.usage.prompt_tokens, completion.usage.completion_tokens

def VH_AW_translation(API_client, task_goal, env_name="AW"):
    all_num_token_in = 0
    all_num_token_out = 0
    
    llm_in = VH_graph_prompt_translation + task_goal + '\nFacts: '
    
    iii = 0
    while True:
        llm_out, num_token_in, num_token_out = call_api(API_client, llm_in, API_model_type="gpt-4.1-mini")
        all_num_token_in += num_token_in
        all_num_token_out += num_token_out
        
        iii += 1
        if iii > 10:
            print([task_goal, llm_out])
            return None, [all_num_token_in, all_num_token_out, iii]

        if llm_out is None:
            continue
        if not (llm_out.strip().startswith('[') and llm_out.strip().endswith(']')):
            continue
        if llm_out == "[]":
            continue
        
        llm_out = llm_out.strip()
        predicates = []
        flag = True
        for x in llm_out[1:-1].split('), ('):
            x = x.strip().replace('(', '').replace(')', '')
            predicate = []
            elements = x.split(',')
            for element in elements:
                predicate.append(element.strip())
            if not ((predicate[0] in VH_ALL_STATES and len(predicate) == 2) \
                or (predicate[0] in VH_ALL_RELATIONS and len(predicate) == 3)): 
                flag = False 
            for x in predicate[1:]:
                if not '-' in x: 
                    flag = False 
            predicates.append(predicate)
        if flag:
            break
    return predicates, [all_num_token_in, all_num_token_out, iii]


def VH_exploration(API_client, key_obj_id, to_explore_ids):
    all_num_token_in = 0
    all_num_token_out = 0
    llm_in = VH_prompt_exploration + f"Target object: {key_obj_id}\nObservations: {sorted(to_explore_ids)}\nOutput: "
    llm_out = ""
    call_time = 0
    tried = set()
    while llm_out not in to_explore_ids:
        llm_out, num_token_in, num_token_out = call_api(API_client, llm_in, API_model_type="gpt-4o-mini")
        all_num_token_in += num_token_in
        all_num_token_out += num_token_out
        call_time += 1
        if call_time >= 10:
            print(key_obj_id, to_explore_ids)
            print("Failure to generate a valid output --- EXPLORATION")
            return random.choice(list(to_explore_ids)), [all_num_token_in, all_num_token_out, call_time]
        if llm_out is None:
            continue
        llm_out = llm_out.strip()
        tried.add(llm_out)
        
        
    return llm_out, [all_num_token_in, all_num_token_out, call_time]


def VH_filter(API_client, API_model, path, current_state, possible_actions_dict, goal_predicates, task_goal,):
    all_num_token_in = 0
    all_num_token_out = 0
    call_time = 0
    if len(possible_actions_dict.keys()) <= 1:
        return list(possible_actions_dict.keys()), [0, 0, 0]
    llm_in = VH_prompt_filter
    
    
    llm_in += "Goal: " + VH_AW_predicate_to_str(goal_predicates) + "\n"
    llm_in += "Current state: " + VH_state_to_str(current_state) + "\n"
    actions = list(possible_actions_dict.keys())
    action_strs = VH_actions_to_str(actions)
    llm_in += f"Candidate actions: {action_strs}\n"
     
    while True:
        llm_out, num_token_in, num_token_out = call_api(API_client, llm_in, API_model_type=API_model)
        all_num_token_in += num_token_in
        all_num_token_out += num_token_out
        call_time += 1
        if "Filtered actions:" in llm_out:
            break
    
    res = llm_out.strip().split('Filtered actions:')
    if len(res) < 2:
        return [], [all_num_token_in, all_num_token_out, call_time]
    res = res[1].split(', ')
    for i in range(len(res)):
        if res[i] not in possible_actions_dict:
            res[i] = process.extractOne(res[i], action_strs)[0]
    return [actions[action_strs.index(x)] for x in res], [all_num_token_in, all_num_token_out, call_time]


def VH_AW_predicate_to_str(goal_predicates):
    res = ""
    for predicate in goal_predicates:
        if len(predicate) == 2:
            res += f"{predicate[1]} is {predicate[0]}, "
    for predicate in goal_predicates:
        if len(predicate) == 3:
            res += f"{predicate[1]} is {predicate[0]} {predicate[2]}, "
    return res[:-2] + ". "

def VH_state_to_str(state): # TODO: sort?
    res = ""
    for node in state["nodes"]:
        obj_states = node["states"]
        if len(obj_states):
            res += f"{node['id']} is " 
            for s in obj_states:
                res += f"{s} and "
            res = res[:-5] + '. '
    for edge in state["edges"]:
        if edge["relation_type"] == "close_to" and edge["from_id"] != "agent-1":
            continue
        res += f"{edge['from_id']} is {edge['relation_type']} {edge['to_id']}. "
    return res

def VH_actions_to_str(actions):
    mapping = {
        "walk": "walk to", 
        "open": "open", 
        "close": "close",
        "wipe": "clean", 
        "switchon": "switch on", 
        "switchoff": "switch off",
        "plugin": "plug in", 
        "plugout": "plug out", 
        "grab": "grab",
        "sit": "sit on",
        "standup": "stand up"
    }
    strs = []
    for act in actions:
        if ' ' not in act:
            act_name = act[1:-1]
            strs.append(f"{act_name}")
        elif len(act.split(' ')) == 3:
            act_name, obj_cls, obj_id = act.split(' ')
            act_name = act_name[1:-1]
            obj_cls = obj_cls[1:-1]
            obj_id = obj_id[1:-1]
            strs.append(f"{mapping[act_name]} {obj_cls}-{obj_id}")
        elif len(act.split(' ')) == 5:
            act_name, obj_cls1, obj_id1, obj_cls2, obj_id2 = act.split(' ')
            act_name = act_name[1:-1]
            obj_cls1 = obj_cls1[1:-1]
            obj_id1 = obj_id1[1:-1]
            obj_cls2 = obj_cls2[1:-1]
            obj_id2 = obj_id2[1:-1]
            if act_name == "putback":
                strs.append(f"put {obj_cls1}-{obj_id1} on {obj_cls2}-{obj_id2}")
            elif act_name == "putin":
                strs.append(f"put {obj_cls1}-{obj_id1} inside {obj_cls2}-{obj_id2}")
            else:
                print(act)
                raise NotImplementedError
        else:
            print(act)
            raise NotImplementedError
    return strs
