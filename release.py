from pathlib import Path
from typing import List, Tuple
import configparser
import subprocess
import argparse
import sys
import os
import git
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser(description='release')
    parser.add_argument('-m', '--message', type=str, action='store', dest='m', help='Release message', required=False)
    parser.add_argument('-t', '--type', type=str, action='store', dest='t', help='Release type major/minor/standard, defaults to standard', required=False)
    args = parser.parse_args()
    if len(sys.argv)==0: # No flags supplied
        parser.print_help()
        exit(2)
    else:
        return args.m, args.t

def get_new_tag(release_type: str) -> str:
    repo = git.Repo(search_parent_directories=True)
    tags = repo.tags
    if (len(tags)==0): # No tags exist, first release
        new_tag = [0,0,0]
    else:
        new_tag = tags[-1].name.split('.')
        new_tag = [int(new_tag[0][1:]), int(new_tag[1]), int(new_tag[2])]
    if release_type=='minor':
        new_tag[2] += 1
    elif release_type=='major':
        new_tag[0] += 1
    else:
        new_tag[1] += 1
    return 'v' + str(new_tag[0]) + '.' + str(new_tag[1]) + '.' + str(new_tag[2])

def get_repo_name() -> str:
    repo = git.Repo(search_parent_directories=True)
    return  repo.working_tree_dir.split("\\")[-1]

def update_footers(new_tag: str) -> None:
    new_footer = compose_footer(get_repo_name(), new_tag)
    repo = git.Repo(search_parent_directories=True)
    for file in os.listdir(repo.working_tree_dir):
        filename = os.fsdecode(file)
        if filename.endswith(".v"):
            remove_footer(os.path.join(repo.working_tree_dir, filename))
            add_footer(os.path.join(repo.working_tree_dir, filename), new_footer)

def gen_footer_line(lhs: str, rhs: str, border: bool=False, empty: bool=False) -> str:
    len_lhs, len_rhs = 15, 35
    len_tot = len_lhs + len_rhs
    start_key, end_key = '//|', '|//'
    # line = start_key + lhs.ljust(len_lhs-len(lhs)-1, ' ') + ':' + rhs.ljust(len_rhs-len(rhs), ' ') + end_key + '\n'
    line = start_key + lhs.ljust(len_lhs - 2, ' ') + ':' + ('  ' + rhs).ljust(len_rhs - 2, ' ') + end_key + '\n'
    border_line = start_key.ljust(len_tot, '~') + end_key + '\n'
    empty_line = start_key.ljust(len_tot, ' ') + end_key + '\n'
    if border:
        return border_line
    elif empty:
        return empty_line
    else:
        return line

def compose_footer(repo_name: str, version: str) -> str:
    date = datetime.today().strftime('%Y-%m-%d')
    author = 'Etay Sela'
    new_footer  = gen_footer_line('','',border=True)
    new_footer += gen_footer_line('','',empty=True)
    new_footer += gen_footer_line(' 1. Project ', repo_name)
    new_footer += gen_footer_line(' 2. Author ', author)
    new_footer += gen_footer_line(' 3. Date ', date)
    new_footer += gen_footer_line(' 4. Version ', version)
    new_footer += gen_footer_line('','',empty=True)
    new_footer += gen_footer_line('','',border=True)
    return new_footer

def remove_footer(source_path: Path) -> None:
    border_line = gen_footer_line('','', border=True)
    with open(source_path, 'r') as source:
        old = source.readlines() 
    with open(source_path, 'w') as source:
        for line in old:
            if border_line==line:
                break
            else:
                source.write(line)

def add_footer(source_path: Path, new_footer: str) -> None:
    with open(source_path, 'r') as source:
        old = source.readlines() 
    if (old[-1] != '\n'):
        old.append('\n')
    with open(source_path, 'w') as source:
        for line in old:
            source.write(line)
        source.write(new_footer)

def add_commit_push_n_tag(new_tag: str, message: str) -> None:
    repo = git.Repo(search_parent_directories=True)
    repo.create_tag(new_tag, message=message)
    for file in os.listdir(repo.working_tree_dir):
        filename = os.fsdecode(file)
        if filename.endswith(".v"):
            repo.index.add([os.path.join(repo.working_tree_dir, filename)])
    repo.index.commit('Release pipe footers update')
    if message==None:
        message = 'Release ' + new_tag
    origin = repo.remote(name='origin')
    origin.push(new_tag)
    origin.push()
    return

def store(new_tag: str) -> None:
    storage_base_path = Path('D:/veri_strg')
    repo_name = get_repo_name()
    repo_path = storage_base_path / Path(repo_name)
    dest_path = repo_path / Path(new_tag)
    dest_path.mkdir(parents=True)
    git.Repo.clone_from('git@github.com:dodlido/' + repo_name + '.git', dest_path)
    return

# Usage: release.py -m <release message> --type <release type>
def main() -> None:
    # 0. Parse flags
    m, t = parse_args()
    # 1. Infer new tag name
    new_tag = get_new_tag(t)
    # 2. Update footers for .v files
    update_footers(new_tag)
    # 3. Add, commit, push and create tag
    add_commit_push_n_tag(new_tag, m)
    # 4. Clone repo to releases storage
    store(new_tag)

if __name__ == '__main__':
    main()