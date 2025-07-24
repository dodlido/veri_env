import os
import sys
import argparse
from pathlib import Path
from utils.general import gen_err
from utils.general import gen_note
from utils.general import gen_search_parent
from utils.general import gen_validate_path
from utils.general import gen_show_ws
from utils.general import gen_show_proj
from utils.general import gen_show_blk
from utils.general import gen_find_cfg_file
from utils.cfgparse import show_views

def parse_args():

    # get arguments
    parser = argparse.ArgumentParser(description='block.py : generates a block template in a given repository')
    parser.add_argument('-w', '--workspace', type=str, action='store', dest='ws', help='Path to workspace , not needed if within a workspace       , "show" to display options', required=False)
    parser.add_argument('-p', '--project', type=str, action='store', dest='p'   , help='Project name      , not needed if you are within a project , "show" to display options', required=False)
    parser.add_argument('-b', '--block-name', type=str, action='store', dest='b', help='Block name        , not needed if you are within a block   , "show" to display options', required=False)
    parser.add_argument('-t', '--type', type=str, action='store', dest='t'     , help='Block type, {design, verif, both}, defaults to "both"', required=False)

    # get arguments
    args = parser.parse_args(None if sys.argv[1:] else ['-h'])
    
    # parse workspace path
    if not args.ws:
        ws_path = gen_search_parent(Path.cwd().absolute(), Path(os.environ['home_dir']))
    elif args.ws=='show':
        gen_show_ws()
    else:
        ws_path = Path(args.ws)
        gen_validate_path(ws_path, 'locate provided workspace directory', True)
        
    # parse repo path
    if not args.p:
        proj_path = gen_search_parent(Path.cwd().absolute(), ws_path)
    elif args.p=='show':
        gen_show_proj(ws_path)
    else:
        proj_path = ws_path / Path(args.p)
        gen_validate_path(proj_path, f'locate project directory', True)
    
    # print available blocks in project
    if args.b=='show':
        gen_show_blk(proj_path)

    # parse block path
    if not args.b:
        gen_err('block name must be provided')
    block_path = proj_path / 'design' / args.b
    if block_path.is_dir():
        gen_err(f'path {block_path} is already occupied, did not override it')

    # verification / design:
    _type = 'both' if not args.t else args.t
    design = _type=='both' or _type=='design' 
    verif  = _type=='both' or _type=='verif' 
    
    return block_path, design, verif

def create_block_folders(block_path, design, verif):
    rtl_path = block_path / 'rtl'
    misc_path = block_path / 'misc'
    regs_path = block_path / 'regs'
    block_name = block_path.stem
    test_path = (block_path / f'../../verification/{block_name}/tests').resolve()
    if design:
        rtl_path.mkdir(parents=True, exist_ok=True) 
        misc_path.mkdir(parents=True, exist_ok=True) 
        regs_path.mkdir(parents=True, exist_ok=True) 
    if verif:
        test_path.mkdir(parents=True, exist_ok=True) 
    return test_path.parent

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

def create_regs_files(block_path, create_rgf: bool):
    env_path = block_path / '.env'
    env_content = os.environ['tools_dir']
    pbe_content = str(Path(os.environ['utils_dir']) / 'pbe')
    vscode_path = block_path / '.vscode'
    vscode_path.mkdir(parents=True, exist_ok=True) 
    json_path = vscode_path / 'settings.json'
    json_template_path = Path(env_content) / 'resources' / 'vscode_settings_template.json'
    with open(env_path, 'w') as env_file:
        env_file.write(env_content)
        env_file.write('\n')
        env_file.write(pbe_content)
    with open(json_template_path, 'r') as json_template_file:
        json_template = json_template_file.read()
    json_content = json_template.replace('{TOOLS_DIR}', env_content)
    json_content = json_content.replace('{PBE_DIR}', pbe_content)
    with open(json_path, 'w') as json_file:
        json_file.write(json_content)
    gen_note(f'wrote .env file at {env_path}')
    if create_rgf:
        block_name = block_path.stem
        rgf_path = block_path / 'regs' / f'{block_name}_rgf.py'
        with open(rgf_path, 'w') as rgf_file:
            rgf_file.write('import os\n')
            rgf_file.write('import sys\n')
            rgf_file.write('tools_dir = os.environ["tools_dir"]\n')
            rgf_file.write('sys.path.append(tools_dir)\n')
            rgf_file.write('from regen.reg_classes import *\n')

def main() -> None:
    # 0. Parse user arguments
    block_path, design, verif = parse_args()
    # 1. Create directories
    test_path = create_block_folders(block_path, design, verif)
    # 2. Create verilog, config and some other stuff
    if design:
        create_verilog_top(block_path)
        create_cfg_file(block_path)
        create_regs_files(block_path, True)
    if verif:
        create_regs_files(test_path, False)

if __name__ == '__main__':
    main()
