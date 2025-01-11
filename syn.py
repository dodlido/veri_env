import sys
import os
import subprocess
import argparse
from pathlib import Path
from typing import List, Tuple
from utils.general import gen_note
from utils.general import gen_err
from utils.general import gen_validate_path
from utils.general import gen_outlog
from utils.general import gen_find_cfg_file
from utils.getlist import getlist
from utils.general import gen_get_descriptor
from utils.cfgparse import show_views
from utils.cfgparse import get_top_level_path


# parse flags:
def parse_args():

    parser = argparse.ArgumentParser(description='Synthsize a given view of any design')
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
    parser.add_argument('--show', action='store_true', dest='show', help='Show synthesis output using graphviz', default=False)

    # get arguments
    args = parser.parse_args(None if sys.argv[1:] else ['-h'])

    # find cfg path 
    cfg_path = gen_find_cfg_file(args.c, args.ws, args.p, args.b)
        
    # parse view name #
    if not args.view:
        gen_err('view name must be provided to simulate')
    elif args.view=='show':
        show_views(cfg_path)
        
    return cfg_path, args.view, args.show

# convert code to verilog, remove sv constructs 
def _sv2v(work_dir: Path):
    
    # validate filelist path
    filelist_path = work_dir / Path('design.fl')
    gen_validate_path(filelist_path, 'locate filelist to send to yosys')

    # start building command
    command = ['sv2v']

    # read filelist
    with open(filelist_path, 'r') as file:
        for line in file:
            command.append(line.strip('\n').strip())
    
    # run conversion
    synth_file = work_dir / 'synth_preprocess.v'
    with open(synth_file, 'w') as sf:
        subprocess.run(command, stdout=sf)

# update yosys script in workdir from template
def _create_ys_script(block_name: str, top_level_module: str, work_dir: Path, show: bool=False, results_names: List[str]=[], results_paths: List[str]=[]) -> Tuple[Path, Path, List[str], List[str]]:
    show_char = '#' if not show else ''

    # validate synthfile is there
    synthfile = work_dir / 'synth_preprocess.v'
    gen_validate_path(synthfile, 'locate synthesizable verilog to send to yosys')

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
    script_content = script_content.replace('{FILELIST}', str(synthfile))
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
    cfg_path, view, show = parse_args()
    # 1. Get descriptor from configuraiton file
    ws_path, _, block_name, _, _, work_dir = gen_get_descriptor(cfg_path, view)
    # 2. Generate filelist
    results_names, results_paths = getlist(ws_path, cfg_path, view, work_dir, True)
    # 3. Find top level module
    top_level_module = get_top_level_path(cfg_path, view).stem
    # 4. Pre-process Systemverilog code
    _sv2v(work_dir)
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