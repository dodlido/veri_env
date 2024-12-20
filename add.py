import git
import argparse
import os
import sys
from pathlib import Path
import subprocess
import sys
import os
import requests
import subprocess

# GitHub credentials and repository information
github_username = os.environ['git_username']
github_key_path = os.environ['git_key_path']

def get_api_token():
    with open(github_key_path) as f:
        key = f.read().split('\n')[0]
    return key

# Function to create GitHub repository using GitHub API
def create_github_repository(repo_name):
    github_token = get_api_token() 
    url = f'https://api.github.com/user/repos'
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    payload = {
        'name': repo_name,
        'description': repo_name,
        'private': False 
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print(f'Repository {repo_name} created successfully on GitHub.')
    except requests.exceptions.RequestException as e:
        print(f'Failed to create repository: {e}')
        return None

# Function to push local repository to GitHub
def push_to_github(repo_path, repo_name):
    # Change directory to the specified local repository
    os.chdir(repo_path)
    
    subprocess.run(['git init'], shell=True)
    subprocess.run(['git add .'], shell=True)
    subprocess.run(['git commit -m \'new repo\''], shell=True)
    
    # Add GitHub repository as remote
    remote_url = f'https://github.com/{github_username}/{repo_name}.git'
    try:
        subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True)
        print(f'Added remote repository {remote_url} successfully.')
    except subprocess.CalledProcessError as e:
        print(f'Failed to add remote repository: {e}')
        return
    
    # Push local repository to GitHub
    try:
        subprocess.run(['git', 'push', '-u', 'origin', 'master'], check=True)
        print('Pushed local repository to GitHub.')
    except subprocess.CalledProcessError as e:
        print(f'Failed to push to GitHub: {e}')

def _err(m):
    print('Error: ' + m)
    exit(2)

def parse_args():
    parser = argparse.ArgumentParser(description='get repo\n Usage: add.py -r <repo_name>\nDefaults to pre-defined WS path')
    parser.add_argument('-r', '--repo', type=str, action='store', dest='r', help='Repository to get', required=True)
    args = parser.parse_args()
    if len(sys.argv)==0: # No flags supplied
        parser.print_help()
        exit(2)
    else:
        return args.r

def create_local_repo(repo_name):
    subprocess.run([str('mkdir ' + repo_name)], shell=True)
    subprocess.run([str('cd ' + repo_name)], shell=True)
    subprocess.run(['mkdir ' + repo_name + '/rtl'], shell=True)
    subprocess.run(['mkdir ' + repo_name + '/misc'], shell=True)
    subprocess.run(['touch ' + repo_name + '/rtl/.keepdir'], shell=True)
    subprocess.run(['touch ' + repo_name + '/misc/.keepdir'], shell=True)

# Usage: add.py -r <repo name> 
def main() -> None:
    # 0. Parse flags
    repo_name = parse_args()
    # 1. Create remote repo
    create_github_repository(repo_name)

    # Provision: 
    # 2. Make repo skeleton locally
    # create_local_repo(repo_name)
    # 3. Push local to remote
    # push_to_github(os.getcwd() + '/' + repo_name, repo_name)

if __name__ == '__main__':
    main()
