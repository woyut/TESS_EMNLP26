import sys
import os
import pickle
import json
import random
from pathlib import Path

import agents
import runners
from arguments import get_args
from openai import OpenAI

if __name__ == '__main__':
    args = get_args()
    
    os.makedirs(args.save_file_dir, exist_ok=True)
    random.seed(args.seed)
    
    all_task_instances = pickle.load(open(args.task_file_path, 'rb'))
    test_results = {}
    
    client = OpenAI(
        api_key="",
        base_url=""
    )
        
    agent = getattr(agents, args.agent_type)(
        client, env_name="VH_graph", filter_api_model=args.filter_api_model, search_depth=args.search_depth, translation_res=args.translation_res)
    runner = getattr(runners, args.runner_type)(agent)
    print(len(all_task_instances))
    SR = 0
    GCR = 0

    for i_task_instance, task_instance in enumerate(all_task_instances):
        (success, gcr), steps, saved_info = runner.run(task_instance, task_instance['task_id']) 
        print('-------------------------------------')
        print(f'TaskID: {i_task_instance}/{len(all_task_instances)}, TaskName: {task_instance["task_goal"]["grounded_task_name"]}')
        print('success' if success else 'failure')
        print('GCR:', gcr)
        print('steps:', steps)
        print(saved_info["action"])
        print('-------------------------------------')
        sys.stdout.flush()
        SR += success
        GCR += gcr
        json.dump(saved_info, open(os.path.join(args.save_file_dir, f"{i_task_instance}-{task_instance['task_id']}.json"), 'w'), indent=4)
    print(SR/len(all_task_instances), GCR/len(all_task_instances))
    