import git
import argparse
import os
import sys
from pathlib import Path

def _err(m):
    print('Error: ' + m)
    exit(2)

def _check_ws_path(p):
    if not p.is_dir():
        message = 'Provided WS path (' + str(p) + ') is not a valid directory'
        _err(message)

def parse_args():
    parser = argparse.ArgumentParser(description='get repo\n Usage: add.py -r <repo_name>\nDefaults to pre-defined WS path')
    parser.add_argument('-r', '--repo', type=str, action='store', dest='r', help='Repository to get', required=True)
    parser.add_argument('-w', '--user-ws', type=str, action='store', dest='w', help='User specified work-space path', required=False)
    parser.add_argument('-dw', '--default-ws', type=str, action='store', dest='dw', help='Default work-space path', required=False)
    args = parser.parse_args()
    if len(sys.argv)==0: # No flags supplied
        parser.print_help()
        exit(2)
    else:
        if not args.dw and not args.w:
            _err('WS not provided and not pre-set')
        elif not args.w:
            ws_path = Path(args.dw)
        else:
            ws_path = Path(args.w)
        _check_ws_path(ws_path)
        return args.r, ws_path / Path(args.r)

# Usage: get.py -r <repo name> 
def main() -> None:
    # 0. Parse flags
    repo_name, ws_path = parse_args()
    # 1. Clone to WS_path/repo_name
    git.Repo.clone_from('git@github.com:dodlido/' + repo_name + '.git', ws_path)

if __name__ == '__main__':
    main()