import os
import sys
import argparse
from pathlib import Path
from utils.general import gen_validate_path
from utils.general import gen_search_parent
from utils.git_funcs import clone_repo

def parse_args():

    # get arguments
    parser = argparse.ArgumentParser(description='get repo\n Usage: add.py -r <repo_name>\nDefaults to pre-defined WS path')
    parser.add_argument('-r', '--repo', type=str, action='store', dest='r', help='Repository to get', required=True)
    parser.add_argument('-w', '--user-ws', type=str, action='store', dest='w', help='User specified work-space path', required=False)

    # get arguments
    args = parser.parse_args(None if sys.argv[1:] else ['-h'])
    
    # parse workspace path
    if not args.w:
        ws_path = gen_search_parent(Path.cwd().absolute(), Path(os.environ['home_dir']))
    else:
        ws_path = Path(args.w)
        gen_validate_path(ws_path, 'locate provided workspace directory', True)
        
    # parse repo path
    repo_name = args.r
    dest_path = ws_path / Path(args.r)

    return repo_name, dest_path

# Usage: get.py -r <repo name> 
def main() -> None:
    # 0. Parse flags
    repo_name, dest_path = parse_args()
    # 1. Clone to WS_path/repo_name
    clone_repo(repo_name, dest_path)

if __name__ == '__main__':
    main()
