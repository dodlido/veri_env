from pathlib import Path
from typing import Tuple, List, Dict
import argparse
import sys
import re
import subprocess

def validate_path(path_str: str, isfile: bool=True, exists: bool=True)->Path:
   if exists:
      if not Path(path_str).is_file() and isfile:
         print('Error, file path ' + path_str +' doesnt exists')
         exit(2)
      elif not Path(path_str).is_dir() and not isfile:
         print('Error, directory path ' + path_str +' doesnt exist')
         exit(2)
      else:
         return Path(path_str)
   else:
      if Path(path_str).is_file() and isfile:
         print('Error, file path ' + path_str +' already exists')
         exit(2)
      elif Path(path_str).is_dir() and not isfile:
         print('Error, directory path ' + path_str +' already exist')
         exit(2)
      else:
         return Path(path_str)

def parse_args() -> Tuple[Path, Path]:
    # Arguments parser definitions:
    parser = argparse.ArgumentParser(description='replace name')
    parser.add_argument('-m', '--module', type=str, action='store', dest='m', help='Name of the module you would like to instantiate'                , required=True)
    parser.add_argument('-d', '--dst'   , type=str, action='store', dest='d', help='Path to destination module in which source is to be instantiated', required=False)
    #parser.add_argument('-l', '--line'  , type=str, action='store', dest='l', help='Starting line to append the instance to as a string'             , required=True)

    # Parse Arguments:
    args = parser.parse_args(None if sys.argv[1:] else ['-h'])
   
    # Validate supplied flags:
    module_name = args.m
    if not args.d:
      dst_path = Path('enst_temp.v')
    else:
      dst_path = validate_path(args.d, isfile=True, exists=False)
    # line = args.l

    return module_name, dst_path # , line

def parse_port_declaration(port_declaration: str) -> tuple:
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
    header_regex = '^\s*//.*//\s*$'
    skip_regex = '^[^a-zA-Z]*$'
    comment_regex = '^\s*//.*$'
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
                port_direction, port_type, port_width, port_name, port_comment = parse_port_declaration(line)
                curr_dict['directions'].append(port_direction)
                curr_dict['types'].append(port_type)
                curr_dict['widths'].append(port_width)
                curr_dict['names'].append(port_name)
                curr_dict['comments'].append(port_comment)
               
    if curr_dict:
        interface.append(curr_dict)

    return interface

def get_inst(interface: List[Dict], module_name: str) -> str:
    inst = module_name + ' i_' + module_name + ' (\n'
    for dic in interface:
        inst += '   ' + dic["headline"] + '\n'
        for i, name in enumerate(dic["names"]):
            if dic["directions"][i] == 'input':
                direction = 'i'
            else:
                direction = 'o'
            type_ = dic["types"][i]
            width = dic["widths"][i].replace(' ', '')
            comment = dic["comments"][i].replace('/','').lstrip()
            inst += '   .' + name + ' (' + name + ') // ' + direction + ', ' + width + ' X ' + type_ + ' , ' + comment + '\n'
    inst += ');'
    return inst

def find_nth(haystack: str, needle: str, curr_max: int, n: int=1) -> int:
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    if start > curr_max:
        return start
    else:
        return curr_max

def align_inst(inst: str) -> str:
   
    # Constants and stuff
    lines = inst.split('\n') # no header and footer
    header, footer = lines[0], lines[-1]
    lines = lines[1:-1]
    aligned_inst = ''
    header_regex = '^\s*//.*//\s*$'
   
    delimiter_list = ['(', ')', 'X', ',', ',']
    sum = 0

    for delimiter in delimiter_list:
        max = 0
        # Find maximum occurance
        for line in lines:
            if re.match(header_regex, line):
                continue
            max = find_nth(line[sum:], delimiter, max)
   
        for i, line in enumerate(lines):
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

def append_inst(dst_path: Path, inst: str, dst_line: str):
    # Read the entire file into memory
    with dst_path.open('r') as file:
        lines = file.readlines()

    # Strip newline characters from dst_line to ensure no trailing \n interferes
    dst_line = dst_line.strip()

    # Replace the first line that matches dst_line with inst
    for i, line in enumerate(lines):
        if line.strip() == dst_line:  # Check if line matches dst_line (strip to ignore newlines)
            lines[i] = inst + '\n'  # Replace the matching line with inst
            break  # Exit after replacing the first match (optional: you can remove this to replace all occurrences)

    # Write the modified content back to the file
    with dst_path.open('w') as file:
        file.writelines(lines)  # Write the entire modified content back to the file

def get_src_path(module_name: str):
   subprocess.run(['python3', '/projects/tools/ML/MLSetup/2.18.0/getList.py', '-v', 'rtl', '-t', 'rtl', '-o', 'temp.txt', '--only-files', '--no-rocky'])
   with open('temp.txt', 'r') as f:
      for line in f:
         if module_name in line:
            src_path = Path(line.strip('\n'))
   if not src_path:
      print('Error: Module not found')
      exit(2)
   else:
      subprocess.run(['rm', 'temp.txt'])
      return src_path

def write_inst(dst_path: Path, inst: str)->None :
    # Write the entire string into file
    with dst_path.open('w') as f:
        f.write(inst)


def main():
    module_name, dst_path = parse_args()
    src_path = get_src_path(module_name)
    interface = get_if(src_path)
    inst = get_inst(interface, module_name)
    inst = align_inst(inst)
    # append_inst(dst_path, inst, line)
    write_inst(dst_path, inst)
   
if __name__ == '__main__':
    main()
