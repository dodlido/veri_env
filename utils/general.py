import os
from pathlib import Path

# Print note to user
def gen_note(m: str) -> None:
    decorator = ''
    message = 'VERI-ENV NOTE:' + m
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