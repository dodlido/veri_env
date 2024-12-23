import os
from pathlib import Path
import configparser
from typing import Tuple, List
from utils.general import gen_err
from utils.general import gen_validate_path

# parses a given section in a given configuration file. view name and keys are optional 
def _parse_sect(config: configparser, section_name: str, view_name: str=None, only_keys: bool=False, required=True)-> Tuple[List[str], List[str]]:
    keys, values = [], []

    # handle general sections placed outside of view scopes
    if not view_name:
        
        # exit if section is not in config file
        if section_name not in config:
            if required:
                gen_err(f'general section {section_name} was not found in configuration file', 2)    
            else:
                return keys, values
        
        section_content = config[section_name]

        # iterate over section contents
        for entry in section_content:
            key, value = entry, section_content.get(entry)
            if only_keys:
                keys.append(key)
            else:
                # check key=value syntax is correct
                if not value:
                    gen_err(f'syntax error in {entry} in view {view_name} in section {section_name}, please use the following syntax\n\tkey=value')
            
                # append to keys and values list
                keys.append(key)
                values.append(value)
        
    # handle sections that are view specific
    else:

        # exit if view does not exist
        if view_name not in config:
            gen_err(f'view {view_name} was not found in configuration file', 2)
    
        # exit if section does not exist
        if section_name not in config[view_name]:
            if required:
                gen_err(f'section {section_name} was not found in view {view_name}', 2)
            else:
                return keys, values

        section_content = config[view_name][section_name]
    
        # parse section content    
        section_content = section_content.split('\n')
        section_content = [s for s in section_content if s.strip()]
        section_content = [s.replace(' ', '') for s in section_content]

        # iterate over section contents
        for entry in section_content:
        
            if only_keys:
                keys.append(entry)
            else:
                # check key=value syntax is correct
                if entry.count('=')!=1:
                    gen_err(f'syntax error in {entry} in view {view_name} in section {section_name}, please use the following syntax\n\tkey=value')
            
                # append to keys and values list
                entry = entry.split('=')
                key, value = entry[0], entry[1]
                keys.append(key)
                values.append(value)

    return keys, values
    
# Parses 'file' under a given view and returns a list of files
def _get_files(config: configparser, view: str, cfg_path: Path) -> List[Path]:
    
    # parse files partial paths from configuration
    files, _ = _parse_sect(config, 'file', view ,True, True)
    
    # infer files full paths
    files_paths = []
    block_path = cfg_path.parent.parent
    for file in files:
        file_path = block_path / Path(file)
        gen_validate_path(file_path, 'build a filelist due to a missing file')
        files_paths.append(file_path)
    
    return files_paths

# Parses 'child' section in view and returns lists of child names, paths to cfgs and view names
def _get_children(config: configparser, view: str, child_names: List[str], child_paths: List[Path]) -> Tuple[List[str], List[Path], List[str]]:
    
    # parse 'child' section in configuration file
    new_names, new_views = _parse_sect(config, 'child', view, False, False)
    
    # locate paths in given path list
    new_paths = []
    for name in new_names:

        # exit if path not specified for that child
        if name not in child_names:
            gen_err(f'child {name} was not provided a path under "[path]"')

        # append path to new paths
        new_paths.append(child_paths[child_names.index(name)])

    return new_names, new_paths, new_views

# build child path 
def _get_child_cfg_path(ws_path: Path, child_name: str, child_type: str) -> Path:
    
    # check validity of child name
    if child_name.count('/')!=2:
        gen_err(f'syntax error in {child_name}, please use the following syntax\n\tPROJECT_NAME/design/BLOCK_NAME')

    # split name to usable values
    blk_name = child_name.split('/')[-1]
    project_name = child_name.split('/')[0]

    # handle local child type
    if 'local' in child_type: 
        cfg_path = ws_path / Path(project_name) / Path('design') / Path(blk_name) / Path('misc') / Path(blk_name + '.cfg')

    # handle release child type
    elif 'release' in child_type:

        # check child type validity
        if child_type.count(',')!=1:
            gen_err(f'syntax error in {child_type}, please provide release version like so:\n\t\release, x.y.z')
        
        # infer configuration path
        else:
            version = child_type.split(',')[-1].replace(' ', '')
            cfg_path = Path(os.environ['rls_dir']) / Path(project_name) / Path('v' + version) / Path('design') / Path(blk_name) / Path('misc') / Path(blk_name + '.cfg')
    
    # throw an error for any other child type
    else:
        gen_err(f'child type {child_type} is not supported yet', 2)
    
    # validate path
    gen_validate_path(cfg_path, f'find {child_name} configuration path', False)

    return cfg_path

# parses 'path' section and returns names and paths of valid childs
def _get_paths(ws_path: Path, config: configparser, cfg_path: Path) -> Tuple[List[str], List[Path]]:
    
    # parse 'path' section
    children, locations = _parse_sect(config, 'path', None, False, False)
    
    # infer path to children configuration paths
    paths = []
    for i, child in enumerate(children):
        paths.append(_get_child_cfg_path(ws_path, child, locations[i]))
        
    return children, paths

# get design values
def _get_design(cfg: configparser, view: str) -> str:
    
    # parse design section
    keys, values = _parse_sect(cfg, 'design', view, False, True)

    # handle top level definition
    for i, key in enumerate(keys):
        # found top key
        if 'top' in key:
            top_level_name = values[i]
            return top_level_name
    
    # throw an error if no top leve was found
    if not top_level_name:
        gen_err(f'top module definition was not found under "design" section, use the following syntax\n\ttop=TOP_MODULE_NAME', 2)
     
# parses through a config file, getting entire file list from all children
def parse_cfg_rec(ws_path: Path, cfg_path: Path, view: str, file_list: List[Path] = []) -> List[Path]:
    
    # read configuration file
    cfg = configparser.ConfigParser()
    cfg.read(cfg_path)

    # get children names paths and views
    names, paths = _get_paths(ws_path, cfg, cfg_path)
    names, paths, views = _get_children(cfg, view, names, paths)

    # exit condition, names list is empty
    if not names:
        # return current filelist + whatever is in 'file' section
        return file_list + _get_files(cfg, view, cfg_path) 
    
    # not done yet, go over children names and re-call recurssion
    else:
        for i,_ in enumerate(names):
            # for every children in list re-call this function
            file_list += parse_cfg_rec(ws_path, paths[i], views[i], file_list)
        
        return file_list + _get_files(cfg, view, cfg_path)
           
# generate descriptor from config file 'general' and 'design' sections
def get_descriptor(cfg_path: Path, ws_path: str, view: str)-> Tuple[str, str, str, Path, Path, Path]:

    # read configuration file
    cfg = configparser.ConfigParser()
    cfg.read(cfg_path)

    # parse 'general' section
    keys, values = _parse_sect(cfg, 'general', None, False, True)

    # check for 'block' definition under 'general'
    for i, key in enumerate(keys):
        # found top key
        if 'block' in key:
            block_value = values[i]

    # check validity of 'block' key
    if block_value.count('/')!=2:
        gen_err(f'syntax error in value ({block_value}) of "block" key under "general" section, please use the following syntax\n\tblock=project_name/design/block_name')

    block_value = block_value.split('/')
    project_name, block_name = block_value[0], block_value[2]

    # Important directories
    rtl_dir   = ws_path / project_name / 'design'       / block_name / 'rtl'
    tb_dir    = ws_path / project_name / 'verification' / block_name / 'tests'
    work_dir  = Path(os.environ['work_dir']) / str(ws_path).split('/')[-1] / project_name / block_name

    top_level_module_name = _get_design(cfg, view)

    return project_name, block_name, top_level_module_name, rtl_dir, tb_dir, work_dir