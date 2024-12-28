from pathlib import Path
import argparse
import sys
import os
import git
import re
import shutil
import stat
from datetime import datetime
from utils.general import gen_err
from utils.general import gen_note
from utils.git_funcs import get_repo_name
from utils.git_funcs import clone_repo
from utils.git_funcs import check_dirty
from utils.git_funcs import check_cwd_for_repo
from utils.git_funcs import check_remote_alignment

def parse_args():
    
    # release arguments
    parser = argparse.ArgumentParser(description='release creates a git tag in the remote repository and a local copy in your storage')
    parser.add_argument('-m', '--message', type=str, action='store', dest='m', help='Release message', required=False)
    parser.add_argument('-t', '--type', type=str, action='store', dest='t', help='Release type major/minor/standard, defaults to standard', required=False)

    # get arguments
    args = parser.parse_args(None if sys.argv[1:] else ['-h'])

    # check conditions for release are met
    check_cwd_for_repo() # check whether we are within a valid repository
    check_dirty() # check wheter there are any changes to commit
    check_remote_alignment() # check whether local is aligned with master
    
    return args.m, args.t

def get_new_tag(release_type: str) -> str:
    # Open the repository
    repo = git.Repo(search_parent_directories=True)

    # Get the latest tag
    tags = repo.tags

    # return first tag
    if not tags:
        if release_type=='major':
            return 'v1.0.0'
        elif release_type=='minor':
            return 'v0.0.1'
        else:
            return 'v0.1.0'
    
    # tag regex
    tag_pattern = r'^v(\d+)\.(\d+)\.(\d+)$'

    # find latest tag
    latest_tag = None
    latest_version = None
    for tag in tags:
        tag_name = tag.name
        match = re.match(tag_pattern, tag_name)
        
        if match:
            major, normal, minor = map(int, match.groups())
            version = (major, normal ,minor)

            if latest_version is None or version > latest_version:
                latest_tag = tag
                latest_version = version

    tag_name = latest_tag.name

    # Check if the tag matches the vX.Y.Z format
    
    match = re.match(tag_pattern, tag_name)
    if not match:
        gen_err(f"tag '{tag_name}' is not of the form 'vX.Y.Z'")

    # Extract the version numbers
    major, normal, minor = map(int, match.groups())

    # Update the version based on the release_type
    if release_type == "major":
        major += 1
        minor = 0  
        normal = 0
    elif release_type == "minor":
        minor += 1
    else: 
        normal += 1
        minor = 0 # Reset minor 

    # Construct the new tag name
    new_tag = f"v{major}.{normal}.{minor}"
    return new_tag

def update_footers(new_tag: str) -> None:
    new_footer = compose_footer(get_repo_name(), new_tag)
    repo = git.Repo(search_parent_directories=True)
    source_filelist = Path(repo.working_tree_dir).rglob('*.v')
    for file in source_filelist:
        remove_footer(file)
        add_footer(file, new_footer)

def gen_footer_line(lhs: str, rhs: str, border: bool=False, empty: bool=False) -> str:
    len_lhs, len_rhs = 15, 35
    len_tot = len_lhs + len_rhs
    start_key, end_key = '//|', '|//'
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
    author = os.environ['real_username']
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

def add_commit_push_n_tag(new_tag, message):
     # Open the repository
    repo = git.Repo(search_parent_directories=True)

    # Get the working directory
    working_dir = repo.working_tree_dir

    # Find all files with a '.v' suffix in the repository
    files_to_add = [os.path.join(root, file)
                    for root, _, files in os.walk(working_dir)
                    for file in files if file.endswith('.v')]

    # Add files to the staging area if there are any
    if files_to_add:
        repo.index.add(files_to_add)
        # Commit the changes with the provided message
        repo.index.commit(message)
        gen_note(f"updated source files footers and created a commit")

    # Create the new tag
    repo.create_tag(new_tag)
    gen_note(f"tag '{new_tag}' created")

    # Push changes and the new tag to the remote repository
    origin = repo.remotes.origin
    origin.push()  # Push commits if there are any
    origin.push(new_tag)  # Push the new tag

    gen_note(f"tag '{new_tag}' pushed to remote")

def store(new_tag: str) -> None:
    storage_base_path = Path(os.environ['rls_dir'])
    repo_name = get_repo_name()
    repo_path = storage_base_path / Path(repo_name)
    dest_path = repo_path / Path(new_tag)
    clone_repo(repo_name, dest_path)
    remove_git_repo_and_set_read_only(dest_path)

def remove_git_repo_and_set_read_only(repo_path):
    
    # Path to the .git directory
    git_dir = os.path.join(repo_path, '.git')

    # Check if the .git directory exists
    if os.path.isdir(git_dir):
        # Remove the .git directory (this effectively 'kills' the repository)
        shutil.rmtree(git_dir)
        gen_note(f"git repository removed from {repo_path}")
    else:
        gen_note(f"no .git directory found at {repo_path}, the repository is already removed")


    # Change all files and directories in the repository to read-only
    for root, dirs, files in os.walk(repo_path):
        # # First, handle directories (which need to be writable for os.walk to traverse)
        # for dir_name in dirs:
        #     full_path = os.path.join(root, dir_name)
        #     try:
        #         # Change directory permissions to read-only
        #         os.chmod(full_path, stat.S_IREAD)
        #     except PermissionError:
        #         continue
        
        # Now, handle files
        for file_name in files:
            full_path = os.path.join(root, file_name)
            try:
                # Change file permissions to read-only
                os.chmod(full_path, stat.S_IREAD)
            except PermissionError:
                continue
   
    gen_note(f"set read-only permission for all files under {repo_path}")

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
