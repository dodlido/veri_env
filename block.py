import os
import sys
import argparse
from pathlib import Path
from utils.general import gen_err
from utils.general import gen_note
from utils.general import gen_search_parent
from utils.general import gen_validate_path

def parse_args():

    # get arguments
    parser = argparse.ArgumentParser(description='block.py : generates a block template in a given repository')
    parser.add_argument('-w', '--user-ws', type=str, action='store', dest='w', help='User specified work-space path', required=False)
    parser.add_argument('-r', '--repo', type=str, action='store', dest='r', help='Repository to get', required=False)
    parser.add_argument('-b', '--block-name', type=str, action='store', dest='b', help='Block name', required=True)

    # get arguments
    args = parser.parse_args(None if sys.argv[1:] else ['-h'])
    
    # parse workspace path
    if not args.w:
        ws_path = gen_search_parent(Path.cwd().absolute(), Path(os.environ['home_dir']))
    else:
        ws_path = Path(args.w)
        gen_validate_path(ws_path, 'locate provided workspace directory', True)
        
    # parse repo path
    if not args.r:
        proj_path = gen_search_parent(Path.cwd().absolute(), ws_path)
    else:
        proj_path = ws_path / Path(args.r)
        gen_validate_path(proj_path, f'locate project directory', True)
    
    block_path = proj_path / 'design' / args.b
    if block_path.is_dir():
        gen_err(f'path {block_path} is already occupied, did not override it')
    
    return block_path

def create_block_folders(block_path):
    rtl_path = block_path / 'rtl'
    misc_path = block_path / 'misc'
    rtl_path.mkdir(parents=True, exist_ok=True) 
    misc_path.mkdir(parents=True, exist_ok=True) 

def create_verilog_top(block_path):
       
    template_path = Path(os.environ['tools_dir']) / 'resources/verilog_src_file_template.v'
    gen_validate_path(template_path, 'locate verilog source template in resources folder')
    with open(template_path, 'r') as file:
        template = file.read()
    
    block_name = block_path.stem
    src = template.replace('{MODULE_NAME}', block_name)

    src_path = block_path / 'rtl' / f'{block_name}_top.v'
    with open(src_path, 'w') as file:
        file.write(src)
    
    gen_note(f'created a top leve verilog source file in {src_path}')

def create_cfg_file(block_path):

    template_path = Path(os.environ['tools_dir']) / 'resources/cfg_template.cfg'
    gen_validate_path(template_path, 'locate verilog source template in resources folder')
    with open(template_path, 'r') as file:
        template = file.read()
    
    block_name = block_path.stem
    proj_name = block_path.parent.parent.stem
    cfg = template.replace('{PROJ_NAME}', proj_name)
    cfg = cfg.replace('{BLOCK_NAME}', block_name)

    cfg_path = block_path / 'misc' / f'{block_name}.cfg'
    with open(cfg_path, 'w') as file:
        file.write(cfg)
    
    gen_note(f'created a block configuration file in {cfg_path}')

def main() -> None:
    # 0. Parse user arguments
    block_path = parse_args()
    # 1. Create directories
    create_block_folders(block_path)
    # 2. Create verilog and config 
    create_verilog_top(block_path)
    create_cfg_file(block_path)

if __name__ == '__main__':
    main()