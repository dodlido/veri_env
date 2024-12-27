import os
from pathlib import Path
from typing import List

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
    
# Recursivly search configuration file from some given start path
def gen_find_cfg_file(start_path: Path) -> Path:
    ws_path = gen_search_parent(start_path, Path(os.environ['home_dir']))
    block_path = gen_search_parent(start_path, ws_path)
    block_name = block_path.stem
    cfg_path = block_path / Path(f'misc/{block_name}.cfg')
    gen_validate_path(cfg_path, f'loctae configuration file of block {block_name}')
    return cfg_path

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
    