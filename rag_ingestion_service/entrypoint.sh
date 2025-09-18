#!/bin/bash
set -e

# If no arguments provided, run the default command
if [ $# -eq 0 ]; then
    exec python cli_main.py
else
    # If arguments provided, run cli_main.py with those arguments
    exec python cli_main.py "$@"
fi
