#!/bin/bash
set -e

# If no arguments provided, run the default command
if [ $# -eq 0 ]; then
    exec python cli_main.py
elif [ "$1" = "python" ] && [ "$2" = "cli_main.py" ]; then
    # If first two args are "python cli_main.py", skip them and use the rest
    shift 2
    exec python cli_main.py "$@"
else
    # If arguments provided, run cli_main.py with those arguments
    exec python cli_main.py "$@"
fi
