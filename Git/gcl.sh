#!/bin/sh
# gcl.sh - Unified launcher for gcl
# Usage:
#   ./gcl.sh [command]              # Run natively (default)
#   ./gcl.sh --venv [command]       # Use venv mode
#   ./gcl.sh --py_docker [command]  # Use Docker mode
#   ./gcl.sh --sh [command]         # Use shell POSIX script
#   ./gcl.sh --help                 # Show help

set -e

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"

# Colors
C_RESET="\033[0m"
C_BOLD="\033[1m"
C_GREEN="\033[32m"
C_CYAN="\033[36m"
C_YELLOW="\033[33m"
C_PURPLE="\033[38;5;141m"
C_GRAY="\033[90m"

# Show help
show_help() {
    printf "\n"
    printf "${C_BOLD}${C_CYAN}╔════════════════════════════════════════════════════════════╗${C_RESET}\n"
    printf "${C_BOLD}${C_CYAN}║                                                            ║${C_RESET}\n"
    printf "${C_BOLD}${C_CYAN}║     gcl.sh - Git Clone/Pull/Push Manager Launcher          ║${C_RESET}\n"
    printf "${C_BOLD}${C_CYAN}║                                                            ║${C_RESET}\n"
    printf "${C_BOLD}${C_CYAN}╚════════════════════════════════════════════════════════════╝${C_RESET}\n\n"

    printf "${C_BOLD}SYNTAX${C_RESET}\n"
    printf "${C_GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}\n"
    printf "  sh gcl.sh [${C_YELLOW}--MODE${C_RESET}] [${C_PURPLE}ACTIONS${C_RESET}]\n\n"

    printf "${C_BOLD}MODES${C_RESET}\n"
    printf "${C_GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}\n"
    printf "  ${C_GREEN}(no mode)${C_RESET}                   ${C_GRAY}Run directly with Python (default)${C_RESET}\n"
    printf "  ${C_YELLOW}--venv${C_RESET}                      ${C_GRAY}Run in Python virtual environment (auto-setups if needed)${C_RESET}\n"
    printf "  ${C_YELLOW}--py_docker${C_RESET}                 ${C_GRAY}Run in Docker container (auto-builds if needed)${C_RESET}\n"
    printf "  ${C_YELLOW}--sh${C_RESET}                        ${C_GRAY}Run the shell POSIX script${C_RESET}\n\n"

    printf "${C_BOLD}ACTIONS${C_RESET}\n"
    printf "${C_GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}\n"
    printf "  ${C_PURPLE}(no command)${C_RESET}                ${C_GRAY}Launch interactive TUI${C_RESET}\n"
    printf "  ${C_PURPLE}sync${C_RESET}                        ${C_GRAY}Bidirectional sync${C_RESET}\n"
    printf "  ${C_PURPLE}push${C_RESET}                        ${C_GRAY}Push changes${C_RESET}\n"
    printf "  ${C_PURPLE}pull${C_RESET}                        ${C_GRAY}Pull changes${C_RESET}\n"
    printf "  ${C_PURPLE}status${C_RESET}                      ${C_GRAY}Check repository status${C_RESET}\n"
    printf "  ${C_PURPLE}fetch${C_RESET}                       ${C_GRAY}Fetch from remote${C_RESET}\n"
    printf "  ${C_PURPLE}untracked${C_RESET}                   ${C_GRAY}List untracked files${C_RESET}\n"
    printf "  ${C_PURPLE}ignored${C_RESET}                     ${C_GRAY}List ignored files${C_RESET}\n"
    printf "  ${C_PURPLE}help${C_RESET}                        ${C_GRAY}Show gcl.py help${C_RESET}\n\n\n"

    printf "${C_BOLD}EXAMPLES${C_RESET}\n"
    printf "${C_GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}\n"
    printf "  ./gcl.sh                    ${C_GRAY}# Run TUI natively${C_RESET}\n"
    printf "  ./gcl.sh --venv             ${C_GRAY}# Run TUI natively (venv)${C_RESET}\n"
    printf "  ./gcl.sh --py_docker        ${C_GRAY}# Run TUI in Docker${C_RESET}\n"
    printf "  ./gcl.sh --sh               ${C_GRAY}# Run TUI in sh Posix${C_RESET}\n\n"
    printf "  ./gcl.sh status             ${C_GRAY}# Check status (native)${C_RESET}\n"
    printf "  ./gcl.sh --venv status      ${C_GRAY}# Check status (venv)${C_RESET}\n\n\n"

    printf "${C_BOLD}OPTIONS${C_RESET}\n"
    printf "${C_GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}\n"
    printf "  ${C_GREEN}--help, -h${C_RESET}                  ${C_GRAY}Show this help message${C_RESET}\n\n"

    printf "${C_BOLD}SETUP${C_RESET}\n"
    printf "${C_GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}\n"
    printf "  --venv                      ${C_GRAY}Mode will automatically setup the virtual environment on first run${C_RESET}\n"
    printf "  --py_docker                 ${C_GRAY}Mode will automatically build the image on first run${C_RESET}\n"
    printf "  (no mode)                   ${C_GRAY}Requires Python 3 to be installed on your system${C_RESET}\n\n"
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

# Run via shell script
run_sh() {
    "$SCRIPT_DIR/gcl/gcl.sh" "$@"
}

# Main
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --py_docker|--docker)
        shift
        run_docker "$@"
        ;;
    --venv)
        shift
        run_venv "$@"
        ;;
    --sh)
        shift
        run_sh "$@"
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
