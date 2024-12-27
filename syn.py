import sys
import os
import subprocess
import argparse
from pathlib import Path
from typing import List, Tuple
from utils.general import gen_note
from utils.general import gen_err
from utils.general import gen_show_ws
from utils.general import gen_validate_path
from utils.general import gen_outlog
from utils.general import gen_search_parent
from utils.general import gen_find_cfg_file
from utils.getlist import getlist
from utils.cfgparse import get_descriptor
from utils.cfgparse import show_views

# parse flags:
def parse_args():

    # sim arguments
    parser = argparse.ArgumentParser(description='Simulate a given view of any design')
    parser.add_argument('-w', '--workspace', type=str, action='store', dest='ws', help='Path to workspace', required=False)
    parser.add_argument('-c', '--cfg', type=str, action='store', dest='c', help='Path to configuration file', required=False)
    parser.add_argument('-v', '--view', type=str, action='store', dest='view', help='Desired view', required=False)
    parser.add_argument('--show', action='store_true', dest='show', help='Show synthesis output using graphviz', default=False)
    
    # get arguments
    args = parser.parse_args(None if sys.argv[1:] else ['-h'])

    # parse workspace path
    if not args.ws:
        ws_path = gen_search_parent(Path.cwd().absolute(), Path(os.environ['home_dir']))
    elif args.ws=='show':
        gen_show_ws()
    else:
        ws_path = Path(args.ws)
        gen_validate_path(ws_path, 'locate provided workspace directory', True)
        
    # parse config path
    if not args.c:
        cfg_path = gen_find_cfg_file(Path.cwd().absolute())
    else:
        cfg_path = Path(args.c)
        gen_validate_path(cfg_path, 'locate provided configuration file')
    
    if not args.view:
        gen_err('view name must be provided to simulate')
    elif args.view=='show':
        show_views(cfg_path)
        
    return ws_path, cfg_path, args.view, args.show

# update yosys script in workdir from template
def _create_ys_script(block_name: str, top_level_module: str, work_dir: Path, show: bool=False, results_names: List[str]=[], results_paths: List[str]=[]) -> Tuple[Path, Path, List[str], List[str]]:
    show_char = '#' if not show else ''

    # validate filelist path
    filelist_path = work_dir / Path('design.fl')
    gen_validate_path(filelist_path, 'locate filelist to send to yosys')

    # read filelist
    with open(filelist_path, 'r') as file:
        flattened_filelist = file.read()
    
    # filelist is one gigantic row
    flattened_filelist = flattened_filelist.replace('\n', ' ')

    # validate .lib path
    libraries_path = Path(os.environ['libs_path'])
    gen_validate_path(libraries_path, 'locate cells library before synthesis')

    # build output path
    output_path = work_dir / Path(f'{top_level_module}_synth.v')

    # validate template script path
    template_path = Path(os.environ['tools_dir']) / Path('resources/synth_template.ys')
    gen_validate_path(template_path, 'locate yosys template script')

    # read template and update the contents with the given parameters
    with open(template_path, 'r') as file:
        script_content = file.read()
    script_content = script_content.replace('{FILELIST}', flattened_filelist)
    script_content = script_content.replace('{TOP_LEVEL_MODULE}', top_level_module)
    script_content = script_content.replace('{LIB}', str(libraries_path))
    script_content = script_content.replace('{OUTPUT_PATH}', str(output_path))
    script_content = script_content.replace('{SHOW}', show_char)

    # write script
    script_path = work_dir / Path(f'{block_name}_synth.ys')
    with open(script_path, 'w') as file:
        file.write(script_content)
    gen_note(f'created a yosys synthesis script at {script_path}')
    results_names.append('synthesis yosys script')
    results_paths.append(script_path)

    return script_path, output_path, results_names, results_paths

# run syntesis script in     
def _run_syn(work_dir: Path, script_path: Path, output_path: Path, results_names: List[str]=[], results_paths: List[str]=[]) -> Tuple[List[str], List[str]]:
    
    # locate yosys
    yosys_dir = Path(os.environ['yosys_dir'])
    gen_validate_path(yosys_dir, 'locate yosys directory', True)

    # validate script exists
    gen_validate_path(script_path, 'locate yosys synthesis script')
    
    # cd into workdir
    current_dir = os.getcwd()
    os.chdir(work_dir)

    # run script
    command = f'{yosys_dir}/./yosys {script_path}'
    gen_note(f'running "{command}"')
    output = subprocess.run([command], shell=True)
    gen_note(f'synthesis complete, results are in {output_path}')
    results_names.append('syntesis results')
    results_paths.append(output_path)

    # go back to original directory
    os.chdir(current_dir)

    # check if simulation failed:
    failed = output.returncode!=0

    return results_names, results_paths, failed

############################
###                      ###
### syn.py main function ###
###                      ###
############################

def main() -> None:
    # 0. Parse user arguments
    ws_path, cfg_path, view, show = parse_args()
    # 1. Get descriptor from configuraiton file
    _, block_name, top_level_module, _, _, work_dir = get_descriptor(cfg_path, ws_path, view)
    # 2. Generate filelist
    results_names, results_paths = getlist(ws_path, cfg_path, view, work_dir, True)
    # 3. Create yosys script in workdir
    script_path, output_path, results_names, results_paths = _create_ys_script(block_name, top_level_module, work_dir, show, results_names, results_paths)
    # 4. Run yosys script
    results_names, results_paths, failed = _run_syn(work_dir, script_path, output_path, results_names, results_paths)
    # 5. Print log
    log_header = 'Synthesis Completed Successfully' if not failed else 'Synthesis Failed'
    gen_outlog(results_names, results_paths, log_header, failed)

############################
###                      ###
### syn.py main function ###
###                      ###
############################

if __name__ == '__main__':
    main()