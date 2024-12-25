from pathlib import Path
from typing import List, Dict, Tuple
import re

def _parse_port_declaration(port_declaration: str) -> tuple:
    # Updated regex pattern to capture types with package qualifiers and handle comments with commas
    pattern = r'^\s*(input|output|inout)\s+([a-zA-Z0-9_::]+)\s*((\[[^\]]*\])*)\s+([a-zA-Z0-9_]+)\s*(,)?\s*(//.*)?\s*$'
   
    # Match the input string against the regex pattern
    match = re.match(pattern, port_declaration.strip())
   
    if match:
        direction = match.group(1)  # Direction of the port (input, output, inout)
        type_ = match.group(2)      # Type of the port (e.g., vmrg_pckg::erim)
       
        # Handle the multi-dimensional width part (captures all the [ ] parts)
        width_parts = match.group(3)  # Capture all the [ ] parts
        name = match.group(5)         # Name of the port (group 5)
        comment = match.group(7) or ''  # Comment, empty if not present
       
        # Clean up the comment (strip the "//" if present)
        comment = comment.strip()[2:].strip() if comment else ''  # Remove leading "//" and any extra spaces
       
        # Parse the width dimensions: extract all occurrences of [something]
        width_dimensions = re.findall(r'\[([^\]]+)\]', width_parts)
       
        # If there are any width dimensions, construct the width string
        if width_dimensions:
            # Join the dimensions with '*' to represent multiplication
            width = '*'.join(width_dimensions)
        else:
            # If no width is specified, default to '[1]'
            width = '[1]'
       
        # Now, remove any occurrences of the pattern that matches "- 1 : 0"
        width = re.sub(r'-\s*1\s*:\s*0', '', width)
       
        return (direction, type_, width, name, comment.replace(',','.'))
   
    else:
        raise ValueError("Invalid port declaration format:\n" + port_declaration)

def get_if(src_path: Path) -> List[Dict]:
    interface = []
    start_flag = False
    break_point = ');'
    header_regex = r'^\s*//.*//\s*$'
    skip_regex = r'^[^a-zA-Z]*$'
    comment_regex = r'^\s*//.*$'
    curr_dict = None
    with open(str(src_path), 'r') as src:
        for line in src:
            if not start_flag:
                if 'module' in line and '//' not in line:
                    start_flag = True
                    continue
                else:
                    continue
            if break_point in line: # Found break point, end of module port list
                break
            elif re.match(skip_regex, line): # No characters ==> skip this line
                continue
            elif re.match(header_regex, line) and 'arameter' not in line: # Found new header # TODO: this "arameter" is here to temporarly skip parameters
                if curr_dict: # Previously assembled dict has ended here
                    interface.append(curr_dict)
                curr_dict = dict(headline=line.lstrip('\t').rstrip('\n'), directions=[], types=[], widths=[], names=[], comments=[])
            elif not curr_dict: # No dictionary started yet, skip this
                continue
            elif re.match(comment_regex, line):
                continue
            else: # probably a port, append to current dict
                port_direction, port_type, port_width, port_name, port_comment = _parse_port_declaration(line)
                curr_dict['directions'].append(port_direction)
                curr_dict['types'].append(port_type)
                curr_dict['widths'].append(port_width)
                curr_dict['names'].append(port_name)
                curr_dict['comments'].append(port_comment)
               
    if curr_dict:
        interface.append(curr_dict)

    return interface