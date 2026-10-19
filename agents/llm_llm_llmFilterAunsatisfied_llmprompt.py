import copy
import sys

from utils.graph_utils import get_action_str, GraphState, clean_graph_VH, state2obs_VH, check_progress_VH
from utils.llm_utils import VH_AW_translation, VH_exploration, VH_filter

from simulators.generated_VH_graph import *

from collections import deque
import heapq
import json

class llm_llm_llmFilterAunsatisfied_llmprompt:
    def __init__(self, api, env_name, filter_api_model, search_depth, translation_res):
        self.agent_type = 'llm_llm_llmFilterAunsatisfied_llmprompt'
        self.agent_graph = None
        self.api = api
        self.env_name = env_name
        self.filter_api_model = filter_api_model
        self.search_depth = search_depth

    def get_full_plan(self, task_goal, goal_predicates, key_obj_ids, tool_obj_ids):
        graph = self.agent_graph
        id2node = {node['id']: node for node in graph['nodes']}
        assert tool_obj_ids == []
        reduced_graph = clean_graph_VH(graph, key_obj_ids)
        
        # ensure the exploration result is enough
        check_ids = [x["id"] for x in reduced_graph["nodes"]]
        for predicate in goal_predicates:
            for x in predicate[1:]:
                assert x in check_ids or x == "agent-1", [goal_predicates, check_ids]

        ret, full_plan, num_search, api_log = self.search(task_goal, reduced_graph, goal_predicates, tool_obj_ids, id2node)
        print(full_plan)
        return ret, full_plan, num_search, api_log

    def search(self, task_goal, cur_state, goal_predicates, tool_obj_ids, id2node):
        total_api_log = [0, 0, 0, 0]
        all_nodes = cur_state["nodes"]
        
        action_classes = [
            ["walk_A", 1], 
            ["walk_room_A", 1], # separate "walk" and "walk_room", for easier simulator construction
            ["open_A", 1], 
            ["close_A", 1],
            ["wipe_A", 1],
            ["switch_on_A", 1], 
            ["switch_off_A", 1],
            ["plug_in_A", 1], 
            ["plug_out_A", 1], 
            ["grab_A", 1],
            ["put_A_on_B", 2],
            ["put_A_in_B", 2],
            ["sit_on_A", 1],
            ["stand_up", 0]
        ]
        
        frontier = []
        heapq.heappush(frontier, (3 * len(goal_predicates), 0, id(cur_state), []))
        explored = set()

        num_search = 0 
        num_search2 = 0 
        num_search3 = 0 
        
        state_map = {}
        state_map[id(cur_state)] = cur_state
        
        best_plan = None
        best_satisfied = -1
        
        while frontier:
            
            f, cost, current_state_id, path = heapq.heappop(frontier)
            
            current_state = state_map[current_state_id]
            satisfied_before = check_progress_VH(current_state, goal_predicates, )
            
            if len(satisfied_before) > best_satisfied:
                best_plan = copy.deepcopy(path)
                best_satisfied = len(satisfied_before)
            
            for_check_duplicate = GraphState(current_state)
            if for_check_duplicate in explored:
                continue
            explored.add(for_check_duplicate)
            
            num_search += 1
            if num_search > self.search_depth:
                print("REACH SEARCH LIMIT!!!!!")
                break
            
            # print(f, cost, path, "#####", satisfied_before, "#####", goal_predicates)
            # sys.stdout.flush()


            current_obs = state2obs_VH(current_state, self.room_ids)
            all_nodes = current_obs["nodes"]
            possible_actions = []

            for action in action_classes:
                action_class, num = action
                if num == 1:
                    for node in all_nodes:
                        objID = node["id"]
                        if objID == "agent-1":
                            continue
                        
                        if action_class == "walk_A" and objID in self.room_ids:
                            continue
                        if action_class == "walk_room_A" and objID not in self.room_ids:
                            continue
                        if action_class == "walk_A": # cannot walk to sth you hold
                            holding_flag = False
                            for edge in current_state["edges"]:
                                if edge["relation_type"] == "holding" and edge["to_id"] == objID:
                                    holding_flag = True
                                    break
                            if holding_flag:
                                continue
                        
                        num_search2 += 1
                        
                        if eval(f"{self.env_name}_"+action_class+"_precond")(current_obs, objID):
                            num_search3 += 1
                            new_state = copy.deepcopy(current_state)
                            new_state = eval(f"{self.env_name}_"+action_class+"_effect")(new_state, objID)
                            if self.env_name == "AW":
                                action_str = action_class.replace("switch_on", "use").replace("A", objID).replace('_', ' ')
                                new_path = path + [action_str]
                            elif self.env_name == "VH":
                                action_tuple = [
                                    action_class.replace("_A", "").replace("_B", "").replace("_", "").replace("puton", "put").replace("siton", "sit").replace("walkroom", "walk"), 
                                    self.split_objID(objID)]
                                new_path = path + [action_tuple]
                            elif self.env_name == "VH_graph":
                                action_tuple = [
                                    action_class.replace("_A", "").replace("_B", "").replace("_", "").replace("puton", "putback").replace("siton", "sit").replace("walkroom", "walk"), 
                                    self.split_objID(objID)]
                                new_path = path + [action_tuple]
                            new_cost = cost + 1
                            
                            for_check_duplicate = GraphState(new_state)
                            if for_check_duplicate in explored:
                                continue
                            
                            satisfied_after = check_progress_VH(new_state, goal_predicates, )
                            if len(satisfied_after) == len(goal_predicates):
                                return 0, new_path, [num_search, num_search2, num_search3], total_api_log
                            h = (len(goal_predicates) - len(satisfied_after)) * 3
                            possible_actions.append([action_class, [objID], new_state, new_cost, h, new_path])          
                elif num == 2:
                    for node1 in all_nodes:
                        objID1 = node1["id"]
                        if objID1 == "agent-1":
                            continue
                        for node2 in all_nodes:
                            objID2 = node2["id"]
                            if objID2 == "agent-1":
                                continue
                            if objID2 == objID1:
                                continue
                            num_search2 += 1

                            if eval(f"{self.env_name}_"+action_class+"_precond")(current_state, objID1, objID2):
                                num_search3 += 1
                                new_state = copy.deepcopy(current_state)
                                new_state = eval(f"{self.env_name}_"+action_class+"_effect")(new_state, objID1, objID2)
                                action_tuple = [
                                    action_class.replace("_A", "").replace("_B", "").replace("_", "").replace("puton", "putback").replace("siton", "sit").replace("walkroom", "walk"), 
                                    self.split_objID(objID1), self.split_objID(objID2)]
                                new_path = path + [action_tuple]
                                new_cost = cost + 1
                                
                                for_check_duplicate = GraphState(new_state)
                                if for_check_duplicate in explored:
                                    continue
                                
                                satisfied_after = check_progress_VH(new_state, goal_predicates, )
                                if len(satisfied_after) == len(goal_predicates):
                                    return 0, new_path, [num_search, num_search2, num_search3], total_api_log
                                h = (len(goal_predicates) - len(satisfied_after)) * 3
                                possible_actions.append([action_class, [objID1, objID2], new_state, new_cost, h, new_path])
                elif num == 0:
                    num_search2 += 1
                    if eval(f"{self.env_name}_"+action_class+"_precond")(current_obs, ):
                        num_search3 += 1
                        new_state = copy.deepcopy(current_state)
                        new_state = eval(f"{self.env_name}_"+action_class+"_effect")(new_state, )
                        if self.env_name == "AW":
                            action_str = action_class.replace("switch_on", "use").replace('_', ' ')
                            new_path = path + [action_str]
                        elif self.env_name == "VH":
                            action_tuple = [
                                action_class.replace("_A", "").replace("_B", "").replace("_", "").replace("puton", "put").replace("siton", "sit").replace("walkroom", "walk"), ]
                            new_path = path + [action_tuple]
                        elif self.env_name == "VH_graph":
                            action_tuple = [
                                action_class.replace("_A", "").replace("_B", "").replace("_", "").replace("puton", "putback").replace("siton", "sit").replace("walkroom", "walk"), ]
                            new_path = path + [action_tuple]
                        new_cost = cost + 1
                        
                        for_check_duplicate = GraphState(new_state)
                        if for_check_duplicate in explored:
                            continue
                        
                        satisfied_after = check_progress_VH(new_state, goal_predicates, )
                        if len(satisfied_after) == len(goal_predicates):
                            return 0, new_path, [num_search, num_search2, num_search3], total_api_log
                        h = (len(goal_predicates) - len(satisfied_after)) * 3
                        possible_actions.append([action_class, [], new_state, new_cost, h, new_path])
                else:
                    raise NotImplementedError

            if len(possible_actions) == 0:
                continue
            possible_actions_dict = {}
            for action_class, args, new_state, new_cost, h, new_path in possible_actions:
                action = new_path[-1]
                action = get_action_str(action)
                possible_actions_dict[action] = (action_class, args, new_state, new_cost, h, new_path)
            filtered_actions, api_log = VH_filter(self.api, self.filter_api_model, path, current_state, possible_actions_dict, goal_predicates, task_goal)
            
            total_api_log[0] += 1
            total_api_log[1] += api_log[0]
            total_api_log[2] += api_log[1]
            total_api_log[3] += api_log[2]
            
            for action in filtered_actions:
                action_class, args, new_state, new_cost, h, new_path = possible_actions_dict[action]
                heapq.heappush(frontier, (new_cost + h, new_cost, id(new_state), new_path))
                state_map[id(new_state)] = new_state
        print("NO SOLUTION FOUND!!!!!")
        return 1, best_plan, [num_search, num_search2, num_search3], total_api_log  # No solution found --- return the best satisfied

    def split_objID(self, objID):
        obj_id = int(objID.split('-')[-1])
        obj_class = '-'.join(objID.split('-')[:-1])
        return [obj_class, obj_id]
    
    
    def VH_finish_explore_checker(self, key_obj_ids, explored_ids):
        for oid in sorted(key_obj_ids):
            if oid not in explored_ids:
                return False, oid
        return True, None
    
    def explore_one_step(self, key_obj_ids, to_explore_ids_or_classes): 
        id2node = {node['id']: node for node in self.agent_graph['nodes']}
        s, key_obj_class = self.VH_finish_explore_checker(key_obj_ids, set(id2node.keys()))
        
        if s:
            return True, None, [0, 0, 0]
        to_explore_ids = to_explore_ids_or_classes
        exp_obj_id, api_log = VH_exploration(self.api, key_obj_class, to_explore_ids)
        return False, exp_obj_id, api_log
    
    def translate(self, task_goal, task_id):
        _predicates, api_log = VH_AW_translation(self.api, task_goal, self.env_name)
        predicates = []
        for elements in _predicates:
            # delete unrealistic predicates
            if elements[0] in ["holding", "sitting_on", "looking_at"]:
                if not elements[1] == "agent-1":
                    continue
            predicates.append(elements)

        key_objs = []
        for predicate in predicates:
            for obj in predicate[1:]:
                if 'agent' not in obj:
                    key_objs.append(obj)
    
        return predicates, key_objs, api_log
