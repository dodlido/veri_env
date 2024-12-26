from pathlib import Path
from typing import List, Tuple
from utils.general import gen_err
from utils.general import gen_validate_path
from utils.cfgparse import parse_cfg_rec


# Generates a .fl file list in the desired location
def _gen_fl(work_dir: Path, file_list: List[Path], results_names: List[str]=[], results_paths: List[str]=[]) -> Tuple[List[str], List[str]]:
    
    # generating a filelist is always first in line, create workdir
    work_dir.mkdir(parents=True, exist_ok=True)
    
    # write filelist to target location
    fl_path = work_dir / Path('design.fl')
    with open(fl_path, 'w') as fl:
        for file in file_list:
            fl.write(str(file)+'\n')
    
    results_names.append('filelist')
    results_paths.append(fl_path)
    
    return results_names, results_paths

# Generates a file list
def getlist(ws_path: Path, cfg_path: Path, view: str, work_dir: Path, create_file: bool=False, results_names: List[str]=[], results_paths: List[str]=[]) -> Tuple[List[str], List[str]]:
    
    # get filelist
    file_list = parse_cfg_rec(ws_path, cfg_path, view)
    
    # resolve paths to full path version
    for i in range(len(file_list)):
        file_list[i] = file_list[i].resolve()
    
    # remove duplicates
    file_list = list(set(file_list))

    if create_file:
        results_names, results_paths = _gen_fl(work_dir, file_list, results_names, results_paths)
    
    return results_names, results_paths
