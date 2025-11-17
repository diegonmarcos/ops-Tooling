#!/bin/sh
# gcl.sh - Unified launcher for gcl.py
# Usage:
#   ./gcl.sh [command]           # Run natively (default)
#   ./gcl.sh --docker [command]  # Use Docker mode
#   ./gcl.sh --venv [command]    # Use venv mode
#   ./gcl.sh --help              # Show help

set -e

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"

# Colors
C_RESET="\033[0m"
C_BOLD="\033[1m"
C_GREEN="\033[32m"
C_CYAN="\033[36m"

# Show help
show_help() {
    printf "${C_BOLD}${C_CYAN}gcl.sh - Git Clone/Pull/Push Manager Launcher${C_RESET}\n\n"
    printf "${C_BOLD}USAGE:${C_RESET}\n"
    printf "  ./gcl.sh [OPTIONS] [COMMAND] [ARGS...]\n\n"
    printf "${C_BOLD}MODES:${C_RESET}\n"
    printf "  ${C_GREEN}--native${C_RESET}       Run directly with Python (default)\n"
    printf "  ${C_GREEN}--docker${C_RESET}       Run in Docker container (auto-builds if needed)\n"
    printf "  ${C_GREEN}--venv${C_RESET}         Run in Python virtual environment (auto-setups if needed)\n\n"
    printf "${C_BOLD}OPTIONS:${C_RESET}\n"
    printf "  ${C_GREEN}--help, -h${C_RESET}    Show this help message\n\n"
    printf "${C_BOLD}SETUP:${C_RESET}\n"
    printf "  ${C_GREEN}--venv${C_RESET} mode will automatically setup the virtual environment on first run\n"
    printf "  ${C_GREEN}--docker${C_RESET} mode will automatically build the image on first run\n"
    printf "  ${C_GREEN}--native${C_RESET} mode requires Python 3 to be installed on your system\n\n"
    printf "${C_BOLD}COMMANDS:${C_RESET}\n"
    printf "  ${C_GREEN}(no command)${C_RESET}  Launch interactive TUI\n"
    printf "  ${C_GREEN}sync${C_RESET}          Bidirectional sync\n"
    printf "  ${C_GREEN}push${C_RESET}          Push changes\n"
    printf "  ${C_GREEN}pull${C_RESET}          Pull changes\n"
    printf "  ${C_GREEN}status${C_RESET}        Check repository status\n"
    printf "  ${C_GREEN}fetch${C_RESET}         Fetch from remote\n"
    printf "  ${C_GREEN}untracked${C_RESET}     List untracked files\n"
    printf "  ${C_GREEN}ignored${C_RESET}       List ignored files\n"
    printf "  ${C_GREEN}help${C_RESET}          Show gcl.py help\n\n"
    printf "${C_BOLD}EXAMPLES:${C_RESET}\n"
    printf "  ./gcl.sh                    ${C_CYAN}# Run TUI natively${C_RESET}\n"
    printf "  ./gcl.sh status             ${C_CYAN}# Check status (native)${C_RESET}\n"
    printf "  ./gcl.sh --docker           ${C_CYAN}# Run TUI in Docker${C_RESET}\n"
    printf "  ./gcl.sh --docker status    ${C_CYAN}# Check status in Docker${C_RESET}\n"
    printf "  ./gcl.sh --venv sync        ${C_CYAN}# Sync using venv (auto-setup)${C_RESET}\n"
}

# Run natively
run_native() {
    # Check terminal size for TUI mode
    if [ $# -eq 0 ]; then
        # Only check terminal for TUI mode (no args)
        if ! command -v tput > /dev/null 2>&1; then
            printf "Warning: tput not found, terminal check skipped\n" >&2
        else
            TERM_ROWS=$(tput lines 2>/dev/null || echo 0)
            TERM_COLS=$(tput cols 2>/dev/null || echo 0)
            if [ "$TERM_ROWS" -lt 24 ] || [ "$TERM_COLS" -lt 80 ]; then
                printf "Error: Terminal too small for TUI (need 24x80, got ${TERM_ROWS}x${TERM_COLS})\n" >&2
                printf "Try: ./gcl.sh status  (to run CLI mode instead)\n" >&2
                exit 1
            fi
        fi

        # Set TERM if not set
        if [ -z "$TERM" ] || [ "$TERM" = "dumb" ]; then
            export TERM=xterm-256color
        fi
    fi

    python3 "$SCRIPT_DIR/gcl/gcl.py" "$@"
}

# Run via Docker
run_docker() {
    cd "$SCRIPT_DIR/gcl/gcl_py-docker"
    if docker compose version > /dev/null 2>&1; then
        docker compose run --rm gcl "$@"
    else
        docker-compose run --rm gcl "$@"
    fi
}

# Run via venv
run_venv() {
    VENV_DIR="$SCRIPT_DIR/gcl/gcl_py-venv/venv"
    VENV_SCRIPT="$SCRIPT_DIR/gcl/gcl_py-venv/gcl-venv.sh"

    # Check if venv exists, if not, run setup
    if [ ! -d "$VENV_DIR" ]; then
        printf "${C_CYAN}==>${C_RESET} ${C_BOLD}Virtual environment not found. Setting up...${C_RESET}\n"
        "$VENV_SCRIPT" setup
        printf "\n"
    fi

    # Now run with venv
    "$VENV_SCRIPT" run "$@"
}

# Main
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --docker)
        shift
        run_docker "$@"
        ;;
    --venv)
        shift
        run_venv "$@"
        ;;
    --native)
        shift
        run_native "$@"
        ;;
    *)
        # Default to native with all args
        run_native "$@"
        ;;
esac
