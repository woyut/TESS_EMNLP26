VH_graph_prompt_translation = """
Suppose you are a helpful agent that can perform actions in a household environment. Upon receiving a task expressed in natural language, I want you to formulate it into a list of facts that should be accomplished at the end of the task execution. 
There are two types of facts: (1) unary fact that descibes a state that an object should possess; (2) binary fact that describes a relation between two objects.
The possible states include: [OPEN, CLOSED, CLEAN, DIRTY, SWITCHON, SWITCHOFF, PLUGGED_IN, PLUGGED_OUT]
The possible relations include: [on, inside, close_to, holding, sitting_on]
You should output exactly a list of facts without other description or explanation. Each item in the list should be a tuple of the form (state, object-id) for unary fact, or a tuple of the form (relation, object1-id1, object2-id2) for binary fact.
Note that the state and relation should come from the lists I provided above. You should focus on the final state of the environment when extracting facts, instead of the process of the actions.
The state of [OPEN, CLOSED, CLEAN, DIRTY, SWITCHON, SWITCHOFF, PLUGGED_IN, PLUGGED_OUT] can only be applied to objects. The relation of [holding, sitting_on, close_to] can only be between the agent (whose id is "agent-1") and an object. 


Here are some examples.
Task: Could you take plate-245 and plate-143, clean them up, and put them on coffeetable-215 for me?
Facts: [(on, plate-245, coffeetable-215), (on, plate-143, coffeetable-215), (CLEAN, plate-245), (CLEAN, plate-143)]

Task: Kindly put chicken-241, food_turkey-479, food_salt-449 inside microwave-234. Next, please turn microwave-234 on and check if it works.
Facts: [(inside, chicken-241, microwave-234), (inside, food_turkey-479, microwave-234), (inside, food_salt-449, microwave-234), (SWITCHON, microwave-234)]

Task: Make sure you are currently holding paper-474.
Facts: [(holding, agent-1, paper-474)]

Task: Stack the two objects, food_kiwi-638 and food_kiwi-637, on cutting_board-636, and then insert cutting_board-636 into dishwasher-151.
Facts: [(inside, cutting_board-636, dishwasher-151), (on, food_kiwi-638, cutting_board-636), (on, food_kiwi-637, cutting_board-636), ]

Task: Head over to basket_for_clothes-451.
Facts: [(close_to, agent-1, basket_for_clothes-451)]

Now comes the query.
Task: """


VH_prompt_exploration = """
Suppose you are a helpful agent in a household environment. I want you to help me find some object. I will give you a target object and a list of observed rooms and objects. The target object is usually hidden in a closed container or storage furniture. You need to choose a room or object in the given list to explore, which should be some place that the target object is likely to be located in. 
Note that your output should be chosen from the given list. Please output directly the room or object that you choose (in the form of \"classname-id\"). Do not output any other information.
Hint: for big objects, you should usually choose a room to explore; while for small objects, you may choose a container that may have it inside.
"""


VH_prompt_filter = """
Suppose you are a agent performing household actions in a house. I will give you (1) a task and its goal that you need to achieve with a series of atomic actions, (2) the current state of the environment; (3) a set of candidate actions that you can do currently.
I want you to filter the candidate actions by reserving the actions that may be helpful for completing the task from current state and removing the actions that seem useless.

Here are some examples.
(1) 
Goal: blender-571 is SWITCHON, blow_dryer-583 is SWITCHON, blow_dryer-584 is SWITCHON, blender-571 is on table-581, blow_dryer-583 is on table-581, blow_dryer-584 is on table-581. 
Current state: kitchen-115 is DIRTY. bookshelf-228 is DIRTY. closet-49 is OPEN and CAN_OPEN and DIRTY. blender-571 is PLUGGED_IN and CLOSED and CAN_OPEN and HAS_PLUG and HAS_SWITCH and HOLDABLE and DIRTY and SWITCHON. table-581 is DIRTY. livingroom-11 is DIRTY. blow_dryer-583 is SWITCHON and PLUGGED_OUT and HAS_PLUG and HAS_SWITCH and HOLDABLE and DIRTY. folder-199 is OPEN and CAN_OPEN and HOLDABLE and DIRTY. blow_dryer-584 is SWITCHON and PLUGGED_OUT and HAS_PLUG and HAS_SWITCH and HOLDABLE and DIRTY. agent-1 is close_to bookshelf-228. agent-1 is close_to blender-571. table-581 is inside kitchen-115. folder-199 is inside kitchen-115. folder-199 is inside bookshelf-228. agent-1 is inside kitchen-115. blender-571 is inside kitchen-115. bookshelf-228 is inside kitchen-115. closet-49 is inside livingroom-11. blow_dryer-584 is inside livingroom-11. blow_dryer-584 is on closet-49. blow_dryer-583 is inside closet-49. blow_dryer-583 is inside livingroom-11. agent-1 is holding folder-199. 
Candidate actions: ['walk to table-581', 'walk to livingroom-11', 'open blender-571', 'clean folder-199', 'switch off blender-571', 'plug out blender-571', 'grab blender-571', 'put folder-199 on bookshelf-228', 'put folder-199 on blender-571', 'put folder-199 inside bookshelf-228']
Analysis: The goal is to switch on blender-571, blow_dryer-583, blow_dryer-584, and put them all on table-581. Currently, blender-571, blow_dryer-583, blow_dryer-584 are all switched on, so I just need to move them to the table. I am now holding folder-199, which is unrelated to the goal. I should put it back to somewhere. I am also close to blender-571, so another proper next step should be grabbing blender-571, so that I can take it to table-581.
Filtered actions: put folder-199 on bookshelf-228, put folder-199 on blender-571, put folder-199 inside bookshelf-228, grab blender-571

(2)
Goal: tape-524 is inside folder-216, address_book-543 is inside folder-216, address_book-541 is inside folder-216, folder-216 is on desk-275. 
Current state: kitchen-158 is DIRTY. address_book-541 is OPEN and CAN_OPEN and HOLDABLE and DIRTY. folder-334 is OPEN and CAN_OPEN and HOLDABLE and DIRTY. address_book-543 is OPEN and CAN_OPEN and HOLDABLE and DIRTY. desk-275 is OPEN and CAN_OPEN and DIRTY. tape-524 is HOLDABLE and DIRTY. livingroom-239 is DIRTY. folder-216 is OPEN and CAN_OPEN and HOLDABLE and DIRTY. desk-275 is inside livingroom-239. address_book-541 is inside desk-275. address_book-541 is inside livingroom-239. address_book-543 is inside livingroom-239. folder-334 is inside livingroom-239. folder-334 is on desk-275. folder-216 is inside kitchen-158. agent-1 is inside kitchen-158. agent-1 is close_to folder-216. tape-524 is inside folder-216. 
Candidate actions: ['walk to tape-524', 'walk to livingroom-239', 'close folder-216', 'grab folder-216']
Analysis: The goal is to put folder-216 on desk-275, then put tape-524, address_book-543, address_book-541 inside folder-216. Currently folder-216 is inside kitchen-158, so I should move it to desk-275. Since I am already close to it, a proper action is to grab it.
Filtered actions: grab folder-216

(3)
Goal: dishwasher-158 is SWITCHON, fork-490 is inside dishwasher-158, cutting_board-469 is inside dishwasher-158. 
Current state: bedroom-282 is DIRTY. dishwasher-158 is OPEN and CAN_OPEN and HAS_SWITCH and DIRTY and SWITCHON. kitchen-56 is DIRTY. fork-490 is HOLDABLE and DIRTY. cutting_board-469 is HOLDABLE and DIRTY. cabinet-316 is CAN_OPEN and DIRTY and CLOSED. cabinet-316 is inside bedroom-282. cutting_board-469 is inside bedroom-282. cutting_board-469 is inside cabinet-316. fork-490 is inside kitchen-56. fork-490 is inside dishwasher-158. dishwasher-158 is inside kitchen-56. agent-1 is inside kitchen-56. agent-1 is close_to dishwasher-158. 
Candidate actions: ['walk to fork-490', 'walk to bedroom-282', 'close dishwasher-158']
Analysis: The goal is to switch on dishwasher-158 and put fork-490 and cutting_board-469 inside it. Now dishwasher-158 is already switched on, and fork-490 is already in it, so I only need to move cutting_board-469 into dishwasher-158. cutting_board-469 is inside bedroom-282 while I am in inside kitchen-56, so I need to walk into bedroom-282 and then walk close to cutting_board-469. Thus, the only proper action at current time is to walk to bedroom-282.
Filtered actions: walk to bedroom-282

(4)
Goal: dough-510 is on kitchen_table-482, bowl-511 is on kitchen_table-482. 
Current state: kitchen_table-482 is DIRTY. kitchen-225 is DIRTY. livingroom-107 is DIRTY. bowl-511 is HOLDABLE and DIRTY. dough-510 is HOLDABLE and DIRTY. fridge-272 is OPEN and CAN_OPEN and HAS_SWITCH and HAS_PLUG and DIRTY. bowl-511 is inside livingroom-107. kitchen_table-482 is inside livingroom-107. agent-1 is inside livingroom-107. dough-510 is inside fridge-272. dough-510 is inside kitchen-225. fridge-272 is inside kitchen-225. 
Candidate actions: ['walk to kitchen_table-482', 'walk to bowl-511', 'walk to kitchen-225']
Analysis: The goal is to put dough-510 and bowl-511 on kitchen_table-482. Currently, dough-510 is in fridge-272 in kitchen-225, and bowl-511 is in livingroom-107. I have two options now, one is to take dough-510 first, while the other is to take bowl-511 first. To take dough-510, I should walk into kitchen-255 first. To take bowl-511, I should directly walk to it. So the filtered actions are walk to kitchen-225 and walk to bowl-511
Filtered actions: walk to kitchen-225, walk to bowl-511

(5)
Goal: plate-211 is CLEAN, plate-301 is CLEAN, plate-211 is inside dishwasher-293, plate-301 is inside dishwasher-293. 
Current state: microwave-300 is SWITCHOFF and OPEN and CAN_OPEN and HAS_SWITCH and HAS_PLUG and DIRTY. plate-301 is HOLDABLE and CLEAN. plate-211 is HOLDABLE and DIRTY. dishwasher-293 is SWITCHOFF and CAN_OPEN and HAS_SWITCH and DIRTY and CLOSED. kitchen-168 is DIRTY. microwave-300 is inside kitchen-168. plate-211 is inside kitchen-168. agent-1 is inside kitchen-168. dishwasher-293 is inside kitchen-168. agent-1 is close_to dishwasher-293. plate-301 is inside dishwasher-293. 
Candidate actions: ['walk to microwave-300', 'walk to plate-211', 'switch on dishwasher-293']
Analysis: The goal is to make plate-211 and plate-301 clean, and move them into dishwasher-293. Currently, plate-301 is already clean and in dishwasher-293. So, I only need to focus on plate-211. It is in the same room with me (kitchen-168) but I am not yet close to it. So the only proper action now is to walk to it, so that I can clean it and move it.
Filtered actions: walk to plate-211

Hint:
1. After "Filtered actions: ", you should output a sequece of actions separated by ", ". **Please make sure that all the acions are selected from the candidate actions.**
2. All the actions in "Candidate actions" are physically performable. You only need to filter those that are unlike to be helpful for the current state.
3. You need to be close to an object (by walking to it) before you interact with it.
4. You can hold at most two objects simultaneously.

Now here comes the query.
"""
