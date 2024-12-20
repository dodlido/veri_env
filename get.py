import git
import argparse
import os
import sys
from pathlib import Path

def _err(m):
    print('Error: ' + m)
    exit(2)

def _check_ws_path(p: str)->Path:
    ws_path = Path(p)
    if not p.is_dir():
        message = 'Provided WS path (' + p + ') is not a valid directory'
        _err(message)
    else:
        return ws_path


def search_until_parent_target(start_dir, target_dir):
    current_dir = start_dir
    while current_dir != os.path.dirname(current_dir):  # Until we reach the root of the filesystem
        parent_dir = os.path.dirname(current_dir)
        
        # Check if the parent directory matches the target directory
        if os.path.basename(parent_dir) == target_dir:
            return parent_dir
        
        # Move to the parent directory
        current_dir = parent_dir
    
    _err(f"Home directory '{target_dir}' not found above your location and so workspace was not inferred")
    return None

def parse_args():
    parser = argparse.ArgumentParser(description='get repo\n Usage: add.py -r <repo_name>\nDefaults to pre-defined WS path')
    parser.add_argument('-r', '--repo', type=str, action='store', dest='r', help='Repository to get', required=True)
    parser.add_argument('-w', '--user-ws', type=str, action='store', dest='w', help='User specified work-space path', required=False)
    args = parser.parse_args()
    if len(sys.argv)==0: # No flags supplied
        parser.print_help()
        exit(2)
    else:
        elif not args.w:
            ws_path = search_until_parent_targe(os.cwd(), os.environ['home_dir']) 
        else:
            ws_path = _check_ws_path(args.w)
        repo_name = args.r
        repo_path = ws_path / Path(args.r)
        return repo_name, repo_path

# Usage: get.py -r <repo name> 
def main() -> None:
    # 0. Parse flags
    repo_name, ws_path = parse_args()
    # 1. Clone to WS_path/repo_name
    git_main_path = os.environ['git_main_path']
    git.Repo.clone_from(git_main_path + repo_name + '.git', ws_path)

if __name__ == '__main__':
    main()
