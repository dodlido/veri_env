from pathlib import Path
from typing import List, Tuple
import configparser
import subprocess
import argparse
import sys
import os

# Print error message and exit
def _err(m: str) -> None:
    print('Error: ' + m)
    exit(2)

# Build child path 
def _get_child_cfg_path(ws_path: Path, child_name: str, child_type: str, papa_cfg_path: Path) -> Path:
    blk_name = child_name.split('/')[-1]
    repo_name = child_name.split('/')[0]
    if child_type=='local':
        cfg_path = ws_path / Path(child_name) / Path('misc') / Path(blk_name + '.cfg')
    elif child_type=='project':
        cfg_path = papa_cfg_path.parent.parent.parent / Path(blk_name) / Path('misc') / Path(blk_name + '.cfg')
    elif 'release' in child_type:
        if ',' not in child_type:
            _err('Syntax error in ' + child_type + 'provide release version in a \'release, x.y.z\' format')
            if len(child_type.split(','))!=2:
                _err('Syntax error in ' + child_type + 'provide release version in a \'release, x.y.z\' format')
        else:
            version = child_type.split(',')[-1].replace(' ', '')
            cfg_path = Path('/home/etay-sela/design/veri_strg') / Path(repo_name) / Path('v' + version) / Path('design') / Path(blk_name) / Path('misc') / Path(blk_name + '.cfg')
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

# Find top level module name for a specific view:
def _get_top_level(cfg_path: Path, view: str):
    if not cfg_path.is_file():
        _err('.cfg file not found in: ' + str(cfg_path))
    else:
        cfg = configparser.ConfigParser()
        cfg.read(cfg_path)
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
                        _err('Top level module not defined in design section')
                    else:
                        return line.split('=')[1]

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
def _make_make(out_dir: str, top_level_name: str) -> None:
    fl_path = Path(out_dir) / Path('design.fl')
    make_path = Path(out_dir) / Path('makefile')
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
            makefile.write('\nTOPLEVEL = ' + top_level_name + '\n\n')
            makefile.write('MODULE = ' + top_level_name + '_tb\n\n')
            makefile.write('include $(shell cocotb-config --makefiles)/Makefile.sim')

# Generates a generic testbench
def _gen_tb(out_dir: str, top_level_name: str) -> None:
    tb_path = Path(out_dir) / Path(top_level_name + '_tb.py') 
    with open(tb_path, 'w') as tb_file:
        tb_file.write('import cocotb\nfrom cocotb.triggers import FallingEdge, Timer, RisingEdge\nfrom cocotb.clock import Clock\n\n')
        tb_file.write('@cocotb.test()\nasync def my_test(dut):\n   cocotb.start_soon(Clock(dut.clk, 1, units="ns").start())\n')
        tb_file.write('   for _ in range(10):\n      await RisingEdge(dut.clk)') # Placeholder

# Add 'dump vcd file' section in design:
def _add_dump_vcd(out_dir: str, top_level_name: str) -> None:
    fl_path = Path(out_dir) / Path('design.fl')
    with open(fl_path, 'r') as file_list:
        for line in file_list:
            if top_level_name in line:
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
            design.write('\ninitial begin\n   $dumpfile(\"dump.vcd\");\n   $dumpvars(1, ' + top_level_name + ');\nend\nendmodule') 

# Remove 'dump vcd file' section in design:
def _rem_dump_vcd(out_dir: str, top_level_name: str) -> None:
    fl_path = Path(out_dir) / Path('design.fl')
    with open(fl_path, 'r') as file_list:
        for line in file_list:
            if top_level_name in line:
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

# Generates a file list
def _get_list(ws_path: Path, cfg_path: Path, view: str, output_dir: str) -> None:
    file_list = _parse_cfg_rec(ws_path, cfg_path, view)
    for i in range(len(file_list)):
        file_list[i] = file_list[i].resolve()
    file_list = list(set(file_list))
    _gen_fl(output_dir, file_list)

# Run make command on shell
def _run_make(output_dir: str) -> None:
    current_dir = os.getcwd()
    os.chdir(output_dir)
    subprocess.run(['make'], shell=True)
    os.chdir(current_dir)

# wave:
def _wave(output_dir: str) -> None:
    found_vcd = False
    for child in Path(output_dir).iterdir():
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

# mkdir:
def _create_output_dir(ws_path: Path, cfg_path: Path) -> None:
    blk_name = str(cfg_path.parent.parent).split('/')[-1]
    repo_name = str(cfg_path.parent.parent.parent.parent).split('/')[-1]
    ws_name = str(ws_path).split('/')[-1]
    output_dir = Path('/home/etay-sela/design/veri_work') / ws_name / repo_name / blk_name
    # output_dir = ws_path / Path('sim') / repo_name / blk_name
    output_dir.mkdir(parents=True, exist_ok=True) # Create output directory if needed
    return output_dir

# parse flags:
def _parse_args():
    parser = argparse.ArgumentParser(description='sim')
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
            if 'home' not in str(Path.cwd()):
                _err('Workspace not provided and not under home directory')
            else:
                p = Path.cwd().absolute()
                while (str(p.parent)).split('/')[-1] != 'veri_home':
                    p = p.parent
                ws_path = p
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

# sim main function:
def main() -> None:
    ws_path, cfg_path, view, waves = _parse_args()
    output_dir = _create_output_dir(ws_path, cfg_path)
    _get_list(ws_path, cfg_path, view, output_dir)
    top_level_name = _get_top_level(cfg_path, view)
    _make_make(output_dir, top_level_name)
    _gen_tb(output_dir, top_level_name)
    _add_dump_vcd(output_dir, top_level_name)
    _run_make(output_dir)
    if waves:
        _wave(output_dir)
    _rem_dump_vcd(output_dir, top_level_name)

if __name__ == '__main__':
    main()