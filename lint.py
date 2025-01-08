from pathlib import Path
from typing import List, Tuple
import subprocess
import argparse
import sys
import os
from utils.general import gen_err
from utils.general import gen_note
from utils.general import gen_validate_path
from utils.general import gen_search_parent
from utils.general import gen_find_cfg_file
from utils.general import gen_outlog
from utils.general import gen_show_proj
from utils.general import gen_show_ws
from utils.general import gen_show_blk
from utils.general import gen_get_descriptor
from utils.getlist import getlist
from utils.cfgparse import show_views
from utils.cfgparse import get_views
from utils.cfgparse import get_top_level_path
from utils.moduleparser import get_if
from utils.git_funcs import show_repos

# parse flags:
def parse_args():

    parser = argparse.ArgumentParser(description='Lint a given view of any design')
    # config location - option 1 - specify the config path itself
    group1 = parser.add_mutually_exclusive_group(required=False)
    group1.add_argument('-c', '--cfg', type=str, action='store', dest='c', help='Block Location Option 1 - provide a path to configuration file', required=False)
    # config location - option 2 - specify the workspace-->project-->block triplet
    group2 = parser.add_mutually_exclusive_group(required=False)
    group2.add_argument('-w', '--workspace', type=str, action='store', dest='ws', help='Block Location Option 2 - Path to workspace , not needed if within a workspace       , "show" to display options', required=False)
    group2.add_argument('-p', '--project', type=str, action='store', dest='p'   , help='Block Location Option 2 - Project name      , not needed if you are within a project , "show" to display options', required=False)
    group2.add_argument('-b', '--block-name', type=str, action='store', dest='b', help='Block Location Option 2 - Block name        , not needed if you are within a block   , "show" to display options', required=False)
    # view name - a must
    parser.add_argument('-v', '--view', type=str, action='store', dest='view', help='Desired view, "show" to display options', required=False)

    # get arguments
    args = parser.parse_args(None if sys.argv[1:] else ['-h'])

    # find cfg path 
    cfg_path = gen_find_cfg_file(args.c, args.ws, args.p, args.b)
        
    # parse view name #
    if not args.view:
        gen_err('view name must be provided to simulate')
    elif args.view=='show':
        show_views(cfg_path)
    else:
        view = args.view
        
    return cfg_path, view

def lint(workdir: Path, top_level_module: str, results_names: List, results_paths: List):
    # log file path
    logfile = workdir / 'lint_log.txt'
    # build command 
    command_list = ['verilator', '-Wall', '--lint-only', '--top-module', top_level_module]
    # read filelist and append to command
    filelist_path = workdir / 'design.fl'
    with open(filelist_path, 'r') as fl:
        for line in fl:
            command_list.append(line.strip().rstrip('\n'))
    # run command
    with open(logfile, 'w') as lf:
        result = subprocess.run(command_list, stdout=lf, stderr=lf)
    # Parse failed return code
    failed = result.returncode!=0
    # Note to the user that you created a file
    gen_note(f'generated a lint log file at {logfile}')
    results_names.append('Lint Log') 
    results_paths.append(logfile)
    return failed, results_names, results_paths

#############################
###                       ###
### lint.py main function ###
###                       ###
#############################

def main() -> None:
    # 0. Parse user arguments
    cfg_path, view = parse_args()
    # 1. Get descriptor from configuraiton file
    ws_path, _, _, _, _, work_dir = gen_get_descriptor(cfg_path, view)
    # 2. Generate filelist
    results_names, results_paths = getlist(ws_path, cfg_path, view, work_dir, True, [], [])
    # 3. Find top-level-module
    top_level_module = get_top_level_path(cfg_path, view).stem
    # 4. Lint 
    failed, results_names, results_paths = lint(work_dir, top_level_module, results_names, results_paths)
    # 5. Generate Summary
    log_header = 'Lint Completed Succesfully' if not failed else 'Lint Completed With Warnings'
    gen_outlog(results_names, results_paths, log_header, False)

#############################
###                       ###
### lint.py main function ###
###                       ###
#############################

if __name__ == '__main__':
    main()