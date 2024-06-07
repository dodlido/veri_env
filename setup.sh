#!/bin/bash

ws_parent='/home/etay-sela/design/veri_home'
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
        full_path="$ws_parent/$2"

        # Create the directory if it doesn't exist
        if [ ! -d "$full_path" ]; then
            mkdir -p "$full_path" || { echo "Error: Unable to create directory '$full_path'."; return 1; }
            echo "Created directory: $full_path"
        fi

        # Change the current working directory
        cd "$full_path" || { echo "Error: Unable to change directory to '$full_path'."; return 1; }

        # Print the new working directory
        echo "Changed working directory to: $(pwd)"

        # Add SSH key to agent
        echo "erim" | sshpass -p "erim" ssh-add ~/.ssh/sk070624
        echo "SSH key added to agent"

        # Set tools
        alias sim='python3 /home/etay-sela/design/veri_env/sim.py'
        alias release='python3 /home/etay-sela/design/veri_env/release.py'
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
