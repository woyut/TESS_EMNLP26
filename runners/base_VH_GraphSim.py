import random
import copy

from utils.graph_utils import update_VH_graph_nodes, update_VH_graph_edges, get_action_str, VHGraph2SimGraph, check_progress_VH_for_eval
import VH_envs.evolving_graph.utils as VH_EG_utils
from VH_envs.evolving_graph.scripts import read_script_from_list_string
from VH_envs.evolving_graph.execution import ScriptExecutor
from VH_envs.evolving_graph.environment import EnvironmentGraph, EnvironmentState

def update_api_log(total, new):
    total[0] += 1
    total[1] += new[0]
    total[2] += new[1]
    total[3] += new[2]
    return total


class BaseRunner_VH_GraphSim(object):
    def __init__(self, agent, ):
        self.agent = agent
        self.name_equivalence = VH_EG_utils.load_name_equivalence()

    def make_full_plan(self, goal_predicates, key_obj_ids):
        ret, plan, num_search, api_log = self.agent.get_full_plan(self.task_goal, goal_predicates, key_obj_ids, tool_obj_ids=[])
        print("PLAN:", plan)
        return ret, plan, num_search, api_log

    def step(self, action_tuple, ):
        action_str = get_action_str(action_tuple)
        try:
            s, self.state = self.executor.execute_one_step(read_script_from_list_string([action_str,]), self.state)
        except Exception as e:
            print("Error!!!", e, action_str)
            s = False
        obs = VH_EG_utils.get_visible_nodes(self.state.to_dict(), agent_id=1)
        error_msg = self.executor.info.get_error_string()
        return obs, action_str, (s, error_msg)
    
    def run(self, task_instance, task_id):
        self.executor = ScriptExecutor(EnvironmentGraph(task_instance["init_graph"]), self.name_equivalence)
        self.state = EnvironmentState(EnvironmentGraph(task_instance["init_graph"]), self.name_equivalence, instance_selection=True)
        self.init_obs = VH_EG_utils.get_visible_nodes(task_instance["init_graph"], agent_id=1)
        
        self.task_goal = copy.deepcopy(task_instance["task_goal"])
        self.agent.task_goal = self.task_goal
        print(">>>>>>>", self.task_goal)
        goal_predicates, key_obj_ids, translation_api_log = self.agent.translate(self.task_goal["grounded_task_name"], task_id)
        print("<<<<<<<", goal_predicates)
        
        saved_info = {'task_id': task_id,
                      'env_id': task_instance["env_id"],
                      'task_name': task_instance["task_name"],
                      'task_goal': self.task_goal,
                      'translated_key_objs': key_obj_ids,
                      'translated_predicates': goal_predicates,
                      'action': [],
                      'action_type': [],
                      'finished': None,
                    #   'init_full_unity_graph': task_instance["init_graph"], # too big
                      'goals_finished': [],
                      'translation_api_log': translation_api_log,} 
        total_step = 0
        
        if goal_predicates is None:
            return [False, 0], total_step, saved_info

        self.agent.agent_graph = VHGraph2SimGraph(self.init_obs)
        self.agent.room_ids = []

        to_explore_ids = set() 
        agg_obs_obj_ids_by_room = {} 
        for node in self.init_obs["nodes"]:
            if node["category"] == "Rooms":
                agg_obs_obj_ids_by_room[node["class_name"]+'-'+str(node["id"])] = set()
                self.agent.room_ids.append(node["class_name"]+'-'+str(node["id"]))
                to_explore_ids.add(node["class_name"]+'-'+str(node["id"]))
        id2class = {x["id"]: x["class_name"] for x in self.init_obs["nodes"]}
        for edge in self.init_obs["edges"]:
            if edge["from_id"] == 1 and edge["relation_type"] == "INSIDE":
                init_room = id2class[edge["to_id"]]
                init_room_id = init_room + '-' + str(edge["to_id"])
                assert init_room_id in self.agent.room_ids
                to_explore_ids.remove(init_room_id)
        for node in self.init_obs["nodes"]:
            if not node["category"] == "Rooms" and not node["class_name"] == "agent" and "CLOSED" in node["states"] and "CAN_OPEN" in node["properties"]: 
                to_explore_ids.add(node["class_name"]+'-'+str(node["id"]))
                agg_obs_obj_ids_by_room[init_room_id].add(node["class_name"]+'-'+str(node["id"]))
        

        cur_room_id = init_room_id
        explore_obj_id = None
        explored_ids = []
        opened_ids = []
        
        explore_api_log = [0, 0, 0, 0]
        while True:
            finish_exploration, explore_obj_id, explore_step_api_log = self.agent.explore_one_step(key_obj_ids, to_explore_ids)
            explore_api_log = update_api_log(explore_api_log, explore_step_api_log)
            
            if finish_exploration:
                break
            explored_ids.append(explore_obj_id)
            
            for room_id in agg_obs_obj_ids_by_room:
                if explore_obj_id == room_id or explore_obj_id in agg_obs_obj_ids_by_room[room_id]:
                    explore_room_id = room_id
            
            if explore_room_id == cur_room_id:
                obj_cls = '-'.join(explore_obj_id.split('-')[:-1])
                action_tuple = ["walk", [obj_cls, explore_obj_id.split('-')[-1]]]
                obs, action_str, _ = self.step(action_tuple)
                total_step += 1
                saved_info['action'].append(action_str)
                saved_info['action_type'].append('EXP')
                action_tuple = ["open", list(explore_obj_id.split('-'))]
                obs, action_str, _ = self.step(action_tuple)
                total_step += 1
                saved_info['action'].append(action_str)
                saved_info['action_type'].append('EXP')
                opened_ids.append(explore_obj_id)
            elif explore_obj_id in agg_obs_obj_ids_by_room:
                action_tuple = ["walk", list(explore_obj_id.split('-'))]
                obs, action_str, _ = self.step(action_tuple)
                total_step += 1
                saved_info['action'].append(action_str)
                saved_info['action_type'].append('EXP')
            else:
                action_tuple = ["walk", list(explore_room_id.split('-'))]
                obs, action_str, _ = self.step(action_tuple)
                total_step += 1
                saved_info['action'].append(action_str)
                saved_info['action_type'].append('EXP')
                action_tuple = ["walk", list(explore_obj_id.split('-'))]
                obs, action_str, _ = self.step(action_tuple)
                total_step += 1
                saved_info['action'].append(action_str)
                saved_info['action_type'].append('EXP')
                action_tuple = ["open", list(explore_obj_id.split('-'))]
                obs, action_str, _ = self.step(action_tuple)
                total_step += 1
                saved_info['action'].append(action_str)
                saved_info['action_type'].append('EXP')
                opened_ids.append(explore_obj_id)
            
            sim_obs = VHGraph2SimGraph(obs)
            
            self.agent.agent_graph["nodes"] = update_VH_graph_nodes(self.agent.agent_graph["nodes"], sim_obs["nodes"])
            self.agent.agent_graph["edges"] = update_VH_graph_edges(self.agent.agent_graph["edges"], sim_obs["edges"], [x["id"] for x in sim_obs["nodes"]], self.agent.room_ids)
            cur_room_id = explore_room_id
            for edge in self.agent.agent_graph["edges"]:
                if edge["from_id"] == "agent-1" and edge["relation_type"] == "in":
                    assert edge["to_id"] == cur_room_id
            for node in obs["nodes"]:
                if not node["category"] == "Rooms" and not node["class_name"] == "agent" and "CLOSED" in node["states"] and "CAN_OPEN" in node["properties"]:
                    agg_obs_obj_ids_by_room[cur_room_id].add(node["class_name"]+'-'+str(node["id"]))
                    to_explore_ids.add(node["class_name"]+'-'+str(node["id"]))
            for x in explored_ids:
                if x in to_explore_ids:
                    to_explore_ids.remove(x)
        
        print("EXPLORATION ACTIONS:", saved_info['action']) 
        print("FINISHED EXPLORATION:", total_step)
        saved_info["exploration_api_log"] = explore_api_log
        
        saved_info["explored_graph"] = self.agent.agent_graph
        saved_info["explored_ids"] = explored_ids

        ret, self.generated_plan, num_search, search_api_log = self.make_full_plan(goal_predicates, key_obj_ids) # mental search
        saved_info["search_api_log"] = search_api_log
        saved_info["generated_plan"] = self.generated_plan
        saved_info["num_search"] = num_search
        if ret:
            saved_info["search_success"] = False
        else:
            saved_info["search_success"] = True
        
        if self.generated_plan is None:
            saved_info["finished"] = False
            saved_info["failed_reason"] = "Failed in searching"
            saved_info["sr"] = 0
            saved_info["gcr"] = 0
            saved_info["steps"] = total_step
            return [False, 0], total_step, saved_info
        
        # execution
        for action_tuple in self.generated_plan:
            obs, action_str, (step_success, step_error_msg) = self.step(action_tuple)
            total_step += 1
            saved_info['action'].append(action_str)
            if not step_success:
                print("         Failed step:", action_str, step_error_msg)
        
        satisfied = check_progress_VH_for_eval(self.state.to_dict(), self.task_goal["predicates"]) # use gt predicate for evaluation
        success = (len(satisfied) == len(self.task_goal["predicates"]))
        gcr = (len(satisfied) / len(self.task_goal["predicates"]))

        saved_info['finished'] = success
        if not success:
            saved_info["failed_reason"] = "Bad plan"
        saved_info["sr"] = success
        saved_info["gcr"] = gcr
        saved_info["steps"] = total_step
        return [success, gcr], total_step, saved_info
    