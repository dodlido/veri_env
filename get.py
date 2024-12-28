import os
import sys
import argparse
from pathlib import Path
from utils.general import gen_err
from utils.general import gen_validate_path
from utils.general import gen_search_parent
from utils.git_funcs import clone_repo
from utils.git_funcs import show_repos
from utils.general import gen_show_ws

def parse_args():

    # get arguments
    parser = argparse.ArgumentParser(description='get repo\n Usage: add.py -r <repo_name>\nDefaults to pre-defined WS path')
    parser.add_argument('-w', '--user-ws', type=str, action='store', dest='w', help='User specified work-space path', required=False)
    parser.add_argument('-r', '--repo', type=str, action='store', dest='r', help='Repository to get', required=False)

    # get arguments
    args = parser.parse_args(None if sys.argv[1:] else ['-h'])
    
    # parse workspace path
    if not args.w:
        ws_path = gen_search_parent(Path.cwd().absolute(), Path(os.environ['home_dir']))
    elif args.ws=='show':
        gen_show_ws()
    else:
        ws_path = Path(args.w)
        gen_validate_path(ws_path, 'locate provided workspace directory', True)
        
    # show repos
    if args.r=='show':
        show_repos()

    # parse repo path
    if not args.r:
        gen_err('repo name must be provided')
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
