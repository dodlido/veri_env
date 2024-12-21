#!/bin/bash

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

        # Source your own definitions:
        export defs_path="$(dirname "$(realpath "$0")")/../my_defs.sh"
        source ${defs_path}

        # Create the full directory path
        home_path="$home_dir/$2"
        work_path="$work_dir/$2"

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
        sshpass -p ${git_ssh_key_passphrase} ssh-add ${git_ssh_key_path}
        echo "SSH key added to agent"

        # Activate python vitual env
        source ${venv_dir}/bin/activate
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
