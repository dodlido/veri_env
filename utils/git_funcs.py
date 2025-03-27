import requests
import git
import os
import json
from pathlib import Path
from typing import List
from utils.general import gen_err
from utils.general import gen_note
from git.exc import InvalidGitRepositoryError

# get a description of your github account
def _get_github_descriptor():
    # GitHub credentials and repository information
    github_username = os.environ['git_username']
    github_key_path = os.environ['git_key_path']
    github_url = f"https://api.github.com/users/{github_username}/repos"
    with open(github_key_path) as f:
        github_token = f.read().split('\n')[0]
    return github_url, github_token

# repository path
def _get_repo_path(repo_name: str) -> str:
    git_main_path = os.environ['git_main_path']
    return git_main_path + repo_name + '.git'

# get a list of github repositories
def _get_github_repositories() -> List[str]:
    
    url, token = _get_github_descriptor()
    
    # If authentication is needed (e.g., for private repos)
    headers = {}
    if token:
        headers['Authorization'] = f'token {token}'
    
    repos = []
    page = 1
    while True:
        # Fetch repositories (pagination is used if there are more than 30 repos)
        response = requests.get(url, headers=headers, params={'page': page, 'per_page': 100})
        
        if response.status_code != 200:
            gen_err(f"failed fetching repositories: {response.status_code}")
            break
        
        data = response.json()
        
        if not data:  # If no more repos are available
            break
        
        for repo in data:
            repos.append(repo['clone_url'])  # Add clone URL to the list
        
        page += 1  # Go to the next page
    
    return repos

# check whether repo is valid
def _is_valid_repo_path(repo_path):
    # Extract the part after the colon, which is in the form of userName/repoName.git
    try:
        # Strip the git@github.com: part and remove the .git extension
        repo_path = repo_path.split(':')[1].replace('.git', '')
        
        # Extract the username and repository name from the repo path
        username, repo_name = repo_path.split('/')
        
        # GitHub API URL to check the repository
        api_url = f"https://api.github.com/repos/{username}/{repo_name}"
        
        # Send a GET request to check if the repository exists
        response = requests.get(api_url)
        
        # If the response status code is 200, the repository exists
        if response.status_code == 200:
            return True
        # Return False if repository does not exist (status code 404)
        elif response.status_code == 404:
            return False
        else:
            # Handle other HTTP status codes (e.g., 403, 500, etc.)
            print(f"Unexpected status code {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

# check if CWD is within some valid git repository
def check_cwd_for_repo() -> None:
    try:
        git.Repo(search_parent_directories=True)  # search for a parent repo if not in the current dir
    except InvalidGitRepositoryError:
        gen_err('you are currently not within a valid git repository')

# show all valid repositories
def show_repos():
    message = 'available repositories:\n'
    repos = _get_github_repositories()
    for repo in repos:
        repo_name = repo.split('/')[-1].split('.')[0]
        message += f'{repo_name}\n'
    gen_note(message)
    exit(0)

# check alignment with remote master branch
def check_remote_alignment() -> None:
    repo = git.Repo(search_parent_directories=True)

    # Ensure we're checking the correct branches
    local_master = repo.heads.master  # Local 'master' branch
    remote_master = repo.remotes.origin.refs.master  # Remote 'origin/master' branch

    # Fetch the latest updates from the remote
    repo.remotes.origin.fetch()

    # Check if the local master is aligned with remote origin/master
    if local_master.commit != remote_master.commit:
        gen_err(f"remote's latest commit {remote_master.commit} is not aligned with local's {local_master.commit}")

# check if the repo is dirty
def check_dirty() -> None:
    repo = git.Repo(search_parent_directories=True)

    # Check for any changes in the repository
    if repo.is_dirty(untracked_files=True):  # Includes untracked files as well
        gen_err("there are changes to commit")

# clone a repository
def clone_repo(repo_name, dest_path):

    some_repo_path = _get_repo_path(repo_name)

    # validate repo path
    if not _is_valid_repo_path(some_repo_path):
        gen_err(f"the repository path {some_repo_path} is invalid or unreachable.")

    # validate destination path is not occupied
    if os.path.exists(dest_path):
        gen_err(f"the destination path {dest_path} already exists. Please provide a different location.")

    # clone the repo        
    try:
        # Try to clone the repository
        git.Repo.clone_from(some_repo_path, dest_path)
        gen_note(f"repository successfully cloned to {dest_path}")
    except git.exc.GitCommandError as e:
        gen_err(f"git error occurred: {e}")
    except Exception as e:
        gen_err(f"an unexpected error occurred: {e}")

# get repository name
def get_repo_name() -> str:
    repo = git.Repo(search_parent_directories=True)
    return  Path(repo.working_tree_dir).stem

# Function to create GitHub repository using GitHub API
def create_github_repository(repo_name):
    
    url, token = _get_github_descriptor()

    repo_path = _get_repo_path(repo_name)
    if _is_valid_repo_path(repo_path):
        gen_err(f'repo {repo_path} already exists')

    url = f'https://api.github.com/user/repos'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    payload = {
        'name': repo_name,
        'description': repo_name,
        'private': False 
    }
    
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        gen_note(f'repository {repo_name} created successfully on GitHub.')
    except requests.exceptions.RequestException as e:
        gen_err(f'failed to create repository: {e}')