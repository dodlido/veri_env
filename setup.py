import os
import sys
from pathlib import Path
import subprocess
import argparse
import sched
import time

def parse_args():
    parser = argparse.ArgumentParser(description='setup')
    parser.add_argument('-w', '--workspace', type=str, action='store', dest='w', help='Workspace directory', required=True)
    args = parser.parse_args()
    if len(sys.argv)==0: # No flags supplied
        parser.print_help()
        exit(2)
    else:
        return args.w

def main() -> None:
    work_top_path = Path('D:/work') # All workspaces are below this directory
    workplace_path = (work_top_path / Path(parse_args())).absolute() # Get path from user
    workplace_path.mkdir(parents=True, exist_ok=True) # Create workplace if needed
    with open(str(work_top_path.absolute()) + '/.curr_ws', 'w') as file:
        file.write(str(workplace_path))
    
if __name__ == '__main__':
    main()