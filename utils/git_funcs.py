import requests
import git
import os
import socket
from utils.general import gen_err
from utils.general import gen_note

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
def get_github_repositories():
    
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
            print(f"Error fetching repositories: {response.status_code}")
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
    try:
        print(repo_path)
        host = repo_path.split('@')[1].split(':')[0]
        socket.create_connection((host, 80), timeout=10)  # Try to connect to the host (port 80 or 443)
        return True
    except socket.error:
        gen_err(f"unable to reach repository at {repo_path}")
        return False

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

# Function to create GitHub repository using GitHub API
def create_github_repository(repo_name):
    
    url, token = _get_github_descriptor()

    repo_path = _get_repo_path(repo_name)
    if _is_valid_repo_path(repo_path):
        gen_err(f'repo {repo_path} already exists')

    url = f'https://api.github.com/users/repos'
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
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print(f'Repository {repo_name} created successfully on GitHub.')
    except requests.exceptions.RequestException as e:
        print(f'Failed to create repository: {e}')
        return None