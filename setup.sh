#!/bin/bash

home_route='/home/etay-sela/design/veri_home'
work_route='/home/etay-sela/design/veri_work'
ws_name=''
ws_path=''

# Function to print usage
print_usage() {
    echo "Usage: source setup.sh <option>"
    echo "       source setup.sh w <directory>"
    echo "       source setup.sh h"
}

# Check if an argument is provided
if [ $# -eq 0 ]; then
    print_usage
    return 1
fi

# Check the option
case "$1" in
    w)
        # Check if the directory argument is provided
        if [ -z "$2" ]; then
            echo "Error: Missing directory argument."
            print_usage
            return 1
        fi

        # Create the full directory path
        home_path="$home_route/$2"
	work_path="$work_route/$2"

        # Create directories if it doesn't exist
        if [ ! -d "$home_path" ]; then
            mkdir -p "$home_path" || { echo "Error: Unable to create directory '$home_path'."; return 1; }
            echo "Created directory: $home_path"
        fi
	if [ ! -d "$work_path" ]; then
            mkdir -p "$work_path" || { echo "Error: Unable to create directory '$work_path'."; return 1; }
            echo "Created directory: $work_path"
        fi

        # Change the current working directory
        cd "$home_path" || { echo "Error: Unable to change directory to '$home_path'."; return 1; }

        # Print the new working directory
        echo "Changed working directory to: $(pwd)"

        # Add SSH key to agent
        echo "erim" | sshpass -p "erim" ssh-add ~/.ssh/sk070624
        echo "SSH key added to agent"

        # Set tools
        alias sim='python3 /home/etay-sela/design/veri_strg/veri_env/v0.9.0/sim.py'
        alias release='python3 /home/etay-sela/design/veri_strg/veri_env/v0.9.0/release.py'
        alias get='python3 /home/etay-sela/design/veri_strg/veri_env/v0.9.0/get.py -dw $home_path'
        alias add='python3 /home/etay-sela/design/veri_strg/veri_env/v0.9.0/add.py'

	# Activate python vitual env
	source ~/design/veri_env/py_venv/bin/activate
        ;;
    h)
        print_usage
        ;;
    *)
        echo "Error: Unknown option '$1'"
        print_usage
        return 1
        ;;
esac
