import subprocess
from pathlib import Path
from typing import List, Tuple
from utils.general import gen_err
from utils.general import gen_note
from utils.general import gen_validate_path
from utils.cfgparse import parse_cfg_rec


# Generates a .fl file list in the desired location
def _gen_fl(work_dir: Path, file_list: List[Path], results_names: List[str]=[], results_paths: List[str]=[]) -> Tuple[List[str], List[str]]:
    
    # write filelist to target location
    fl_path = work_dir / Path('design.fl')
    with open(fl_path, 'w') as fl:
        for file in file_list:
            fl.write(str(file)+'\n')
    
    gen_note(f'generated a file list at {fl_path}')

    results_names.append('filelist')
    results_paths.append(fl_path)
    
    return results_names, results_paths

# build defines file
def build_defines_file(defines_list: List[str], work_dir: Path, file_list: List[Path]) -> List[Path]:
    defines_path = work_dir / 'defs.v'
    with open(defines_path, 'w') as file:
        for define in defines_list:
            file.write(f'`define {define}\n')
    gen_note(f'generated a defines file in {defines_path}')
    file_list.insert(0, defines_path)
    return file_list

# build verilog register files
def build_verilog_rgfs(regs_list: List[Path], work_dir: Path, file_list: List[Path]) -> List[Path]:

    # create a regen directory within workdir if it does not exist
    rgfs_dir = work_dir / 'regen' 
    temp_path = rgfs_dir / 'temp_rgf.py'
    rgfs_dir.mkdir(parents=True, exist_ok=True)

    # for each RGF:
    for rgf_path in regs_list:
        
        # read RGF description from file
        with open(rgf_path, 'r') as rgf_file:
            rgf_content = rgf_file.read()
        
        # Add to RGF content a write to rgfs dir
        rgf_name = rgf_path.stem
        rgf_path = rgfs_dir / f'{rgf_name}.v'
        rgf_content += f'''
verilog = {rgf_name}.get_verilog()
with open('{rgf_path}', 'w') as verilog_file:
    verilog_file.write(verilog)
        '''

        # Write RGF content to temp.py
        with open(temp_path, 'w') as temp_file:
            temp_file.write(rgf_content)
        
        # Run temp.py
        try:
            subprocess.run(['python3', f'{temp_path}'])
        except:
            gen_err(f'failed to run {temp_path}')
        gen_note(f'generated verilog code for RGF {rgf_name} at {rgf_path}')
        
        # Append newly generated verilog to filelist
        file_list.append(rgf_path)

    return file_list

# Generates a file list
def getlist(ws_path: Path, cfg_path: Path, view: str, work_dir: Path, create_file: bool=False, results_names: List[str]=[], results_paths: List[str]=[]) -> Tuple[List[str], List[str]]:

    # generating a filelist is always first in line, create workdir
    work_dir.mkdir(parents=True, exist_ok=True)

    # get filelist
    file_list, defines_list, regs_list = parse_cfg_rec(ws_path, cfg_path, view, [], [], [])
    
    # resolve paths to full path version
    for i in range(len(file_list)):
        file_list[i] = file_list[i].resolve()

    # Create defines file and append it to filelist head
    file_list = build_defines_file(defines_list, work_dir, file_list)

    # Create verilog files from python descriptors
    file_list = build_verilog_rgfs(regs_list, work_dir, file_list)

    # remove duplicates
    seen = set()
    file_list = [x for x in file_list if not (x in seen or seen.add(x))]

    # Create filelist
    if create_file:
        results_names, results_paths = _gen_fl(work_dir, file_list, results_names, results_paths)
    
    return results_names, results_paths
