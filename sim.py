from pathlib import Path
from typing import List, Tuple
import configparser
import subprocess
import argparse
import sys

# Get home location
def _get_home(cfg_path: str) -> Path:
    full_cfg_path = Path.cwd() / cfg_path
    if not full_cfg_path.is_file():
        print('.cfg file not found')
    else:
        return full_cfg_path.parents[1]

# Parses 'path' section and returns names and paths of valid childs
def _get_paths(config: configparser, cfg_path: str) -> Tuple[List[str], List[Path]]:
    names, paths = [], []
    if 'path' in config:
        for key in config['path']:
            val = config['path'].get(key)
            val = val.replace(' ', '')
            if ',' not in val:
                print('Delimiter (comma) not found, please provide both child type and path')
                continue
            else:
                val = val.split(',')
                if len(val) != 2:
                    print('Too many (or not enough) values provided, please provide type and path seperated by a comma')
                    continue
                else:
                    val_type, val_path = val[0], _get_home(cfg_path) / Path(val[1])
                    val_path = val_path / 'misc'
                    if val_type != 'local': 
                        print('This type is not supported yet')
                        continue
                    else:
                        if not val_path.is_dir():
                            print('Path does not exist or does not have a misc sub-directory, please provide a valid path')
                            print(val_path)
                            continue
                        else:
                            found_cfg = False
                            for f in val_path.iterdir():
                                if f.suffix == '.cfg' and not found_cfg:
                                    paths.append(f)
                                    names.append(key)
                                    found_cfg = True
                                elif f.suffix == '.cfg' and found_cfg:
                                    print('More than one .cfg files in directory, this is not supported, taking the first one found')
                            if not found_cfg:
                                print('.cfg file not found in directory')
    return names, paths
        
# Parses 'child' under given view and returns a list of views
def _get_children(config: configparser, view: str, cfg_path: str, child_names: List[str], child_paths: List[Path]) -> Tuple[List[str], List[Path], List[str]]:
    children, paths, views = [], [], []
    if view in config:
        if 'child' in config[view]:
            child_content = config[view]['child'].split('\n')
            for child in child_content:
                child.replace(' ', '')
                if child == '':
                    continue
                else:
                    if '=' not in child:
                        print('Delimiter not found, please use equal sign to seperate between child name and view')
                    elif (len(child.split('=')) != 2):
                        print('Too many delimiters, please use a single one to seperate between child name and view')
                    else:
                        child_name, child_view = child.split('=')[0], child.split('=')[1]
                        if child_name not in child_names:
                            print('Child not found in path section, please specify where to locate this child')
                        else:
                            children.append(child_name)
                            paths.append(child_paths[child_names.index(child_name)])
                            views.append(child_view)
    else:
        print('Error: view not found')
    return children, paths, views

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
                    f_path = _get_home(cfg_path) / Path(f)
                    if f_path.is_file():
                        files.append(f_path)
                    else:
                        print('File does not exist')
                        print(f_path)
        else:
            print("No file key in provided view")
    else:
        print('Provided view was not found in .cfg file')
    return files

# Parses through a config file, getting entire file list from all children
def _parse_cfg_rec(path: Path, view: str, file_list: List[Path] = []) -> List[Path]:
    cfg = configparser.ConfigParser()
    cfg.read(path)
    names, paths = _get_paths(cfg, path)
    children, paths, views = _get_children(cfg, view, path, names, paths)
    if not children:
        return file_list + _get_files(cfg, view, path)
    else:
        for i,c in enumerate(children):
            file_list += _parse_cfg_rec(paths[i], views[i], file_list)
            file_list += _get_files(cfg, view, path)
        return file_list

# Generates a .fl file list in the desired location
def _gen_fl(fl_dir: str, file_list: List[Path]) -> None:
    if not Path(fl_dir).is_dir():
        print('Not a valid output directory, try again')
        return
    else:
        fl_path = fl_dir / Path('design.fl')
        with open(fl_path, 'w') as fl:
            for file in file_list:
                fl.write(str(file)+'\n')

# Generates a file list
def _get_list(cfg_path: str, view: str, output_dir: str) -> None:
    file_list = list(set(_parse_cfg_rec(cfg_path, view)))
    _gen_fl(output_dir, file_list)

# pre-run:
def _pre_run(output_dir: str) -> None:
    subprocess.run(['iverilog', '-o', output_dir+'/design.cmp', '-c', output_dir+'/design.fl'])

# run:
def _run(output_dir: str) -> None:
    subprocess.run(['vvp', output_dir+'/design.cmp'])

# wave:
def _wave(output_dir: str) -> None:
    found_vcd = False
    for child in Path(output_dir):
        if child.is_file() and child.suffix=='.vcd':
            if found_vcd:
                print('More than one .vcd file in folder, took the first ignored the rest')
            else:
                found_vcd = True
                vcd_path = child
    subprocess.run(['gtkwave', str(vcd_path), '&'])

# mkdir:
def _mkdir(output_dir: str) -> None:
    if not Path(output_dir).is_dir():
        Path(output_dir).mkdir()

# parse flags:
def _parse_args():
    parser = argparse.ArgumentParser(description='sim')
    parser.add_argument('-c', '--cfg', type=str, action='store', dest='c', help='Path to configuration file')
    parser.add_argument('-v', '--view', type=str, action='store', dest='v', help='Desired view')
    parser.add_argument('-o', '--out', type=str, action='store', dest='o', help='Output directory')
    parser.add_argument('--pre-run', action='store_true', dest='p', help='Perform pre-run')
    parser.add_argument('--run', action='store_true', dest='r', help='Perform run')
    parser.add_argument('--waves', action='store_true', dest='w', help='Create waves')
    args = parser.parse_args()
    if not len(sys.argv)==10:
        print(len(sys.argv))
        parser.print_help()
        exit(2)
    else:
        return args.c, args.v, args.o, args.p, args.r, args.w 

# sim main function:
def main() -> None:
    cfg_path, view, output_dir, pre_run, run, waves = _parse_args()
    _mkdir(output_dir)
    _get_list(cfg_path, view, output_dir)
    if pre_run:
        _pre_run(output_dir)
    if run:
        _run(output_dir)
    if waves:
        _wave(output_dir)

if __name__ == '__main__':
    main()