from pathlib import Path
from typing import List, Dict, Tuple
import re
import subprocess

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

def _parse_parameter_declaration(parameter_declaration: str) -> tuple:
    '''
    parses a verilog parameter declaration of one of the following forms:
    1. parameter <PARAM_NAME> = <PARAM_VALUE> , // <PARAM_COMMENT>
    2. parameter <PARAM_TYPE> <PARAM_NAME> = <PARAM_VALUE> , // <PARAM_COMMENT>
    3. parameter <PARAM_TYPE> [<PARAM_WIDTH>] <PARAM_NAME> = <PARAM_VALUE> , // <PARAM_COMMENT>
    notes:
    * each of the above forms can come with a comma between the "<PARAM_VALUE>" and "// <PARAM_COMMENT>" statements or without one
    * each of the above forms can come with any number of white spaces between any of the form parts
    The function returns the following tuple:
    {<PARAM_TYPE>: str, <PARAM_NAME>: str, <PARAM_WIDTH>: str, <PARAM_VALUE>: str, <PARAM_COMMENT>: str}
    '''
    # Regular expression pattern to match the given parameter declaration formats
    pattern = r"""
        \s*               # Optional leading white space
        parameter         # The keyword 'parameter'
        \s+               # At least one space
        (?P<type>\S+)?    # Optional parameter type (non-whitespace characters)
        \s*               # Optional spaces
        (\[?(?P<width>[\d:]+)?\]?)   # Optional width (digits or ranges, enclosed in square brackets)
        \s+               # At least one space
        (?P<name>\S+)     # Parameter name (non-whitespace characters)
        \s*               # Optional spaces
        =\s*              # Equals sign with optional spaces
        (?P<value>[\S\s]+?)  # Parameter value (non-whitespace characters, possibly including quotes or other chars)
        \s*               # Optional spaces
        (?:,?\s*//\s*(?P<comment>.*))?   # Optional comment after "//" (may have spaces and a comma before)
    """
    # Match the pattern to the input string using regex
    match = re.match(pattern, parameter_declaration, re.VERBOSE)
    
    if match:
        # Extract the captured groups, use empty string if a group was not matched
        param_type = match.group('type') or 'int'
        param_name = match.group('name') or ''
        param_width = match.group('width') or ''
        param_value = match.group('value') or 'none'
        param_comment = match.group('comment') or ''
        
        # Return as a tuple
        return (param_type, param_name, param_width, param_value, param_comment)
    else:
        raise ValueError(f"Invalid parameter declaration format: {parameter_declaration}")


def get_if(src_path: Path) -> List[Dict]:
    interface = []
    params_dict = dict(types=[], names=[], widths=[], values=[], comments=[])
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
            elif 'parameter' in line: # user parameters ==> parse
                param_type, param_name, param_width, param_value, param_comment = _parse_parameter_declaration(line)
                params_dict['types'].append(param_type)
                params_dict['names'].append(param_name)
                params_dict['widths'].append(param_width)
                params_dict['values'].append(param_value)
                params_dict['comments'].append(param_comment)
            elif 'localparam' in line: # local parameters ==> continue
                continue
            elif re.match(header_regex, line) and 'Parameter' not in line and 'parameter' not in line: # Found new header 
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

    return interface, params_dict 

def _get_inst(interface: List[Dict], module_name: str, params: dict) -> str:
    inst = f'{module_name} #(\n'
    for i, _ in enumerate(params['names']):
        last_param = ',' if i==len(params['names'])-1 else ' '
        inst += f'   .{params["names"][i]}({params["names"][i]}){last_param} // type: {params['types'][i]}, default: {params['values'][i]}, description: {params['comments'][i]}\n'
    inst += f') i_{module_name} (\n'
    for j, dic in enumerate(interface):
        inst += '   ' + dic["headline"] + '\n'
        for i, name in enumerate(dic["names"]):
            if dic["directions"][i] == 'input':
                direction = 'i'
            else:
                direction = 'o'
            type_ = dic["types"][i]
            width = dic["widths"][i].replace(' ', '')
            comment = dic["comments"][i].replace('/','').lstrip()
            # print(f'{j}/{len(interface)-1} ; {i}/{}')
            ket = ') // ' if (j==len(interface)-1) and (i==len(dic['names'])-1) else '), // '
            inst += '   .' + name + ' (' + name + ket + direction + ', ' + width + ' X ' + type_ + ' , ' + comment + '\n'
    inst += ');'
    return inst

def _find_nth(haystack: str, needle: str, curr_max: int, n: int=1) -> int:
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    if start > curr_max:
        return start
    else:
        return curr_max

def _align_inst(inst: str, module_name: str) -> str:
   
    # Constants and stuff
    lines = inst.split('\n') # no header and footer
    header, footer = lines[0], lines[-1]
    lines = lines[1:-1]
    aligned_inst = ''
    header_regex = r'^\s*//.*//\s*$'
   
    delimiter_list = ['(', ')', 'X', ',', ',']
    sum = 0
    

    for delimiter in delimiter_list:
        max = 0
        start = False
        # Find maximum occurance
        for line in lines:
            if f'i_{module_name}' in line:
                start = True
                continue
            elif not start and f'i_{module_name}' not in line:
                continue

            if re.match(header_regex, line):
                continue
            max = _find_nth(line[sum:], delimiter, max)
   
        start = False
        for i, line in enumerate(lines):
            if f'i_{module_name}' in line:
                start = True
                continue
            elif not start and f'i_{module_name}' not in line:
                continue

            if re.match(header_regex, line):
                continue
            idx = line[sum:].find(delimiter) + sum
            tempL = line[:idx]              
            tempR = line[idx:]
            tempL += ' ' * (max - idx + sum)
            lines[i] = tempL + tempR
       
        sum += max + 1
   
    aligned_inst += header + '\n'
    for line in lines:
        aligned_inst += line + '\n'
    aligned_inst += footer
    return aligned_inst

def get_inst(src_path: Path, src_module_name: str)->str:
    header = '''\n
// --------------------------------------------------------- //
// the below instance was generated automatically by enst.py //
\n'''
    footer = '''\n
// the above instance was generated automatically by enst.py //
// --------------------------------------------------------- //
\n'''
    _if, params = get_if(src_path)
    inst = _get_inst(_if, src_module_name, params)
    return header + _align_inst(inst, src_module_name) + footer
