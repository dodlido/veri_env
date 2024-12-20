# Your github info #
export git_username="username"
export git_main_path="git@github.com:username/"
export git_key_path="wherever you keep your api private key"
# Your name #
export real_username="name"
# Paths to your personal storage #
export rls_dir="some arbitrary path"   # Directory to store releases 
export home_dir="some arbitrary path"  # Directory to develop 
export work_dir="some arbitrary path"  # Directory to see simulation results
export utils_dir="some arbitrary path" # Directory to my_defs.sh, setup.sh and pyvenv
# Tools setup #
export tools_version="clone to your releases some tag and specify here which tag you used" # Specify the tools version you would like to use
export tools_dir="${rls_dir}/veri_env/${tools_version}/"
alias sim='python3 ${tools_dir}sim.py'
alias get='python3 ${tools_dir}get.py'
alias add='python3 ${tools_dir}add.py'
alias rls='python3 ${tools_dir}release.py'
