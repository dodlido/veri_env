
################################################
### Manual edit of active script starts here ###
################################################
# Your github info #
export git_username="git_username"
export git_main_path="git@github.com:git_username/"
export git_key_path="path_to_api_key"
export git_ssh_key_path="path_to_private_ssh_key" # Path to your own private ssh key
export git_ssh_key_passphrase="pass_phrase" # Passphrase to your own private ssh key
# Your name #
export real_username="some_name_to_autograph_releases_with"
# Paths to your personal storage #
export setup_path="" # Path to this file
export rls_dir=   "" # Directory to store releases in
export home_dir=  "" # Directory to develop in 
export work_dir=  "" # Directory to see simulation results in
export utils_dir= "" # Directory to my_defs.sh, and tools, py_venv folders
export venv_dir=  "" # Directory to virtual python environment
export yosys_dir=""  # Directory to yosys
export libs_path=""  # Directory to cells library
# Tools setup #
export tools_dir="${utils_dir}/veri_env/"
alias setup='source ${setup_path}'
alias sim='python3 ${tools_dir}sim.py'
alias syn='python3 ${tools_dir}syn.py'
alias get='python3 ${tools_dir}get.py'
alias add='python3 ${tools_dir}add.py'
alias rls='python3 ${tools_dir}release.py'
alias blk='python3 ${tools_dir}block.py'
################################################
### Manual edit of active script ends here   ###
################################################
