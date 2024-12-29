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
from utils.general import gen_show_ws
from utils.cfgparse import show_views
from utils.cfgparse import get_top_rgf_path
from utils.cfgparse import get_top_level_path

# parse flags:
def parse_args():

    parser = argparse.ArgumentParser(description='regen.py - get verilog code (instance or module) or html descriptions of a given view')
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
    # options
    parser.add_argument('-html', '--html', action='store_true', dest='html', help='Get HTML description of the registers', required=False)
    parser.add_argument('-inst', '--inst', action='store_true', dest='inst', help='Append RGF instance to top-level-module', required=False)
    parser.add_argument('-verilog', '--verilog', action='store_true', dest='verilog', help='Generate verilog source code', required=False)
    # output directory
    parser.add_argument('-o', '--out-dir', type=str, action='store', dest='out', help='Output directory for verilog or HTML files', required=False)
    parser.add_argument('-a', '--append', action='store_true', dest='a', help='If set, instance will be appended to top-level-module. Otherwise it will be in a new file in --out-dir', required=False)
    
    # get arguments
    args = parser.parse_args(None if sys.argv[1:] else ['-h'])

    # find cfg path 
    cfg_path = gen_find_cfg_file(args.c, args.ws, args.p, args.b)
        
    # parse view name #
    if not args.view:
        gen_err('view name must be provided to simulate')
    elif args.view=='show':
        show_views(cfg_path)
    
    if not args.out:
        out_dir = Path.cwd()
    else:
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        
    return cfg_path, args.view, args.html, args.inst, args.verilog, out_dir, args.a

def execute(rgf_path: Path, top_module_path: Path, html: bool, inst: bool, verilog: bool, out_dir: Path, append: bool)->None:
        notes = []
        rgf_name = rgf_path.stem
        
        # read RGF description from file
        with open(rgf_path, 'r') as rgf_file:
            rgf_content = rgf_file.read()
    
        # 1. Append instance to top level module
        if inst:
            if append:
                rgf_content += f'''
inst = {rgf_name}.get_inst()
with open('{top_module_path}', 'a') as top_module:
    top_module.write(inst)'''
                notes.append(f'appended {rgf_name} instance to {top_module_path}')
            else:
                out_file = out_dir / f'{rgf_name}_inst.v'
                rgf_content += f'''
inst = {rgf_name}.get_inst()
with open('{out_file}', 'w') as instance_file:
    instance_file.write(inst)'''
                notes.append(f'wrote {rgf_name} instance verilog code to {out_file}')
        
        # 2. Write verilog to out_dir
        if verilog:
            out_file = out_dir / f'{rgf_name}.v'
            rgf_content += f'''
verilog = {rgf_name}.get_verilog()
with open('{out_file}', 'w') as verilog_file:
    verilog_file.write(verilog)'''
            notes.append(f'wrote {rgf_name} verilog code to {out_file}')
        
        # 3. Write HTML to out_dir
        if html:
            out_file = out_dir / f'{rgf_name}.html'
            rgf_content += f'''
html = {rgf_name}.get_html()
with open('{out_file}', 'w') as html_file:
    html_file.write(html)'''
            notes.append(f'wrote {rgf_name} html to {out_file}')
            
        # Write RGF content to temp.py
        temp_path = Path('temp.py')
        with open(temp_path, 'w') as temp_file:
            temp_file.write(rgf_content)
        
        # Run temp.py
        output = subprocess.run(['python3', f'{temp_path}'])
        if output.returncode!=0:
            gen_err(f'failed to run {temp_path}')
        subprocess.run(['rm', f'{temp_path}'])
        
        # Output results to log
        for note in notes:
            gen_note(note)

def main():
    # 0. parse arguments
    cfg_path, view, html, inst, verilog, out_dir, append = parse_args()
    # 1. get top level module path
    top_module_path = get_top_level_path(cfg_path, view)
    # 2. get RGF path
    rgf_path = get_top_rgf_path(cfg_path, view)
    # 3. execute user request - html \ verilog \ append instance
    execute(rgf_path, top_module_path, html, inst, verilog, out_dir, append)

if __name__ == '__main__':
    main()

