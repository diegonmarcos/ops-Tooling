#!/bin/sh

# gcl.sh - A simple, POSIX-compliant git clone/pull/push manager with TUI and CLI modes.

# --- Configuration: Repository Lists ---
PUBLIC_REPOS="
front-Github_profile:git@github.com:diegonmarcos/diegonmarcos.git
front-Github_io:git@github.com:diegonmarcos/diegonmarcos.github.io.git
back-Mylibs:git@github.com:diegonmarcos/back-Mylibs.git
back-System:git@github.com:diegonmarcos/back-System.git
back-Algo:git@github.com:diegonmarcos/back-Algo.git
back-Graphic:git@github.com:diegonmarcos/back-Graphic.git
cyber-Cyberwarfare:git@github.com:diegonmarcos/cyber-Cyberwarfare.git
ops-Tooling:git@github.com:diegonmarcos/ops-Tooling.git
ml-MachineLearning:git@github.com:diegonmarcos/ml-MachineLearning.git
ml-DataScience:git@github.com:diegonmarcos/ml-DataScience.git
ml-Agentic:git@github.com:diegonmarcos/ml-Agentic.git
"
PRIVATE_REPOS="
front-Notes_md:git@github.com:diegonmarcos/front-Notes_md.git
z-lecole42:git@github.com:diegonmarcos/lecole42.git
z-dev:git@github.com:diegonmarcos/dev.git
"
ALL_REPOS="${PUBLIC_REPOS}${PRIVATE_REPOS}"

# --- TUI State Variables ---
_strategy_selected=1      # 0=LOCAL, 1=REMOTE (default)
_action_selected=0        # 0=PULL, 1=SYNC, 2=PUSH
_repo_cursor_index=0      # For scrolling through repos
_repo_selection=""        # A string of 'y'/'n' for each repo
_repo_list=""             # A newline-separated list of repo names
_repo_count=0
_current_field=0          # 0=strategy, 1=action, 2=repos, 3=run button
_total_fields=4

# --- Color and Terminal Control ---
C_RESET="\033[0m"; C_BOLD="\033[1m"; C_RED="\033[31m"; C_GREEN="\033[32m";
C_YELLOW="\033[33m"; C_BLUE="\033[34m"; C_CYAN="\033[36m";
C_BG_BLUE="\033[44m"; C_BG_GREEN="\033[42m";

_clear_screen() { tput clear; }
_move_cursor() { tput cup "$1" "$2"; }
_hide_cursor() { tput civis; }
_show_cursor() { tput cnorm; }
_save_term() { _SAVED_TERM=$(stty -g); }
_restore_term() { stty "$_SAVED_TERM"; _show_cursor; }

# --- Helper Functions ---
_log() { printf "${C_CYAN}==>${C_RESET} ${C_BOLD}%s${C_RESET}\n" "$1"; }
_success() { printf "${C_GREEN}  ✓ %s${C_RESET}\n" "$1"; }
_error() { printf "${C_RED}  ✗ %s${C_RESET}\n" "$1"; }
_warn() { printf "${C_YELLOW}  ⚠ %s${C_RESET}\n" "$1"; }

# --- Core Git Functions ---
# @param $1: Repository directory name
# @param $2: Repository git URL
# @param $3: Pull strategy ('ours' or 'theirs' or 'none' for push-only)
# @param $4: Action ('sync', 'pull', 'push')
process_repo() {
    repo_dir="$1"; repo_url="$2"; strategy="$3"; action="$4"

    _log "Processing '$repo_dir'"

    if ! [ -d "$repo_dir" ]; then
        _log "Cloning '$repo_dir'வைக்..."
        if git clone -q "$repo_url" "$repo_dir"; then _success "Clone complete."; else _error "Clone failed."; fi
        printf "\n"; return
    fi

    case "$action" in
        sync|pull) 
            printf "  Pulling with strategy: ${C_BOLD}%s${C_RESET}\n" "$strategy"
            if git -C "$repo_dir" pull -q --strategy-option="$strategy"; then
                _success "Pull complete."
                if [ "$action" = "sync" ]; then
                    printf "  Pushing changes...\n"
                    if git -C "$repo_dir" push -q; then _success "Push complete."; else _warn "Push failed (no changes or permissions issue)."; fi
                fi
            else
                _error "Pull failed."
            fi
            ;; 
        push)
            printf "  Staging all changes...\n"
            git -C "$repo_dir" add .
            # Commit only if there are staged changes
            if ! git -C "$repo_dir" diff-index --quiet --cached HEAD --; then
                printf "  Found changes, committing with default message 'fixes'...\n"
                if git -C "$repo_dir" commit -q -m "fixes"; then
                    _success "Commit complete."
                else
                    _error "Commit failed unexpectedly."
                fi
            fi
            printf "  Pushing changes...\n"
            if git -C "$repo_dir" push -q; then _success "Push complete."; else _warn "Push failed (no changes or permissions issue)."; fi
            ;; 
    esac
    printf "\n"
}

# --- CLI Actions ---
run_cli_sync() {
    strategy_arg="$1"; git_strategy="theirs"
    repos_to_process="${2:-$ALL_REPOS}"
    [ "$strategy_arg" = "local" ] && git_strategy="ours"
    _log "Starting Bidirectional Sync (Strategy: $git_strategy)"
    printf "%s" "$repos_to_process" | while IFS=: read -r repo_dir repo_url;
        do
        [ -z "$repo_dir" ] && continue
        # If the line doesn't contain ':', it's just a repo name from the TUI
        if ! echo "$repo_dir" | grep -q ':'; then
            repo_url=$(printf "%s" "$ALL_REPOS" | grep "^${repo_dir}:" | cut -d: -f2-)
        fi
        process_repo "$repo_dir" "$repo_url" "$git_strategy" "sync"
    done
}

run_cli_push() {
    repos_to_process="${1:-$ALL_REPOS}"
    _log "Starting Push"
    printf "%s" "$repos_to_process" | while IFS=: read -r repo_dir repo_url;
        do
        [ -z "$repo_dir" ] && continue
        if ! echo "$repo_dir" | grep -q ':'; then
            repo_url=$(printf "%s" "$ALL_REPOS" | grep "^${repo_dir}:" | cut -d: -f2-)
        fi
        process_repo "$repo_dir" "$repo_url" "none" "push"
    done
}

run_cli_pull() {
    repos_to_process="${1:-$ALL_REPOS}"
    _log "Starting Forced Pull (Remote Overwrites Local on Conflict)"
    printf "%s" "$repos_to_process" | while IFS=: read -r repo_dir repo_url;
        do
        [ -z "$repo_dir" ] && continue
        if ! echo "$repo_dir" | grep -q ':'; then
            repo_url=$(printf "%s" "$ALL_REPOS" | grep "^${repo_dir}:" | cut -d: -f2-)
        fi
        process_repo "$repo_dir" "$repo_url" "theirs" "pull"
    done
}

# --- TUI Functions ---
_read_key() {
    char=""
    key=""
    char=$(dd bs=1 count=1 2>/dev/null)
    if [ "$char" = "$(printf '\033')" ]; then
        char2=$(dd bs=1 count=2 2>/dev/null)
        case "$char2" in
            '[A') key="up" ;;
            '[B') key="down" ;;
        esac
    elif [ "$char" = "$(printf '\n')" ] || [ "$char" = "$(printf '\r')" ]; then
        key="enter"
    elif [ "$char" = " " ]; then
        key="space"
    elif [ "$char" = "$(printf '\t')" ]; then
        key="tab"
    elif [ "$char" = "a" ]; then
        key="selectall"
    elif [ "$char" = "u" ]; then
        key="unselectall"
    elif [ "$char" = "q" ]; then
        key="quit"
    fi
    printf "%s" "$key"
}

draw_interface() {
    _clear_screen; _move_cursor 0 0
    printf "${C_BOLD}${C_CYAN}╔══════════════════════════════════════════════════════════════════════╗\n"
    printf "║                  gcl.sh - Git Sync Manager                     ║\n"
    printf "╚══════════════════════════════════════════════════════════════════════╝${C_RESET}\n"
    printf "  ${C_YELLOW}Navigate: ↑/↓  Switch: TAB  Toggle: SPACE  Run: ENTER  Quit: q${C_RESET}\n"
    printf "  ${C_YELLOW}Select All: a  Unselect All: u${C_RESET}\n\n"

    # --- Strategy Selection ---
    _line=5; _move_cursor $_line 2; printf "${C_BOLD}${C_BLUE}MERGE STRATEGY (On Conflict):${C_RESET}"
    _line=$((_line + 1)); _move_cursor $_line 4
    [ "$_current_field" -eq 0 ] && printf "$C_BG_BLUE"
    printf "[%s] LOCAL  (Keep local changes)" "$([ "$_strategy_selected" -eq 0 ] && printf "●" || printf " ")"
    printf "$C_RESET"

    _line=$((_line + 1)); _move_cursor $_line 4
    [ "$_current_field" -eq 0 ] && printf "$C_BG_BLUE"
    printf "[%s] REMOTE (Overwrite with remote)" "$([ "$_strategy_selected" -eq 1 ] && printf "●" || printf " ")"
    printf "$C_RESET\n"

    # --- Action Selection ---
    _line=$((_line + 2)); _move_cursor $_line 2; printf "${C_BOLD}${C_BLUE}ACTION:${C_RESET}"
    _line=$((_line + 1)); _move_cursor $_line 4
    [ "$_current_field" -eq 1 ] && printf "$C_BG_BLUE"
    printf "[%s] PULL   (Remote -> Local)" "$([ "$_action_selected" -eq 0 ] && printf "●" || printf " ")"
    printf "$C_RESET"

    _line=$((_line + 1)); _move_cursor $_line 4
    [ "$_current_field" -eq 1 ] && printf "$C_BG_BLUE"
    printf "[%s] SYNC   (Remote <-> Local)" "$([ "$_action_selected" -eq 1 ] && printf "●" || printf " ")"
    printf "$C_RESET"

    _line=$((_line + 1)); _move_cursor $_line 4
    [ "$_current_field" -eq 1 ] && printf "$C_BG_BLUE"
    printf "[%s] PUSH   (Local -> Remote)" "$([ "$_action_selected" -eq 2 ] && printf "●" || printf " ")"
    printf "$C_RESET\n"

    # --- Repository Selection ---
    _line=$((_line + 2)); _move_cursor $_line 2; printf "${C_BOLD}${C_BLUE}REPOSITORIES (Toggle with SPACE):${C_RESET}"
    
    # Save current line to draw the run button later
    _run_button_line=$((_line + _repo_count + 2))

    i=0
    printf "%s" "$_repo_list" | while IFS= read -r repo_name || [ -n "$repo_name" ]; do
        _line=$((_line + 1)); _move_cursor $_line 4
        
        is_selected=$(echo "$_repo_selection" | cut -c $((i + 1)))
        
        # Highlight if this is the active field and the cursor is on this repo
        if [ "$_current_field" -eq 2 ] && [ "$i" -eq "$_repo_cursor_index" ]; then
            printf "$C_BG_BLUE"
        fi

        printf "[%s] %s" "$([ "$is_selected" = "y" ] && printf "✓" || printf " ")" "$repo_name"
        printf "$C_RESET"
        i=$((i + 1))
    done


    # --- Execute Button ---
    _move_cursor $_run_button_line 2
    [ "$_current_field" -eq 3 ] && printf "$C_BG_GREEN"
    printf "  ${C_BOLD}[ RUN ]${C_RESET}  "
    _move_cursor $(($_run_button_line + 2)) 0
}

run_tui_action() {
    _restore_term; _clear_screen
    strategy="theirs"; [ "$_strategy_selected" -eq 0 ] && strategy="ours"
    
    # Build the list of selected repos
    selected_repos=""
    i=0
    printf "%s" "$_repo_list" | while IFS= read -r repo_name || [ -n "$repo_name" ]; do
        is_selected=$(echo "$_repo_selection" | cut -c $((i + 1)))
        if [ "$is_selected" = "y" ]; then
            selected_repos="${selected_repos}${repo_name}\n"
        fi
        i=$((i + 1))
    done

    if [ -z "$selected_repos" ]; then
        _warn "No repositories selected. Nothing to do."
    else
        case "$_action_selected" in
            0) run_cli_pull "$selected_repos" ;; 
            1) run_cli_sync "$([ "$_strategy_selected" -eq 0 ] && echo "local" || echo "remote")" "$selected_repos" ;; 
            2) run_cli_push "$selected_repos" ;; 
        esac
    fi
    
    printf "\n${C_GREEN}${C_BOLD}All tasks complete! Press any key to exit.${C_RESET}\n"
    dd bs=1 count=1 >/dev/null 2>&1
}

run_interactive_mode() {
    # --- Initialize TUI-specific repo variables ---
    # Extract just the repo names, trimming leading/trailing whitespace
    _repo_list=$(printf "%s" "$ALL_REPOS" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | cut -d: -f1 | sed '/^$/d')
    _repo_count=$(echo "$_repo_list" | wc -l)
    # Initialize all repos to be selected ('y')
    i=1; while [ "$i" -le "$_repo_count" ]; do _repo_selection="${_repo_selection}y"; i=$((i+1)); done

    trap '_restore_term' EXIT INT TERM; _save_term
    stty -icanon -echo; _hide_cursor

    while true; do
        draw_interface
        key=$(_read_key)
        case "$key" in
            up)
                if [ "$_current_field" -eq 2 ]; then # In repo list
                    _repo_cursor_index=$(( (_repo_cursor_index - 1 + _repo_count) % _repo_count ))
                else
                    _current_field=$(((_current_field - 1 + _total_fields) % _total_fields))
                fi
                ;;
            down)
                if [ "$_current_field" -eq 2 ]; then # In repo list
                    _repo_cursor_index=$(( (_repo_cursor_index + 1) % _repo_count ))
                else
                    _current_field=$(((_current_field + 1) % _total_fields))
                fi
                ;;
            tab)
                _current_field=$(((_current_field + 1) % _total_fields))
                ;;
            selectall)
                # Select all repositories
                _repo_selection=""
                i=1; while [ "$i" -le "$_repo_count" ]; do _repo_selection="${_repo_selection}y"; i=$((i+1)); done
                ;;
            unselectall)
                # Unselect all repositories
                _repo_selection=""
                i=1; while [ "$i" -le "$_repo_count" ]; do _repo_selection="${_repo_selection}n"; i=$((i+1)); done
                ;;
            space)
                case "$_current_field" in
                    0) _strategy_selected=$((1 - _strategy_selected)) ;;
                    1) _action_selected=$(((_action_selected + 1) % 3)) ;;
                    2) # Toggle repo selection
                        current_char=$(echo "$_repo_selection" | cut -c $((_repo_cursor_index + 1)))
                        new_char=$([ "$current_char" = "y" ] && echo "n" || echo "y")
                        _repo_selection=$(echo "$_repo_selection" | sed "s/./$new_char/$((_repo_cursor_index + 1))")
                        ;;
                    3) run_tui_action; break ;;
                esac
                ;; 
            enter) [ "$_current_field" -eq 3 ] && { run_tui_action; break; };;
            quit) break ;; 
        esac
    done
    _restore_term
}

show_help() {
    printf "${C_BOLD}${C_CYAN}gcl.sh - Git Clone/Pull/Push Manager${C_RESET}\n\n"
    printf "Manages multiple git repositories via a TUI or command-line arguments.\n\n"
    printf "${C_BOLD}${C_YELLOW}USAGE:${C_RESET}\n"
    printf "  ${C_BOLD}gcl.sh${C_RESET} [command] [options]\n\n"
    printf "${C_BOLD}${C_YELLOW}COMMANDS:${C_RESET}\n"
    printf "  (no command)\t\tLaunches the interactive TUI menu.\n"
    printf "  ${C_GREEN}sync [local|remote]${C_RESET}\tBidirectional sync. Default: 'remote'.\n"
    printf "  ${C_GREEN}push${C_RESET}\t\t\tPushes committed changes.\n"
    printf "  ${C_GREEN}pull${C_RESET}\t\t\tPulls using 'remote' strategy.\n"
    printf "  ${C_GREEN}help${C_RESET}\t\t\tShows this help message.\n\n"
}

# --- Main Entry Point ---
main() {
    case "$1" in
        sync) run_cli_sync "$2" ;; 
        push) run_cli_push ;; 
        pull) run_cli_pull ;; 
        help|-h|--help) show_help ;; 
        "") run_interactive_mode ;; 
        *) _error "Invalid command: $1"; show_help; exit 1 ;; 
    esac
}

main "$@"