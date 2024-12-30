from pathlib import Path
from typing import Tuple
import argparse
import sys
from utils.general import gen_err
from utils.general import gen_note
from utils.general import gen_validate_path
from utils.general import gen_find_cfg_file
from utils.general import gen_get_descriptor
from utils.cfgparse import show_views
from utils.cfgparse import get_top_level_path
from utils.moduleparser import get_inst
from utils.cfgparse import parse_children

# parse flags:
def parse_args():

    parser = argparse.ArgumentParser(description="Instantiate given child's top-level module in a given source file")
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
    # optional triggers
    parser.add_argument('-son', '--child', type=str, action='store', dest='child', help='Desired child to instantiate', required=False)
    parser.add_argument('-dst', '--destination', type=str, action='store', dest='dst', help='Destination file to append the instance to. If none is provided, instance will be printed to terminal', required=False)
    
    # get arguments
    args = parser.parse_args(None if sys.argv[1:] else ['-h'])

    # find cfg path 
    cfg_path = gen_find_cfg_file(args.c, args.ws, args.p, args.b)
        
    # parse view name #
    if not args.view:
        gen_err('view name must be provided to simulate')
    elif args.view=='show':
        show_views(cfg_path)
    
    print = not args.dst
    if args.dst:
        gen_validate_path(Path(args.dst), 'locate destination file to append the instance to')
        dst_path = Path(args.dst)
    else:
        dst_path = args.dst
        
    return cfg_path, args.view, args.child, dst_path, print

def get_child_top_module_path(cfg_path: Path, view: str, ws_path: str, child_name: str) -> Tuple[Path,str] :
    
    # parse your block children 
    names, paths, views = parse_children(ws_path, cfg_path, view)
    
    # if supplied child is not in config --> error
    if child_name not in names:
        gen_err(f'did not find child {child_name} in children list: {names}')
    
    # find child cfg path and view
    child_cfg_path = paths[names.index(child_name)]
    child_view = views[names.index(child_name)]

    # find child top level module path
    child_top_path = get_top_level_path(child_cfg_path, child_view)
    child_top_name = child_top_path.stem

    return child_top_path, child_top_name

# append instance 
def append_inst(dst_path: Path, print: bool, inst: str, child_name: str, child_top_name: str)->None:
    if print:
        gen_note(f'instance of {child_name} top level module "{child_top_name}" is:\n{inst}')
    else:
        with open(dst_path, 'a') as dst_file:
            dst_file.write(inst)

def main() -> None:
    # 0. Parse user arguments
    cfg_path, view, child, dst_path, print = parse_args()
    # 1. Get descriptor from configuraiton file
    ws_path, _, _, _, _, _ = gen_get_descriptor(cfg_path, view)
    # 2. Get child top level module path
    child_top_path, child_top_name = get_child_top_module_path(cfg_path, view, ws_path, child)
    # 3. Get child module instance
    child_module_inst = get_inst(child_top_path, child_top_name)
    # 4. Write instance to output location
    append_inst(dst_path, print, child_module_inst, child, child_top_name)

if __name__ == '__main__':
    main()
