#!/bin/bash

choose() {
    echo "How do you want to populate the database?"
    echo "1) Using CSV files"
    echo "2) Using example data"
    read -p "Enter 1 or 2: " choice
    echo "$choice"
}

run_script() {
    case "$1" in
        1|csv)
            echo "Running pop_with_csv.py..."
            python3 pop_with_csv.py "${@:2}"
            ;;
        2|example)
            echo "Running pop_with_example.py..."
            python3 pop_with_example.py "${@:2}"
            ;;
        *)
            echo "Invalid option."
            exit 1
            ;;
    esac
}

if [ $# -eq 0 ]; then
    choice=$(choose)
    run_script "$choice"
else
    run_script "$@"
fi
