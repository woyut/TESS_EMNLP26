import argparse


def get_args():
    parser = argparse.ArgumentParser(description='TESS')

    parser.add_argument(
        '--task_file_path', type=str, default="./tinytest_full.pik")
    parser.add_argument(
        '--save_file_dir', type=str, default="./save_results")
    
    parser.add_argument(
        '--seed', type=int, default=0)
    
    parser.add_argument(
        '--agent_type', type=str, default="llm_llm_llmFilterAunsatisfied_llmprompt")
    parser.add_argument(
        '--runner_type', type=str, default="BaseRunner_VH_GraphSim")
    
    parser.add_argument(
        '--filter_api_model', type=str, default="gpt-4.1-mini")
    parser.add_argument(
        '--translation_res', type=str)
    parser.add_argument(
        '--search_depth', type=int, default=500)
    
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = get_args()
