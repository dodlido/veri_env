from pathlib import Path
from typing import List, Tuple
import subprocess
import argparse
import sys
import os
from utils.general import gen_err
from utils.general import gen_note
from utils.general import gen_validate_path
from utils.general import gen_search_ws_path
from utils.getlist import getlist
from utils.cfgparse import get_descriptor
from utils.moduleparser import get_if

# parse flags:
def parse_args():
    parser = argparse.ArgumentParser(description='Simulate a given view of any design')
    parser.add_argument('-w', '--workspace', type=str, action='store', dest='ws', help='Path to workspace', required=False)
    parser.add_argument('-c', '--cfg', type=str, action='store', dest='c', help='Path to configuration file', required=False)
    parser.add_argument('-v', '--view', type=str, action='store', dest='v', help='Desired view', required=True)
    parser.add_argument('--waves', action='store_true', dest='wave', help='Create waves')
    args = parser.parse_args()
    if len(sys.argv)==0:
        parser.print_help()
        exit(2)
    else:
        if not args.ws:
            if os.environ['home_dir'] not in str(Path.cwd()):
                gen_err('you are currently not in a workspace and one was not provided')
            else:
                ws_path = gen_search_ws_path(Path.cwd().absolute())
        else:
            ws_path = Path(args.ws)
            gen_validate_path(ws_path, f'locate workspace directory {ws_path}')
        if not args.c:
            cfg_dir, cfg_path = None, None
            if str(Path.cwd()).split('/')[-1]=='misc':
                cfg_dir = Path.cwd()
            else:
                for sub in os.walk(Path.cwd()):
                    if sub[0].split('/')[-1]=='misc':
                        cfg_dir = Path.cwd() / Path('misc')
            if not cfg_dir:
                gen_err('misc directory not found')
            else:
                for item in cfg_dir.iterdir():
                    if item.suffix=='.cfg':
                        cfg_path = Path(cfg_dir) / item
            if not cfg_path:
                gen_err('.cfg file not found in misc directory')
        else:
            cfg_path = Path(args.c)
            if cfg_path.suffix!='.cfg':
                gen_err('specified cfg path is invalid')
    return ws_path, cfg_path, args.v, args.wave

# Generates a makefile
def _make_make(work_dir: str, top_level_module: str, block_name: str) -> None:
    
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
        makefile.write('MODULE = ' + top_level_module + '_tb\n\n')
        makefile.write('include $(shell cocotb-config --makefiles)/Makefile.sim')
    
    # notify user
    gen_note(f'wrote makefile to {make_path}')

# Get a list of input names and a list of output names for a given module
def _get_sim_portlist(rtl_dir: Path, top_level_module: str, work_dir: Path) -> Tuple[List[str], List[str]]:
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
    clks_file = output_dir / Path('clks.txt')
    with open(clks_file, 'w') as file:
        for clk in clks:
            file.write(clk+'\n')
    rsts_file = output_dir / Path('resets.txt')
    with open(rsts_file, 'w') as file:
        for rst in rsts:
            file.write(rst+'\n')
    inputs_file = output_dir / Path('inputs.txt')
    with open(inputs_file, 'w') as file:
        for _input in inputs:
            file.write(_input+'\n')
    outputs_file = output_dir / Path('outputs.txt')
    with open(outputs_file, 'w') as file:
        for output in outputs:
            file.write(output+'\n')
    panics_file = output_dir / Path('panics.txt')
    with open(panics_file, 'w') as file:
        for panic in panics:
            file.write(panic+'\n')

# Generates a generic testbench
def _gen_tb(tb_dir: Path, work_dir: Path, block_name: str) -> None:
    
    # Paths to Testbenches
    homedir_tb_path = tb_dir / Path(block_name + '_tb.py') 
    workdir_tb_path = work_dir / Path(block_name + '_tb.py')   
    auto_tb_path = Path(os.environ['tools_dir']) / Path('utils/auto_tb.py')
    
    # Generate automatic testbench:
    if not homedir_tb_path.is_file():
        gen_note(f'there is no existing testbench in {homedir_tb_path}, an automatic one will be generated')
        with open(auto_tb_path, 'r') as file:
            tb_contents = 'work_dir = \"' + str(work_dir) + '\"\n'
            tb_contents += file.read()
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

# Run make command on shell
def _run_make(work_dir: str) -> None:
    
    # store current directory in temp
    current_dir = os.getcwd()

    # validate work directory exists and makefile exists
    makefile_path = work_dir / Path('makefile')
    gen_validate_path(work_dir, f'locate workdir {work_dir}', True)
    gen_validate_path(makefile_path, f'locate makefile in {makefile_path}')

    # cd into workdir
    gen_note(f'temporarly cd\'ing into workdir {work_dir}')
    os.chdir(work_dir)

    # run make
    gen_note(f'running makefile in {makefile_path}')
    subprocess.run(['make'], shell=True)

    # cd back to original directory
    gen_note(f'heading back to original directory {current_dir}')
    os.chdir(current_dir)

# open GTKWave
def _wave(work_dir: str) -> None:
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
    else:
        gen_err('no vcd files found')

# create test files: makefile and testbench
def create_test(tb_dir: Path, work_dir: Path, top_level_module: str, rtl_dir: Path, block_name: str) -> None:
    _make_make(work_dir, top_level_module, block_name)
    _gen_tb(tb_dir, work_dir, block_name)
    _get_sim_portlist(rtl_dir, top_level_module, work_dir)

# 4. Run simulation 
def run_sim(work_dir: Path, top_level_module: str, waves: bool) -> None:
    # 0. Temporarly edit design to include vcd dump
    _add_dump_vcd(work_dir, top_level_module)
    # 1. Run make file
    _run_make(work_dir)
    # 2. Open GTKWave if needed
    if waves:
        _wave(work_dir)
    # 3. Remove Dump
    _rem_dump_vcd(work_dir, top_level_module)

############################
###                      ###
### sim.py main function ###
###                      ###
############################

def main() -> None:
    # 0. Parse user arguments
    ws_path, cfg_path, view, waves = parse_args()
    # 1. Get descriptor from configuraiton file
    project_name, block_name, top_level_module, rtl_dir, tb_dir, work_dir = get_descriptor(cfg_path, ws_path, view)
    # 2. Generate filelist
    getlist(ws_path, cfg_path, view, work_dir, True)
    # 3. Create test files: makefile and testbench
    create_test(tb_dir, work_dir, top_level_module, rtl_dir, block_name)
    # 4. Run simulation
    run_sim(work_dir, top_level_module, waves)

############################
###                      ###
### sim.py main function ###
###                      ###
############################

if __name__ == '__main__':
    main()
