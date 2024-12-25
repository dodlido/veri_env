from pathlib import Path
from typing import List
from utils.general import gen_err
from utils.general import gen_validate_path
from utils.cfgparse import parse_cfg_rec


# Generates a .fl file list in the desired location
def _gen_fl(work_dir: Path, file_list: List[Path]) -> None:
    
    # make sure workdir exists
    gen_validate_path(work_dir, f'workdir {work_dir} does not exist', True)
    
    # write filelist to target location
    fl_path = work_dir / Path('design.fl')
    with open(fl_path, 'w') as fl:
        for file in file_list:
            fl.write(str(file)+'\n')

# Generates a file list
def getlist(ws_path: Path, cfg_path: Path, view: str, work_dir: Path, create_file: bool=False) -> None:
    
    # get filelist
    file_list = parse_cfg_rec(ws_path, cfg_path, view)
    
    # resolve paths to full path version
    for i in range(len(file_list)):
        file_list[i] = file_list[i].resolve()
    
    # remove duplicates
    file_list = list(set(file_list))

    if create_file:
        _gen_fl(work_dir, file_list)
