from pathlib import Path
from typing import List, Tuple
import configparser
import subprocess
import argparse
import sys
import os
from utils.enst import get_if

###################################
###                             ###
###  Start of helper functions  ###
###                             ###
###################################

# Print error message and exit
def _err(m: str) -> None:
    print('Error: ' + m)
    exit(2)

# Build child path 
def _get_child_cfg_path(ws_path: Path, child_name: str, child_type: str, papa_cfg_path: Path) -> Path:
    blk_name = child_name.split('/')[-1]
    repo_name = child_name.split('/')[0]
    if child_type=='local':
        cfg_path = ws_path / Path(repo_name) / Path('design') / Path(blk_name) / Path('misc') / Path(blk_name + '.cfg')
    elif 'release' in child_type:
        if ',' not in child_type:
            _err('Syntax error in ' + child_type + 'provide release version in a \'release, x.y.z\' format')
            if len(child_type.split(','))!=2:
                _err('Syntax error in ' + child_type + 'provide release version in a \'release, x.y.z\' format')
        else:
            version = child_type.split(',')[-1].replace(' ', '')
            cfg_path = Path(os.environ['rls_dir']) / Path(repo_name) / Path('v' + version) / Path('design') / Path(blk_name) / Path('misc') / Path(blk_name + '.cfg')
    else:
        _err(child_type + ' not supported yet')
    if not cfg_path.is_file():
            _err('.cfg file not found in path: ' + str(cfg_path))
    else:
        return cfg_path

# Parses 'path' section and returns names and paths of valid childs
def _get_paths(ws_path: Path, config: configparser, cfg_path: Path) -> Tuple[List[str], List[Path]]:
    names, paths = [], []
    if 'path' in config:
        for child_name in config['path']:
            child_type = config['path'].get(child_name)
            paths.append(_get_child_cfg_path(ws_path, child_name, child_type, cfg_path))
            names.append(child_name)
    return names, paths
        
# Parses 'child' section in view and returns lists of child names, paths to cfgs and view names
def _get_children(config: configparser, view: str, child_names: List[str], child_paths: List[Path]) -> Tuple[List[str], List[Path], List[str]]:
    child_views, new_paths, new_names = [], [], []
    if view in config:
        if 'child' in config[view]:
            child_content = config[view]['child'].split('\n')
            for child in child_content:
                child.replace(' ', '')
                if child == '' or child == '\n':
                    continue
                else:
                    if '=' not in child:
                        _err('Syntax error in line ' + child + ', please provide both a child name and a view seperated by a delimiter')
                    elif (len(child.split('=')) != 2):
                        _err('Syntax error in line ' + child + ', please provide both a child name and a view seperated by a delimiter')
                    else:
                        child_name, child_view = child.split('=')[0], child.split('=')[1]
                        if child_name not in child_names:
                            _err('Child ' + child_name + ' was not provided a path')
                        else:
                            child_views.append(child_view)
                            new_names.append(child_name)
                            new_paths.append(child_paths[child_names.index(child_name)])
    return new_names, new_paths, child_views


# Parses 'file' under a given view and returns a list of files
def _get_files(config: configparser, view: str, cfg_path: str) -> List[Path]:
    files = []
    if view in config:
        if 'file' in config[view]:
            file_content = config[view]['file'].split('\n')
            for f in file_content:
                if f=='':
                    continue
                else:
                    f_path = cfg_path.parent.parent / Path(f)
                    if f_path.is_file():
                        files.append(f_path)
                    else:
                        _err('File ' + f_path + ' does not exist')
        else:
            _err('No file key in view ' + view)
    else:
        _err('view ' + view + ' was not found in .cfg file')
    return files

# Parses through a config file, getting entire file list from all children
def _parse_cfg_rec(ws_path: Path, cfg_path: Path, view: str, file_list: List[Path] = []) -> List[Path]:
    cfg = configparser.ConfigParser()
    cfg.read(cfg_path)
    names, paths = _get_paths(ws_path, cfg, cfg_path)
    names, paths, views = _get_children(cfg, view, names, paths)
    if not names:
        return file_list + _get_files(cfg, view, cfg_path)
    else:
        for i,_ in enumerate(names):
            file_list += _parse_cfg_rec(ws_path, paths[i], views[i], file_list)
        return file_list + _get_files(cfg, view, cfg_path)



# Generates a .fl file list in the desired location
def _gen_fl(fl_dir: str, file_list: List[Path]) -> None:
    if not Path(fl_dir).is_dir():
        _err('Supplied output dir ' + fl_dir + ' is invalid')
    else:
        fl_path = fl_dir / Path('design.fl')
        with open(fl_path, 'w') as fl:
            for file in file_list:
                fl.write(str(file)+'\n')

# Generates a makefile
def _make_make(work_dir: str, top_level_module: str) -> None:
    fl_path = Path(work_dir) / Path('design.fl')
    make_path = Path(work_dir) / Path('makefile')
    if not fl_path.is_file():
        _err('File list not found in ' + str(fl_path))
    else:
        with open(fl_path, 'r') as fl:
            fl_list = fl.readlines()
        with open(make_path, 'w') as makefile:
            makefile.write('# Makefile\n\n# Defaults\n')
            makefile.write('SIM ?= icarus\n')
            makefile.write('TOPLEVEL_LANG ?= verilog\n\n')
            for file in fl_list:
                file_str = str(Path(file.rstrip()).as_posix())
                makefile.write('VERILOG_SOURCES += ' + file_str + '\n')
            makefile.write('\nTOPLEVEL = ' + top_level_module + '\n\n')
            makefile.write('MODULE = ' + top_level_module + '_tb\n\n')
            makefile.write('include $(shell cocotb-config --makefiles)/Makefile.sim')

# Get a list of input names and a list of output names for a given module
def _get_portlist(rtl_dir: Path, top_level_module: str, work_dir: Path) -> Tuple[List[str], List[str]]:
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
def _gen_tb(tb_dir: Path, work_dir: Path, top_level_module: str) -> None:
    
    # Paths to Testbenches
    homedir_tb_path = tb_dir / Path(top_level_module + '_tb.py') 
    workdir_tb_path = work_dir / Path(top_level_module + '_tb.py')   
    auto_tb_path = Path(os.environ['tools_dir']) / Path('utils/auto_tb.py')
    
    # Generate automatic testbench:
    if not homedir_tb_path.is_file():
        print(f'Note: Did not find an existing testbench in {homedir_tb_path}, generating an automatic one')
        with open(auto_tb_path, 'r') as file:
            tb_contents = 'work_dir = \"' + str(work_dir) + '\"\n'
            tb_contents += file.read()
    # Get existing testbench from verification directory:
    else:
        print(f'Note: Found existing testbench in {homedir_tb_path}, using this for simulation')
        # add verification directory to sys path in case there are some additional files in there:
        sys.path.insert(0, str(tb_dir.parent)) 
        tb_contents = 'import sys\n' 
        tb_contents += 'sys.path.append("' + str(homedir_tb_path.parent.parent) + '")\n'
        with open(homedir_tb_path, 'r') as file:
            tb_contents += file.read()
    
    # Write testbench to workdir
    with open(workdir_tb_path, 'w') as worktb_file:
        worktb_file.write(tb_contents)


# Add 'dump vcd file' section in design:
def _add_dump_vcd(work_dir: str, top_level_module: str) -> None:
    fl_path = Path(work_dir) / Path('design.fl')
    with open(fl_path, 'r') as file_list:
        for line in file_list:
            if top_level_module in line:
                top_level_path = Path(line.rstrip())
    if not top_level_path.is_file():
        _err('Top level module not found in ' + str(top_level_path))
    else:
        with open(top_level_path, 'r') as design:
            old = design.readlines() 
        with open(top_level_path, 'w') as design:
            for line in old:
                if 'endmodule' in line:
                    break
                else:
                    design.write(line)
            design.write('\ninitial begin\n   $dumpfile(\"dump.vcd\");\n   $dumpvars(1, ' + top_level_module + ');\nend\nendmodule') 

# Remove 'dump vcd file' section in design:
def _rem_dump_vcd(work_dir: str, top_level_module: str) -> None:
    fl_path = Path(work_dir) / Path('design.fl')
    with open(fl_path, 'r') as file_list:
        for line in file_list:
            if top_level_module in line:
                top_level_path = Path(line.rstrip())
    if not top_level_path.is_file():
        _err('Top level module not found in ' + str(top_level_path))
    else:
        with open(top_level_path, 'r') as design:
            old = design.readlines() 
        with open(top_level_path, 'w') as design:
            for line in old:
                if 'initial begin' in line:
                    break
                else:
                    design.write(line)
            design.write('endmodule')


# Run make command on shell
def _run_make(work_dir: str) -> None:
    current_dir = os.getcwd()
    os.chdir(work_dir)
    subprocess.run(['make'], shell=True)
    os.chdir(current_dir)

# wave:
def _wave(work_dir: str) -> None:
    found_vcd = False
    for child in Path(work_dir).iterdir():
        if child.is_file() and child.suffix=='.vcd':
            if found_vcd:
                print('More than one .vcd file in folder, took the first ignored the rest')
            else:
                found_vcd = True
                vcd_path = child
                print(vcd_path)
    if found_vcd:
        subprocess.run(['gtkwave', vcd_path, '&'])
    else:
        print('No vcd files found')

    
# Find top level module name for a specific view:
def _get_top_level(cfg: configparser, view: str):
    if view not in cfg:
        _err('view ' + view + ' not found in cfg file')
    else:
        if 'design' not in cfg[view]:
            _err('design section not found in view ' + view)
        else:
            design_content = cfg[view]['design'].split('\n')
            for line in design_content:
                line.replace(' ', '')
                if 'top' not in line:
                    continue
                elif '=' not in line:
                    _err('Top level module not defined in design section. Use this syntax:\n\ttop=top_level_module')
                else:
                    return line.split('=')[1]

# Recursivly search workspace path from some given start path
def _search_ws_path(start_path: Path) -> Path:
    if os.environ['home_dir'] not in str(start_path.parent):
        _err('You are currently not inside any workspace')
    p = start_path
    while (str(p.parent)) != os.environ['home_dir']:
        p = p.parent
    ws_path = p
    return ws_path

#################################
###                           ###
###  End of helper functions  ###
###                           ###
#################################

# 0. Parse Flags:
def parse_args():
    parser = argparse.ArgumentParser(description='Simulate a given view of any design')
    parser.add_argument('-w', '--workspace', type=str, action='store', dest='ws', help='Path to workspace', required=False)
    parser.add_argument('-c', '--cfg', type=str, action='store', dest='c', help='Path to configuration file', required=False)
    parser.add_argument('-v', '--view', type=str, action='store', dest='v', help='Desired view', required=True)
    parser.add_argument('--waves', action='store_true', dest='wave', help='Create waves')
    args = parser.parse_args()
    if len(sys.argv)==0:
        print(len(sys.argv))
        print(sys.argv)
        parser.print_help()
        exit(2)
    else:
        if not args.ws:
            if os.environ['home_dir'] not in str(Path.cwd()):
                _err('Workspace not provided and not under home directory')
            else:
                ws_path = _search_ws_path(Path.cwd().absolute())
        else:
            ws_path = Path(args.ws)
            if not ws_path.is_dir():
                _err('Workspace dir is invalid')
        if not args.c:
            cfg_dir, cfg_path = None, None
            if str(Path.cwd()).split('/')[-1]=='misc':
                cfg_dir = Path.cwd()
            else:
                for sub in os.walk(Path.cwd()):
                    if sub[0].split('/')[-1]=='misc':
                        cfg_dir = Path.cwd() / Path('misc')
            if not cfg_dir:
                _err('misc directory not found')
            else:
                for item in cfg_dir.iterdir():
                    if item.suffix=='.cfg':
                        cfg_path = Path(cfg_dir) / item
            if not cfg_path:
                _err('.cfg file not found in misc')
        else:
            cfg_path = Path(args.c)
            if cfg_path.suffix!='.cfg':
                _err('specified cfg path is invalid')
    return ws_path, cfg_path, args.v, args.wave

# 1. Generate Descriptor from Config File
def get_descriptor(cfg_path: Path, ws_path: str, view: str)-> Tuple[str, str, str, Path, Path, Path]:

    # Parse 'general' section in config
    cfg = configparser.ConfigParser()
    cfg.read(cfg_path)
    if 'general' not in cfg:
        _err('general section is a mandatory part of the configuration file')
    else:
        if 'block' not in cfg['general']:
            _err('general section must have a "block" key. Use this syntax:\n\tgeneral:\n\t\tblock=project_name/design/block_name')
        else:
            key = cfg['general'].get('block')

    # Parse key
    keys_list = key.split('/')
    if len(keys_list)!=3:
        _err('detected wrong syntax in "block" key in general section. Use this syntax:\n\tgeneral:\n\t\tblock=project_name/design/block_name')
    project_name, block_name = keys_list[0], keys_list[2]

    # Important directories
    rtl_dir   = ws_path / project_name / 'design'       / block_name / 'rtl'
    tb_dir    = ws_path / project_name / 'verification' / block_name / 'tests'
    work_dir  = Path(os.environ['work_dir']) / str(ws_path).split('/')[-1] / project_name / block_name
    work_dir.mkdir(parents=True, exist_ok=True) # Create output directory if needed

    top_level_module = _get_top_level(cfg, view)

    return project_name, block_name, top_level_module, rtl_dir, tb_dir, work_dir

# 2. Generates a file list
def get_list(ws_path: Path, cfg_path: Path, view: str, output_dir: str) -> None:
    file_list = _parse_cfg_rec(ws_path, cfg_path, view)
    for i in range(len(file_list)):
        file_list[i] = file_list[i].resolve()
    file_list = list(set(file_list))
    _gen_fl(output_dir, file_list)

# 3. Create test files: makefile and testbench
def create_test(tb_dir: Path, work_dir: Path, top_level_module: str, rtl_dir: Path) -> None:
    _make_make(work_dir, top_level_module)
    _gen_tb(tb_dir, work_dir, top_level_module)
    _get_portlist(rtl_dir, top_level_module, work_dir)

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
    get_list(ws_path, cfg_path, view, work_dir)
    # 3. Create test files: makefile and testbench
    create_test(tb_dir, work_dir, top_level_module, rtl_dir)
    # 4. Run simulation
    run_sim(work_dir, top_level_module, waves)

############################
###                      ###
### sim.py main function ###
###                      ###
############################

if __name__ == '__main__':
    main()
