import os
from pathlib import Path
from typing import List, Tuple

# Print note to user
def gen_note(m: str) -> None:
    decorator = ''
    message = '\033[33mVERI-ENV NOTE:\033[0m ' + m
    print(decorator + message + decorator)

# Print error message and exit
def gen_err(m: str, code: int=1) -> None:
    
    message_header = '\033[31mVERI-ENV ERROR:\033[0m'
    length = len(m) + 4
    decorator = (length * '#')
    message_header = (f'# {message_header.ljust(length - 4 + 9)} #')
    message = (f'# {m.ljust(length - 4)} #')
    print(decorator)
    print(message_header)
    print(message)
    print(decorator)
    exit(code)

# Validate some path
def gen_validate_path(path: Path, what_failed: str='', is_dir: bool=False) -> None:
    if is_dir and not path.is_dir():
        gen_err(f'directory {path} does not exist, failed to {what_failed}')
    if not is_dir and not path.is_file():
        gen_err(f'file {path} does not exist, failed to {what_failed}')

# return path which is a parent of src_path and the first child of root
def gen_search_parent(src_path: Path, root: Path) -> Path:
    if root not in src_path.parents:
        gen_err(f'{root} not in {src_path}', 2)
    while src_path.parent != root:
        src_path = src_path.parent
    return src_path
    
# infer configuration path
def gen_find_cfg_file(given_cfg_path: Path=None, ws: str=None, project: str=None, block: str=None) -> Path:
    
    ### configuration path inferring process ###

    if given_cfg_path: # option 1 - config path specified 
        cfg_path = Path(given_cfg_path)
        gen_validate_path(cfg_path, 'locate provided configuration file')
    
    else: # option 2 - some form of the workspace-->project-->block triplet should have been specified or inferred
        # step 1 - infer workspace
        if not ws: # workspace was not provided --> we must be in one
            ws_path = gen_search_parent(Path.cwd().absolute(), Path(os.environ['home_dir']))
        elif ws=='show': # workspace 'show' option
            gen_show_ws()
        else: # workspace is provided
            ws_path = Path(ws)
            gen_validate_path(ws_path, 'locate provided workspace directory', True)
        # step 2 - infer project
        if not project: # project was not provided --> we must be in one
            project_path = gen_search_parent(Path.cwd().absolute(), ws_path)
        elif project=='show': # project 'show' option provided
            gen_show_proj(ws_path)
        else: # project is provided
            project_path = ws_path / project
            gen_validate_path(project_path, 'project path was not found', True)
        # step 3 - infer block
        if not block: # block not specified --> we must be in one
            block_path = gen_search_parent(Path.cwd().absolute(), (project_path / 'design'))
            gen_validate_path(block_path, 'block path was not found', True)
        elif block=='show': # block show chosen
            gen_show_blk(project_path)
        else: # block name is provided
            block_path = project_path / 'design' / block
        cfg_path = block_path / 'misc' / f'{block_path.stem}.cfg'
        gen_validate_path(cfg_path, 'locate inferred configuration path')

    return cfg_path

# show all valid workspaces
def gen_show_ws():
    home_path = Path(os.environ['home_dir'])
    message = 'available workspaces:\n'
    for child in home_path.iterdir():
        if child.is_dir():
            message += f'{child.stem}\n'
    gen_note(message)
    exit(0)

# show all projects under some workspace
def gen_show_proj(ws_path):
    message = 'available projects:\n'
    for proj in ws_path.iterdir():
        if proj.is_dir():
            message += f'{proj.stem}\n'
    gen_note(message)
    exit(0)

# show all blocks under some project
def gen_show_blk(proj_path):
    message = 'available blocks:\n'
    proj_path = proj_path / 'design'
    for blk in proj_path.iterdir():
        if blk.is_dir():
            message += f'{blk.stem}\n'
    gen_note(message)
    exit(0)

# print output log
def gen_outlog(names_list: List[str], paths_list: List[Path], header_content: str, failed: bool=False) -> None:
    # Check if both lists have the same length
    if len(names_list) != len(paths_list):
        raise ValueError("The length of names_list and paths_list must be the same.")
    
    # Define the ANSI escape codes for green color
    red = '\033[31m'
    green = '\033[32m'
    color = red if failed else green
    reset = '\033[0m'  # Reset to default color
    
    # Prepare the header and content
    header = header_content
    content = []
    max_name_length = len(header)  # Start with the length of the header
    max_path_length = 0  # Track the max path length
    line_num = 1

    for name, path in zip(names_list, paths_list):
        # Replace the tab with 4 spaces and store each part as separate lines
        name_line = f" {line_num}. {name} can be found here:"
        path_line = f"          {path}"  # Use 4 spaces instead of \t
        
        # Append to content
        content.append((name_line, path_line))
        
        # Update max lengths for name and path
        max_name_length = max(max_name_length, len(name_line))
        max_path_length = max(max_path_length, len(path_line))
        line_num += 1
    
    # Calculate the total width for the rectangle
    total_width = max(max_name_length, max_path_length) + 4  # Add padding and borders
    
    # Print the top border
    print('#' * total_width)
    
    # Print the header centered in the rectangle
    blank = ""
    print(f"#{blank.ljust(total_width - 2)}#")
    print(f"#{color}{header.center(total_width - 2)}{reset}#")
    print(f"#{blank.ljust(total_width - 2)}#")
    
    # Print each content line: name and path in separate lines
    for name_line, path_line in content:
        print(f"#{name_line.ljust(total_width - 2)}#")
        print(f"#{path_line.ljust(total_width - 2)}#")
        print(f"#{blank.ljust(total_width - 2)}#")
    
    # Print the bottom border
    print('#' * total_width)
    
# generate descriptor from config file 'general' and 'design' sections
def gen_get_descriptor(cfg_path: Path, view: str)-> Tuple[str, str, str, Path, Path, Path]:

    # infer ws, project, block triplet
    block_path = cfg_path.parent.parent
    project_path = block_path.parent.parent
    ws_path = project_path.parent
    block_name = block_path.stem
    project_name = project_path.stem
    
    # Important directories
    rtl_dir   = ws_path / project_name / 'design'       / block_name / 'rtl'
    tb_dir    = ws_path / project_name / 'verification' / block_name / 'tests'
    work_dir  = Path(os.environ['work_dir']) / str(ws_path).split('/')[-1] / project_name / block_name

    return ws_path, project_name, block_name, rtl_dir, tb_dir, work_dir