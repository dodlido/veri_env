import argparse
import sys
from utils.git_funcs import create_github_repository

def parse_args():
    # add.py arguments
    parser = argparse.ArgumentParser(description='get repo\n Usage: add.py -r <repo_name>\nDefaults to pre-defined WS path')
    parser.add_argument('-r', '--repo', type=str, action='store', dest='r', help='Repository to get', required=True)
    
    # get arguments
    args = parser.parse_args(None if sys.argv[1:] else ['-h'])
   
    return args.r

# Usage: add.py -r <repo name> 
def main() -> None:
    # 0. Parse flags
    repo_name = parse_args()
    # 1. Create remote repo
    create_github_repository(repo_name)

if __name__ == '__main__':
    main()
