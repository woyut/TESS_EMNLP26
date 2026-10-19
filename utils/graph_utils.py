from collections import defaultdict

def clean_graph_VH(state, key_obj_ids):
    new_graph = {}
    remain_ids = set()
    to_check = key_obj_ids + ["agent-1",]
    
    id2node = {node['id']: node for node in state['nodes']}
    inside = {} 
    for edge in state['edges']:
        if edge['relation_type'] == 'inside':
            if edge['from_id'] not in inside.keys():
                inside[edge['from_id']] = []
            inside[edge['from_id']].append(edge['to_id'])
    
    while (len(to_check) > 0):
        new_to_check = []
        for node in to_check:
            remain_ids.add(node)
            if node in inside:
                new_to_check += [x for x in inside[node] if x not in remain_ids]
        to_check = list(set(new_to_check))
    new_graph = {
            "edges": [edge for edge in state['edges'] if edge['from_id'] in set(remain_ids) and edge['to_id'] in set(remain_ids)],
            "nodes": [id2node[id_node] for id_node in set(remain_ids)]
    }

    return new_graph

def state2obs_VH(state_graph, room_ids):
    id2node = {node['id']: node for node in state_graph['nodes']}
    
    child_to_parents = defaultdict(set)
    grabbed_ids = []
    for edge in state_graph['edges']:
        if edge['relation_type'] == 'inside':
            child_to_parents[edge['from_id']].add(edge['to_id'])
        elif edge['relation_type'] == 'holding':
            assert edge['from_id'] == "agent-1"
            grabbed_ids.append(edge['to_id'])

    for edge in state_graph['edges']:
        if edge['relation_type'] == 'inside' and edge["from_id"] == "agent-1":
            assert edge["to_id"] in room_ids, [edge, room_ids]
            room_id = edge["to_id"]

    
    # We'll use memoization to avoid redundant computations
    memo = {}
    def get_all_parents(node):
        visited = set()
        def inner_get_all_parents(current_node):
            if current_node in memo:
                return memo[current_node]
            parents = set(child_to_parents.get(current_node, set()))
            all_parents = set(parents)
            for parent in parents:
                if parent not in visited:
                    visited.add(parent)
                    all_parents.update(inner_get_all_parents(parent))
            memo[current_node] = all_parents
            return all_parents
        return inner_get_all_parents(node)
    
    object_in_room_ids = []
    for node in state_graph["nodes"]:
        all_parents = get_all_parents(node["id"])
        if room_id in all_parents:
            flag = True
            for x in all_parents:
                if "CLOSED" in id2node[x]["states"]:
                    flag = False
                    break
            if flag:
                object_in_room_ids.append(node["id"])
    
    observable_object_ids = object_in_room_ids + room_ids + grabbed_ids
    obs_graph = {
        "nodes": [x for x in state_graph["nodes"] if x["id"] in observable_object_ids],
        "edges": [x for x in state_graph["edges"] if x["from_id"] in observable_object_ids and x["to_id"] in observable_object_ids]
    }
    return obs_graph

def get_action_str(action_tuple):
    if len(action_tuple) == 1:
        return '[{}]'.format(action_tuple[0])
    obj_args = [x for x in list(action_tuple)[1:] if x is not None]
    objects_str = ' '.join(['<{}> ({})'.format(x[0], x[1]) for x in obj_args])
    return '[{}] {}'.format(action_tuple[0], objects_str)


def check_progress_VH(state, predicates, ):
    satisfied = []
    id2node = {node['id']: node for node in state['nodes']}
    for predicate in predicates:
        elements = predicate
        if elements[0] in ["on", "inside", "close_to"]:
            for edge in state['edges']:
                if edge['relation_type'].lower() == elements[0] and edge['to_id'] == elements[2] and edge['from_id'] == elements[1]:
                    satisfied.append(predicate)
                    break
        elif elements[0] in ["holding", "sitting_on", "looking_at"]:
            assert elements[1] == "agent-1"
            for edge in state['edges']:
                if edge['relation_type'].lower() == elements[0] and edge['from_id'] == "agent-1" and edge['to_id'] == elements[2]:
                    satisfied.append(predicate)
                    break
        elif elements[0] == 'SWITCHON':
            if 'SWITCHON' in id2node[elements[1]]['states']:
                satisfied.append(predicate)
        elif elements[0] == 'SWITCHOFF':
            if 'SWITCHOFF' in id2node[elements[1]]['states']:
                satisfied.append(predicate)
        elif elements[0] == 'PLUGGED_IN':
            if 'PLUGGED_IN' in id2node[elements[1]]['states']:
                satisfied.append(predicate)
        elif elements[0] == 'PLUGGED_OUT':
            if 'PLUGGED_OUT' in id2node[elements[1]]['states']:
                satisfied.append(predicate)
        elif elements[0] == 'CLEAN':
            if 'CLEAN' in id2node[elements[1]]['states']:
                satisfied.append(predicate)
        elif elements[0] == 'OPEN':
            if 'OPEN' in id2node[elements[1]]['states']:
                satisfied.append(predicate)
        elif elements[0] == 'CLOSED':
            if 'CLOSED' in id2node[elements[1]]['states']:
                satisfied.append(predicate)
        else:
            print("!!!!!!!!!!!PREDICATE", elements)
            raise NotImplementedError
    return satisfied

def check_progress_VH_for_eval(state, predicates, ):
    satisfied = []
    id2node = {node['id']: node for node in state['nodes']}
    for predicate in predicates:
        elements = predicate.split('_')
        if elements[0] == "on" or elements[0] == "inside":
            for edge in state['edges']:
                if edge['relation_type'].lower() == elements[0] and edge['to_id'] == int(elements[2]) and edge['from_id'] == int(elements[1]):
                    satisfied.append(predicate)
                    break
        elif elements[0] == "closeto":
            for edge in state['edges']:
                if edge['relation_type'].lower().startswith('close') and edge['to_id'] == int(elements[1]) and edge['from_id'] == int(elements[2]):
                    satisfied.append(predicate)
                    break
        elif elements[0] == "hold":
            assert elements[1] == "1"
            for edge in state['edges']:
                if edge['relation_type'].lower().startswith('holds') and edge['from_id'] == 1 and edge['to_id'] == int(elements[2]):
                    satisfied.append(predicate)
                    break
        elif elements[0] == "sit":
            assert elements[1] == "1"
            sit = False
            on = False
            for edge in state['edges']:
                if edge['relation_type'].lower() == "on" and edge['from_id'] == 1 and edge['to_id'] == int(elements[2]):
                    on = True
                    break
            for node in state['nodes']:
                if node['id'] == 1:
                    if 'SITTING' in node['states']:
                        sit = True
                        break
            if sit and on:
                satisfied.append(predicate)
        elif elements[0] == "facing":
            assert elements[1] == "1"
            for edge in state['edges']:
                if edge['relation_type'].lower().startswith('facing') and edge['from_id'] == 1 and edge['to_id'] == int(elements[2]):
                    satisfied.append(predicate)
                    break
        elif elements[0] == 'switchon':
            if 'ON' in id2node[int(elements[1])]['states']:
                satisfied.append(predicate)
        elif elements[0] == 'plugin':
            if 'PLUGGED_IN' in id2node[int(elements[1])]['states']:
                satisfied.append(predicate)
        elif elements[0] == 'switchoff':
            if 'OFF' in id2node[int(elements[1])]['states']:
                satisfied.append(predicate)
        elif elements[0] == 'plugout':
            if 'PLUGGED_OUT' in id2node[int(elements[1])]['states']:
                satisfied.append(predicate)
        elif elements[0] == 'clean':
            if 'CLEAN' in id2node[int(elements[1])]['states']:
                satisfied.append(predicate)
        elif elements[0] == 'open':
            if 'OPEN' in id2node[int(elements[1])]['states']:
                satisfied.append(predicate)
        elif elements[0] == 'closed':
            if 'CLOSED' in id2node[int(elements[1])]['states']:
                satisfied.append(predicate)
        else:
            print("!!!!!!!!!!!PREDICATE", elements)
            raise NotImplementedError
    return satisfied


VH2Sim_state_mapper = {
    "OPEN": "OPEN",
    "CLOSED": "CLOSED",
    "ON": "SWITCHON",
    "OFF": "SWITCHOFF",
    "STANDING": "STANDING",
    "PLUGGED_IN": "PLUGGED_IN",
    "PLUGGED_OUT": "PLUGGED_OUT",
    "CLEAN": "CLEAN",
    "DIRTY": "DIRTY",

    "GRABBABLE": "HOLDABLE",
    "SITTABLE": "SITTABLE",
    "HAS_PLUG": "HAS_PLUG",
    "HAS_SWITCH": "HAS_SWITCH",
    "CAN_OPEN": "CAN_OPEN",

    "SITTING": "SITTING", 
}
VH2Sim_relation_mapper = {
    "ON": "on",
    "INSIDE": "inside",
    "CLOSE": "close_to",
    "SITTING": "sitting_on",
    "HOLDS_LH": "holding",
    "HOLDS_RH": "holding",

}
def VHGraph2SimGraph(graph):
    sim_graph = {
        "nodes": [],
        "edges": [],
    }
    id2simid = {}
    for node in graph["nodes"]:
        sim_node = {
            "id": node["class_name"] + '-' + str(node["id"]),
            "class_name": node["class_name"],
            "states": [VH2Sim_state_mapper[x] for x in node["states"]] + [VH2Sim_state_mapper[x] for x in node["properties"] if x in VH2Sim_state_mapper]
        }
        if node["class_name"] == "character":
            assert node["id"] == 1
            sim_node["id"] = "agent-1"
            sim_node["class_name"] = "agent"
        elif "CLEAN" not in sim_node["states"]:
            sim_node["states"].append("DIRTY")
        id2simid[node["id"]] = sim_node["id"]
        sim_graph["nodes"].append(sim_node)
    for edge in graph["edges"]:
        if edge["relation_type"] not in VH2Sim_relation_mapper:
            continue
        sim_edge = {
            "from_id": id2simid[edge["from_id"]],
            "to_id": id2simid[edge["to_id"]],
            "relation_type": VH2Sim_relation_mapper[edge["relation_type"]]
        }
        sim_graph["edges"].append(sim_edge)
    return sim_graph


def update_VH_graph_nodes(A, B):
    a_dict = {item['id']: item for item in A}
    
    for item in B:
        a_dict[item['id']] = item
    
    return list(a_dict.values())
def update_VH_graph_edges(A, B, obs_ids, room_ids):
    new_edges = []
    for e in B:
        if e["from_id"] in obs_ids and e["to_id"] in obs_ids:
            new_edges.append(e)
        else:
            pass
    for e in A:
        if e["from_id"] not in obs_ids and e["to_id"] not in obs_ids:
            new_edges.append(e)
        elif e["from_id"] in obs_ids and e["to_id"] in obs_ids:
            continue
        else:
            if e["from_id"] == "agent-1" or e["to_id"] == "agent-1": 
                continue
            elif e["to_id"] in room_ids:
                new_edges.append(e)
            else:
                pass
    
    for e in B:
        if e["from_id"] == "agent-1" and e["relation_type"] == "inside":
            assert e["to_id"] in room_ids
            agent_room_id = e["to_id"]
    from_ids = set([x["from_id"] for x in new_edges])
    for nid in obs_ids:
        if nid not in from_ids and nid not in room_ids:
            new_edges.append({"from_id": nid, "to_id": agent_room_id, "relation_type": "inside"})
    
    return new_edges 


def make_hashable(obj):
    """
    Recursively convert a data structure into a hashable type.
    - dicts become frozensets of key-value pairs (with values processed recursively)
    - lists become tuples (with items processed recursively)
    - sets become frozensets (with items processed recursively)
    - other types are returned as-is.
    """
    if isinstance(obj, dict):
        return frozenset((k, make_hashable(v)) for k, v in obj.items())
    elif isinstance(obj, list):
        return tuple(make_hashable(x) for x in obj)
    elif isinstance(obj, set):
        return frozenset(make_hashable(x) for x in obj)
    else:
        return obj

class GraphState: # for hashing in search
    def __init__(self, graph):
        # nodes: dict mapping node id to attributes (e.g., {'obj_class': ..., 'obj_id': ..., 'state': ...})
        # edges: list of tuples (from_node, to_node, relationship)
        self.nodes = []
        # print(graph["nodes"])
        # print(graph["edges"])
        # print("****************")
        for d in graph["nodes"]:
            self.nodes.append(str(d["id"])+'#'.join(sorted(d["states"])))
        self.edges = graph["edges"]

    def __hash__(self): 
        # Use the recursive conversion function to get hashable representations.
        nodes_hashable = make_hashable(self.nodes)
        edges_hashable = make_hashable(self.edges)
        return hash((nodes_hashable, edges_hashable))

    def __eq__(self, other):
        if not isinstance(other, GraphState):
            return False
        return (make_hashable(self.nodes) == make_hashable(other.nodes)) and \
               (make_hashable(self.edges) == make_hashable(other.edges))
    
    def __getitem__(self, key):
        if key == "nodes":
            return self.nodes
        elif key == "edges":
            return self.edges
        else:
            raise KeyError(f"Invalid key: {key}")
