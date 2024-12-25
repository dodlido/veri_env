import os
from pathlib import Path
from typing import List

# Print note to user
def gen_note(m: str) -> None:
    decorator = ''
    message = 'VERI-ENV NOTE: ' + m
    print(decorator + message + decorator)

# Print error message and exit
def gen_err(m: str, code: int=1) -> None:
    decorator = '\n##########################################################################################\n'
    message = 'VERI-ENV ERROR:\n' + m
    print(decorator + message + decorator)
    exit(code)

# Validate some path
def gen_validate_path(path: Path, what_failed: str='', is_dir: bool=False) -> None:
    if is_dir and not path.is_dir():
        gen_err(f'directory {path} does not exist, failed to {what_failed}')
    if not is_dir and not path.is_file():
        gen_err(f'file {path} does not exist, failed to {what_failed}')

# Recursivly search workspace path from some given start path
def gen_search_ws_path(start_path: Path) -> Path:
    if os.environ['home_dir'] not in str(start_path.parent):
        gen_err('You are currently not inside any workspace', 2)
    p = start_path
    while (str(p.parent)) != os.environ['home_dir']:
        p = p.parent
    ws_path = p
    return ws_path

def gen_outlog(names_list: List[str], paths_list: List[Path]) -> None:
    # Check if both lists have the same length
    if len(names_list) != len(paths_list):
        raise ValueError("The length of names_list and paths_list must be the same.")
    
    # Define the ANSI escape codes for green color
    green = '\033[32m'
    reset = '\033[0m'  # Reset to default color
    
    # Prepare the header and content
    header = "Simulation Done!!! Results:"
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
    print(f"#{green}{header.center(total_width - 2)}{reset}#")
    print(f"#{blank.ljust(total_width - 2)}#")
    
    # Print each content line: name and path in separate lines
    for name_line, path_line in content:
        print(f"#{name_line.ljust(total_width - 2)}#")
        print(f"#{path_line.ljust(total_width - 2)}#")
        print(f"#{blank.ljust(total_width - 2)}#")
    
    # Print the bottom border
    print('#' * total_width)
    