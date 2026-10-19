def VH_graph_open_A_precond(graph, A):
    # This is the precondition function for the action of "open A".
    # The action "open A" can only be performed if the object A is closed, and the agent is close to A. 
    # Therefore, I need to check: 1.whether A has the state "CLOSED"; 2.whether there is a relation of "close_to" between agent-1 and A.

    # First, I need to check the unary predicates on A, which means to check the state list of node A.
    A_is_closed = False
    # I will iterate over all the nodes in the graph, and find A by its id.
    for node in graph["nodes"]:
        if node["id"] == A:
            # I need to check whether A has the state "CLOSED"
            if "CLOSED" in node["states"]:
                A_is_closed = True
    
    # Then, I need to check the binary predicates on agent-1 and A, which means to check the edge list of the graph.
    agent_is_close_to_A = False
    for edge in graph["edges"]:
        if edge["from_id"] == "agent-1" and edge["to_id"] == A and edge["relation_type"] == "close_to":
            agent_is_close_to_A = True
    
    if A_is_closed and agent_is_close_to_A:
        return True
    else:
        return False

def VH_graph_open_A_effect(graph, A):

    # This is the effect function for the action of "open A".
    # The action "open A" will make A open. Also, A will no longer be closed.
    # Therefore, the things I need to do is remove the state "CLOSED" from A, and add the state "OPEN" to A.

    # First, I need to iterate over all the nodes in the graph, and find A by its id.
    for node in graph["nodes"]:
        if node["id"] == A:
            # Then, I need to remove the state "CLOSED" from A's state list, and add the state "OPEN" to it.
            if "CLOSED" in node["states"]:
                node["states"].remove("CLOSED")
            if "OPEN" not in node["states"]:
                node["states"].append("OPEN")
    return graph

def VH_graph_walk_A_precond(graph, A):
    # The agent can "walk to" A if it is not already close to A.
    # That is, there should be no "close_to" edge from agent-1 to A.
    for edge in graph["edges"]:
        if edge["from_id"] == "agent-1" and edge["to_id"] == A and edge["relation_type"] == "close_to":
            return False
    # Otherwise, the walk is allowed
    return True

def VH_graph_walk_A_effect(graph, A):
    # Add "close_to" edge from agent-1 to A; remove all other "close_to" edges (agent can only be close to one thing at a time)
    # Also, if A is inside a room, add "inside" edge from agent-1 to the same room.
    new_edges = [edge for edge in graph["edges"] if not (edge["from_id"] == "agent-1" and edge["relation_type"] == "close_to")]
    new_edges.append({"from_id": "agent-1", "to_id": A, "relation_type": "close_to"})
    
    
    graph["edges"] = new_edges
    return graph

def VH_graph_walk_room_A_precond(graph, A):
    # A must be a room (assume we can walk into any node that does not have the property HOLDABLE or SITTABLE)
    # Agent must not already be inside A.
    already_inside = False
    for edge in graph["edges"]:
        if edge["from_id"] == "agent-1" and edge["to_id"] == A and edge["relation_type"] == "inside":
            already_inside = True
            break
    if already_inside:
        return False
    return True

def VH_graph_walk_room_A_effect(graph, A):
    # Remove any existing "inside" edges from agent-1, add a new one to A.
    graph["edges"] = [edge for edge in graph["edges"] if not (edge["from_id"] == "agent-1" and edge["relation_type"] in ["inside", "close_to"])]
    graph["edges"].append({"from_id": "agent-1", "to_id": A, "relation_type": "inside"})
    return graph

def VH_graph_close_A_precond(graph, A):
    # Check A has "CAN_OPEN" and "OPEN"; agent is close to A
    has_can_open = False
    is_open = False
    for node in graph["nodes"]:
        if node["id"] == A:
            if "CAN_OPEN" in node["states"]:
                has_can_open = True
            if "OPEN" in node["states"]:
                is_open = True
    is_close = any(edge["from_id"] == "agent-1" and edge["to_id"] == A and edge["relation_type"] == "close_to" for edge in graph["edges"])
    return has_can_open and is_open and is_close

def VH_graph_close_A_effect(graph, A):
    # Remove "OPEN", add "CLOSED"
    for node in graph["nodes"]:
        if node["id"] == A:
            if "OPEN" in node["states"]:
                node["states"].remove("OPEN")
            if "CLOSED" not in node["states"]:
                node["states"].append("CLOSED")
    return graph

def VH_graph_sit_on_A_precond(graph, A):
    # Check A is SITTABLE; agent is close to A and not already sitting
    is_sittable = False
    for node in graph["nodes"]:
        if node["id"] == A and "SITTABLE" in node["states"]:
            is_sittable = True
            break
    close_to = any(edge["from_id"] == "agent-1" and edge["to_id"] == A and edge["relation_type"] == "close_to" for edge in graph["edges"])
    agent_is_sitting = False
    for node in graph["nodes"]:
        if node["id"] == "agent-1" and "SITTING" in node["states"]:
            agent_is_sitting = True
            break
    return is_sittable and close_to and not agent_is_sitting

def VH_graph_sit_on_A_effect(graph, A):
    # Add "SITTING" to agent-1, and edge "sitting_on"
    for node in graph["nodes"]:
        if node["id"] == "agent-1" and "SITTING" not in node["states"]:
            node["states"].append("SITTING")
    # Remove any existing "sitting_on" edge
    graph["edges"] = [edge for edge in graph["edges"] if not (edge["from_id"] == "agent-1" and edge["relation_type"] == "sitting_on")]
    graph["edges"].append({"from_id": "agent-1", "to_id": A, "relation_type": "sitting_on"})
    return graph

def VH_graph_stand_up_precond(graph):
    # Agent must be sitting
    for node in graph["nodes"]:
        if node["id"] == "agent-1" and "SITTING" in node["states"]:
            return True
    return False

def VH_graph_stand_up_effect(graph):
    # Remove "SITTING" state from agent-1, remove "sitting_on" edge if exists
    for node in graph["nodes"]:
        if node["id"] == "agent-1" and "SITTING" in node["states"]:
            node["states"].remove("SITTING")
    graph["edges"] = [edge for edge in graph["edges"] if not (edge["from_id"] == "agent-1" and edge["relation_type"] == "sitting_on")]
    return graph

def VH_graph_grab_A_precond(graph, A):
    # A must be HOLDABLE, agent must be close to A, and agent must have no more than 1 object already held
    a_holdable = False
    for node in graph["nodes"]:
        if node["id"] == A and "HOLDABLE" in node["states"]:
            a_holdable = True
            break
    agent_close = any(edge["from_id"] == "agent-1" and edge["to_id"] == A and edge["relation_type"] == "close_to" for edge in graph["edges"])
    # Count number of "holding" from agent-1
    count_holding = sum(1 for edge in graph["edges"] if edge["from_id"] == "agent-1" and edge["relation_type"] == "holding")
    return a_holdable and agent_close and count_holding < 2

def VH_graph_grab_A_effect(graph, A):
    # Add "holding" edge from agent-1 to A. Remove all "inside", "on", "close_to" edges to A (since agent now holds A)
    # Remove any existing "holding" edge to A first if somehow exists.
    graph["edges"] = [edge for edge in graph["edges"] if not ((edge["from_id"] == "agent-1" and edge["to_id"] == A and edge["relation_type"] == "holding")
                                                               or (edge["to_id"] == A and edge["relation_type"] in ("inside", "on", "close_to"))
                                                               or (edge["from_id"] == A and edge["relation_type"] in ("inside", "on", "close_to")))]
    graph["edges"].append({"from_id": "agent-1", "to_id": A, "relation_type": "holding"})
    return graph

def VH_graph_put_A_on_B_precond(graph, A, B):
    # Agent must be holding A, and be close to B (holding edge agent-1->A, close_to agent-1->B)
    agent_holding_A = any(edge["from_id"] == "agent-1" and edge["to_id"] == A and edge["relation_type"] == "holding" for edge in graph["edges"])
    agent_close_to_B = any(edge["from_id"] == "agent-1" and edge["to_id"] == B and edge["relation_type"] in ["close_to", "holding"] for edge in graph["edges"])
    return agent_holding_A and agent_close_to_B

def VH_graph_put_A_on_B_effect(graph, A, B):
    # Remove "holding" agent-1->A; Add "on" A->B
    graph["edges"] = [edge for edge in graph["edges"] if not (edge["from_id"] == "agent-1" and edge["to_id"] == A and edge["relation_type"] == "holding")]
    # Remove any previous "on" or "inside" edge from A, only one location at a time
    graph["edges"] = [edge for edge in graph["edges"] if not (edge["from_id"] == A and edge["relation_type"] in ["on", "inside"])]
    graph["edges"].append({"from_id": A, "to_id": B, "relation_type": "on"})
    return graph

def VH_graph_put_A_in_B_precond(graph, A, B):
    # Agent must be holding A; agent must be close to B; B must be "OPEN" (if it can be opened)
    agent_holding_A = any(edge["from_id"] == "agent-1" and edge["to_id"] == A and edge["relation_type"] == "holding" for edge in graph["edges"])
    agent_close_to_B = any(edge["from_id"] == "agent-1" and edge["to_id"] == B and edge["relation_type"] in ["close_to", "holding"] for edge in graph["edges"])
    # Check if B is open if B can be opened
    B_can_open = False
    B_is_open = False
    for node in graph["nodes"]:
        if node["id"] == B and "CAN_OPEN" in node["states"]:
            B_can_open = True
            if "OPEN" in node["states"]:
                B_is_open = True
    b_open_ok = not B_can_open or (B_can_open and B_is_open)
    return agent_holding_A and agent_close_to_B and b_open_ok

def VH_graph_put_A_in_B_effect(graph, A, B):
    # Remove "holding" agent-1->A; Remove any previous "on" or "inside" or "close_to" of A. Add "inside" A->B.
    graph["edges"] = [edge for edge in graph["edges"] if not (
        (edge["from_id"] == "agent-1" and edge["to_id"] == A and edge["relation_type"] == "holding") or
        (edge["from_id"] == A and edge["relation_type"] in ["on", "inside"]))]
    graph["edges"].append({"from_id": A, "to_id": B, "relation_type": "inside"})
    return graph

def VH_graph_switch_on_A_precond(graph, A):
    # A must have HAS_SWITCH and be SWITCHOFF; agent is close to A
    a_has_switch = False
    is_off = False
    for node in graph["nodes"]:
        if node["id"] == A:
            if "HAS_SWITCH" in node["states"]:
                a_has_switch = True
            if "SWITCHOFF" in node["states"]:
                is_off = True
    agent_close = any(edge["from_id"] == "agent-1" and edge["to_id"] == A and edge["relation_type"] == "close_to" for edge in graph["edges"])
    return a_has_switch and is_off and agent_close

def VH_graph_switch_on_A_effect(graph, A):
    # Remove "SWITCHOFF", add "SWITCHON"
    for node in graph["nodes"]:
        if node["id"] == A:
            if "SWITCHOFF" in node["states"]:
                node["states"].remove("SWITCHOFF")
            if "SWITCHON" not in node["states"]:
                node["states"].append("SWITCHON")
    return graph

def VH_graph_switch_off_A_precond(graph, A):
    # A must have HAS_SWITCH and be SWITCHON; agent is close to A
    a_has_switch = False
    is_on = False
    for node in graph["nodes"]:
        if node["id"] == A:
            if "HAS_SWITCH" in node["states"]:
                a_has_switch = True
            if "SWITCHON" in node["states"]:
                is_on = True
    agent_close = any(edge["from_id"] == "agent-1" and edge["to_id"] == A and edge["relation_type"] == "close_to" for edge in graph["edges"])
    return a_has_switch and is_on and agent_close

def VH_graph_switch_off_A_effect(graph, A):
    # Remove "SWITCHON", add "SWITCHOFF"
    for node in graph["nodes"]:
        if node["id"] == A:
            if "SWITCHON" in node["states"]:
                node["states"].remove("SWITCHON")
            if "SWITCHOFF" not in node["states"]:
                node["states"].append("SWITCHOFF")
    return graph

def VH_graph_plug_in_A_precond(graph, A):
    # A has HAS_PLUG and PLUGGED_OUT; agent is close to A
    a_has_plug = False
    is_out = False
    for node in graph["nodes"]:
        if node["id"] == A:
            if "HAS_PLUG" in node["states"]:
                a_has_plug = True
            if "PLUGGED_OUT" in node["states"]:
                is_out = True
    agent_close = any(edge["from_id"] == "agent-1" and edge["to_id"] == A and edge["relation_type"] == "close_to" for edge in graph["edges"])
    return a_has_plug and is_out and agent_close

def VH_graph_plug_in_A_effect(graph, A):
    for node in graph["nodes"]:
        if node["id"] == A:
            if "PLUGGED_OUT" in node["states"]:
                node["states"].remove("PLUGGED_OUT")
            if "PLUGGED_IN" not in node["states"]:
                node["states"].append("PLUGGED_IN")
    return graph

def VH_graph_plug_out_A_precond(graph, A):
    # A has HAS_PLUG and PLUGGED_IN; agent is close to A
    a_has_plug = False
    is_in = False
    for node in graph["nodes"]:
        if node["id"] == A:
            if "HAS_PLUG" in node["states"]:
                a_has_plug = True
            if "PLUGGED_IN" in node["states"]:
                is_in = True
    agent_close = any(edge["from_id"] == "agent-1" and edge["to_id"] == A and edge["relation_type"] == "close_to" for edge in graph["edges"])
    return a_has_plug and is_in and agent_close

def VH_graph_plug_out_A_effect(graph, A):
    for node in graph["nodes"]:
        if node["id"] == A:
            if "PLUGGED_IN" in node["states"]:
                node["states"].remove("PLUGGED_IN")
            if "PLUGGED_OUT" not in node["states"]:
                node["states"].append("PLUGGED_OUT")
    return graph

def VH_graph_wipe_A_precond(graph, A):
    # Agent must be holding A; A must be DIRTY
    agent_holding = any(edge["from_id"] == "agent-1" and edge["to_id"] == A and edge["relation_type"] == "holding" for edge in graph["edges"])
    is_dirty = False
    for node in graph["nodes"]:
        if node["id"] == A and "DIRTY" in node["states"]:
            is_dirty = True
            break
    return agent_holding and is_dirty

def VH_graph_wipe_A_effect(graph, A):
    for node in graph["nodes"]:
        if node["id"] == A and "DIRTY" in node["states"]:
            node["states"].remove("DIRTY")
            if "CLEAN" not in node["states"]:
                node["states"].append("CLEAN")
    return graph
