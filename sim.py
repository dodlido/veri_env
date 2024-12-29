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
from utils.cfgparse import get_top_level_path
from utils.moduleparser import get_if
from utils.git_funcs import show_repos

# parse flags:
def parse_args():

    parser = argparse.ArgumentParser(description='Simulate a given view of any design')
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
    parser.add_argument('--waves', action='store_true', dest='wave', help='Create waves', default=False)
    parser.add_argument('--sim-time', type=int, action='store', dest='simtime', help='simulation time for automatically generated testbench, specified in [cycles]', default=(2**16))
    parser.add_argument('--no-coco', action='store_true', dest='nococo', help='compile only, no cocotb testbench', default=False)
    
    # get arguments
    args = parser.parse_args(None if sys.argv[1:] else ['-h'])

    # find cfg path 
    cfg_path = gen_find_cfg_file(args.c, args.ws, args.p, args.b)
        
    # parse view name #
    if not args.view:
        gen_err('view name must be provided to simulate')
    elif args.view=='show':
        show_views(cfg_path)
        
    return cfg_path, args.view, args.wave, args.simtime, args.nococo

# Generates a makefile
def _make_make(work_dir: str, top_level_module: str, block_name: str, results_names: List[str]=[], results_paths: List[str]=[]) -> Tuple[List[str], List[str]]:
    
    fl_path = Path(work_dir) / Path('design.fl')
    make_path = Path(work_dir) / Path('makefile')
    gen_validate_path(fl_path, 'locate filelist during makefile creation', False)
    
    # read filelist
    with open(fl_path, 'r') as fl:
        fl_list = fl.readlines()
    
    # write makefile
    with open(make_path, 'w') as makefile:

        # makefile header
        makefile.write('# Makefile\n\n# Defaults\n') 
        makefile.write('SIM ?= icarus\n')
        makefile.write('TOPLEVEL_LANG ?= verilog\n\n')

        # makefile filelist
        for file in fl_list:
            file_str = str(Path(file.rstrip()).as_posix())
            makefile.write('VERILOG_SOURCES += ' + file_str + '\n')

        # makefile footer
        makefile.write('\nTOPLEVEL = ' + top_level_module + '\n\n')
        makefile.write('MODULE = ' + block_name + '_tb\n\n')
        makefile.write('include $(shell cocotb-config --makefiles)/Makefile.sim')
    
    # notify user
    gen_note(f'wrote makefile to {make_path}')
    results_names.append('makefile')
    results_paths.append(make_path)

    return results_names, results_paths

# Get a list of input names and a list of output names for a given module
def _get_sim_portlist(rtl_dir: Path, top_level_module: str, work_dir: Path, results_names: List[str]=[], results_paths: List[str]=[]) -> Tuple[List[str], List[str]]:
    top_level_path = rtl_dir / Path(top_level_module + '.v')
    if_dict = get_if(top_level_path)
    clks, rsts, inputs, outputs, panics  = [], [], [], [], []
    for dictionary in if_dict:
        for i, name in enumerate(dictionary["names"]):
            if dictionary['directions'][i]=='input':
                if 'clk' in name:
                    clks.append(name)
                elif ('rst' or 'reset') in name:
                    rsts.append(name)
                else:
                    inputs.append(name)
            else:
                if 'panic' in name:
                    panics.append(name)
                else:
                    outputs.append(name)
    output_dir = work_dir / Path('port_description')
    output_dir.mkdir(parents=True, exist_ok=True) # Create output directory if needed
    
    # write clocks file
    clks_file = output_dir / Path('clks.txt')
    with open(clks_file, 'w') as file:
        for clk in clks:
            file.write(clk+'\n')

    # write resets file
    rsts_file = output_dir / Path('resets.txt')
    with open(rsts_file, 'w') as file:
        for rst in rsts:
            file.write(rst+'\n')

    # write inputs file
    inputs_file = output_dir / Path('inputs.txt')
    with open(inputs_file, 'w') as file:
        for _input in inputs:
            file.write(_input+'\n')
    
    # write outputs file
    outputs_file = output_dir / Path('outputs.txt')
    with open(outputs_file, 'w') as file:
        for output in outputs:
            file.write(output+'\n')
    
    # write panic file
    panics_file = output_dir / Path('panics.txt')
    with open(panics_file, 'w') as file:
        for panic in panics:
            file.write(panic+'\n')
    
    results_names.append('port lists')
    results_paths.append(output_dir)
    return results_names, results_paths

# Generates a generic testbench
def _gen_tb(tb_dir: Path, work_dir: Path, block_name: str, simtime: int, results_names: List[str]=[], results_paths: List[str]=[]) -> Tuple[List[str], List[str]]:
    
    # Paths to Testbenches
    homedir_tb_path = tb_dir / Path(block_name + '_tb.py') 
    workdir_tb_path = work_dir / Path(block_name + '_tb.py')   
    auto_tb_path = Path(os.environ['tools_dir']) / Path('resources/auto_tb_template.py')
    
    # Generate automatic testbench:
    if not homedir_tb_path.is_file():
        gen_note(f'there is no existing testbench in {homedir_tb_path}, an automatic one will be generated')
        with open(auto_tb_path, 'r') as file:
            tb_contents = file.read()
        tb_contents = tb_contents.replace('{WORK_DIR}', str(work_dir))
        tb_contents = tb_contents.replace('{ITERATIONS}', str(simtime))
    # Get existing testbench from verification directory:
    else:
        gen_note(f'found an existing testbench in {homedir_tb_path}, this will be used for simulation')
        # add verification directory to sys path in case there are some additional files in there:
        sys.path.insert(0, str(tb_dir.parent)) 
        tb_contents = 'import sys\n' 
        tb_contents += 'sys.path.append("' + str(homedir_tb_path.parent.parent) + '")\n'
        with open(homedir_tb_path, 'r') as file:
            tb_contents += file.read()
    
    # Write testbench to workdir
    with open(workdir_tb_path, 'w') as worktb_file:
        worktb_file.write(tb_contents)
    gen_note(f'testbench written to {workdir_tb_path}')
    results_names.append('testbench')
    results_paths.append(workdir_tb_path)
    
    return results_names, results_paths

# Add 'dump vcd file' section in design:
def _add_dump_vcd(work_dir: str, top_level_module: str) -> None:
    
    # validate filelist path
    fl_path = Path(work_dir) / Path('design.fl')
    gen_validate_path(fl_path, 'locate filelist during vcd dump process')
    
    # find top level path in filelist
    with open(fl_path, 'r') as file_list:
        for line in file_list:
            if top_level_module in line:
                top_level_path = Path(line.rstrip())
    
    # throw an error if top level module was not found
    if not top_level_path.is_file():
        gen_err(f'top level module not found in {top_level_path}')
    
    # read design to temp
    with open(top_level_path, 'r') as design:
        old = design.readlines() 
    
    # write old content to temporary file
    temp_path = Path(str(top_level_path) + '.temp')
    with open(temp_path, 'w') as origin:
        for line in old:
            origin.write(line)
    gen_note(f'design temporarly backed up to {temp_path}')

    # overwrite content with the design + a dump command
    with open(top_level_path, 'w') as design:
        for line in old:
            if 'endmodule' in line:
                design.write('\ninitial begin\n   $dumpfile(\"dump.vcd\");\n   $dumpvars(1, ' + top_level_module + ');\nend\nendmodule') 
            else:
                design.write(line)
    gen_note(f'vcd dump command added to top-level module in {top_level_path}')
        
# Remove 'dump vcd file' section in design:
def _rem_dump_vcd(work_dir: str, top_level_module: str) -> None:

    # validate filelist path
    fl_path = Path(work_dir) / Path('design.fl')
    gen_validate_path(fl_path, 'locate filelist during vcd removal process')

    # find top level path in filelist
    with open(fl_path, 'r') as file_list:
        for line in file_list:
            if top_level_module in line:
                top_level_path = Path(line.rstrip())
    
    # throw an error if top level module was not found
    if not top_level_path.is_file():
        gen_err(f'top level module not found in {top_level_path}')
    
    # validate original design backup path
    top_level_origin_path = Path(str(top_level_path) + '.temp')
    gen_validate_path(top_level_origin_path, 'locate backup design in dump removal process')

    # read original design backup
    with open(top_level_origin_path, 'r') as design:
        old = design.readlines() 
    
    # write to original design location
    with open(top_level_path, 'w') as design:
        for line in old:
            design.write(line)
    
    # remove temporary design
    subprocess.run(['rm ' + str(top_level_origin_path)], shell=True)

# Run make or iverilog command on shell 
def _run(work_dir: Path, top_level_module: str, nococo: bool=False, results_names: List[str]=[], results_paths: List[str]=[]) -> Tuple[List[str], List[str]]:

    # store current directory in temp
    current_dir = os.getcwd()
    # cd into workdir
    gen_validate_path(work_dir, f'locate workdir', True)
    os.chdir(work_dir)

    # no cocotb flow:
    if nococo:
        # validate work directory exists and makefile exists
        fl_path = Path(work_dir) / Path('design.fl')
        gen_validate_path(fl_path, 'locate filelist for compilation', False)
        
        # run command on shell
        command = 'iverilog -s ' + top_level_module + ' -o ' + top_level_module + '_compile_results -c ' + str(fl_path) + ' -g2012'
        output = subprocess.run([command], shell=True)
        
        # append outputs to result list
        results_names.append('compilation output')
        results_paths.append(Path(f'{work_dir}/{top_level_module}_compile_results'))
        
    # cocotb flow:
    else:
        # make
        makefile_path = work_dir / Path('makefile')
        gen_validate_path(makefile_path, f'locate makefile in {makefile_path}')
        gen_note(f'running makefile in {makefile_path}')
        output = subprocess.run(['make'], shell=True)

        # append output results
        results_names.append('simulation output')
        results_paths.append(work_dir / Path('results.xml'))
            
    # cd back to original directory
    os.chdir(current_dir)

    # check if simulation failed:
    failed = output.returncode!=0

    return results_names, results_paths, failed

# open GTKWave
def _wave(work_dir: str, results_names: List[str]=[], results_paths: List[str]=[]) -> Tuple[List[str], List[str]]:
    found_vcd = False
    for child in Path(work_dir).iterdir():
        if child.is_file() and child.suffix=='.vcd':
            if found_vcd:
                gen_note('found more than one .vcd file in folder, took the first ignored the rest')
            else:
                found_vcd = True
                vcd_path = child
    if found_vcd:
        gen_note(f'opening vcd file in {vcd_path} using GTKWave')
        subprocess.run(['gtkwave', vcd_path, '&'])
        results_names.append('vcd dump')
        results_paths.append(Path(vcd_path))
        return results_names, results_paths
    else:
        gen_err('no vcd files found')

# create test files: makefile and testbench
def create_test(tb_dir: Path, work_dir: Path, top_level_module: str, rtl_dir: Path, block_name: str, simtime: int, results_names: List[str]=[], results_paths: List[str]=[]) -> Tuple[List[str], List[str]]:
    results_names, results_paths = _make_make(work_dir, top_level_module, block_name, results_names, results_paths)
    results_names, results_paths = _gen_tb(tb_dir, work_dir, block_name, simtime, results_names, results_paths)
    results_names, results_paths = _get_sim_portlist(rtl_dir, top_level_module, work_dir, results_names, results_paths)
    return results_names, results_paths

# 4. Run simulation 
def run_sim(work_dir: Path, top_level_module: str, waves: bool, nococo: bool=False, results_names: List[str]=[], results_paths: List[str]=[]) -> Tuple[List[str], List[str]]:
    # 0. Temporarly edit design to include vcd dump
    if not nococo and waves:
        _add_dump_vcd(work_dir, top_level_module)
    # 1. Run makefile or icarus only
    results_names, results_paths, failed = _run(work_dir, top_level_module, nococo, results_names, results_paths)
    # 2. Open GTKWave if needed
    if not nococo and waves:
        results_names, results_paths = _wave(work_dir, results_names, results_paths)
    # 3. Remove Dump
    if not nococo and waves:
        _rem_dump_vcd(work_dir, top_level_module)
    
    return results_names, results_paths, failed

############################
###                      ###
### sim.py main function ###
###                      ###
############################

def main() -> None:
    # 0. Parse user arguments
    cfg_path, view, waves, simtime, nococo = parse_args()
    # 1. Get descriptor from configuraiton file
    ws_path, project_name, block_name, rtl_dir, tb_dir, work_dir = gen_get_descriptor(cfg_path, view)
    # 2. Generate filelist
    results_names, results_paths = getlist(ws_path, cfg_path, view, work_dir, True)
    # 3. Find top-level-module
    top_level_module = get_top_level_path(cfg_path, view).stem
    # 4. Create test files: makefile and testbench
    if not nococo:
        results_names, results_paths = create_test(tb_dir, work_dir, top_level_module, rtl_dir, block_name, simtime, results_names, results_paths)
    # 5. Run simulation
    results_names, results_paths, failed = run_sim(work_dir, top_level_module, waves, nococo, results_names, results_paths)
    # 6. Print log
    log_header = 'Simulation Completed Successfully' if not failed else 'Simulation Failed'
    gen_outlog(results_names, results_paths, log_header, failed)

############################
###                      ###
### sim.py main function ###
###                      ###
############################

if __name__ == '__main__':
    main()
