#!/bin/sh

# gcl.sh - A simple, POSIX-compliant git clone/pull/push manager with TUI and CLI modes.
# MODIFIED:
# - Added TUI-based repo status panel on the right.
# - Added 'r' key to refresh status panel.
# - Added 's' key to select only "not OK" repos.
# - FIXED: 's' key was selecting all repos.
# - MODIFIED: 'sync' action now adds+commits before pushing.
# - MODIFIED: 'Enter' key now triggers RUN from anywhere.
# - FIXED: "m" + "enter" auto-run bug.
# - ADDED: All-lowercase shortcuts as requested (l/e, s/p/c/t, k/r/a/u).
# - FIXED: "divergent branches" error by adding --no-rebase to pull command.
# - FIXED: TUI highlighting bug; highlight now fills the entire line.
# - MODIFIED: Changed shortcuts/labels per user request (Pull='l', Local='o', Remote='E')
# - FIXED: Corrected TUI labels (L O CAL, S T ATUS) per request.
# - FIXED: Removed yellow/orange from help text per request.
# - FIXED: Reverted buggy full-line highlight for Strategy/Action/Run per request.

# --- Configuration: Repository Lists ---
PUBLIC_REPOS="
front-Github_profile:git@github.com:diegonmarcos/diegonmarcos.git
front-Github_io:git@github.com:diegonmarcos/diegonmarcos.github.io.git
back-System:git@github.com:diegonmarcos/back-System.git
back-Algo:git@github.com:diegonmarcos/back-Algo.git
back-Graphic:git@github.com:diegonmarcos/back-Graphic.git
cyber-Cyberwarfare:git@github.com:diegonmarcos/cyber-Cyberwarfare.git
ops-Tooling:git@github.com:diegonmarcos/ops-Tooling.git
ops-Mylibs:git@github.com:diegonmarcos/ops-Mylibs.git
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
_action_selected=0        # 0=SYNC (default), 1=PUSH, 2=PULL, 3=STATUS
_repo_cursor_index=0      # For scrolling through repos
_repo_selection=""        # A string of 'y'/'n' for each repo
_repo_list=""             # A newline-separated list of repo names
_repo_status_list=""      # A newline-separated list of repo statuses
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

# Silently checks the status of a single repo for the TUI
# @param $1: Repository directory name
_get_repo_status() {
    repo_dir="$1"

    if ! [ -d "$repo_dir" ]; then
        printf "${C_YELLOW}Not Cloned${C_RESET}"
        return
    fi

    # Check for uncommitted changes (staged and unstaged)
    if ! git -C "$repo_dir" diff-index --quiet HEAD -- 2>/dev/null; then
        printf "${C_YELLOW}Uncommitted${C_RESET}"
        return
    fi

    # Check if branch tracks a remote
    if ! git -C "$repo_dir" rev-parse @{u} >/dev/null 2>&1; then
        printf "${C_RED}No Remote${C_RESET}"
        return
    fi

    # Check for unpushed commits
    unpushed=$(git -C "$repo_dir" log @{u}.. --oneline 2>/dev/null | wc -l)
    if [ "$unpushed" -gt 0 ]; then
        printf "${C_YELLOW}%s Unpushed${C_RESET}" "$unpushed"
        return
    fi

    printf "${C_GREEN}OK${C_RESET}"
}


# @param $1: Repository directory name
# @param $2: Repository git URL
# @param $3: Pull strategy ('ours' or 'theirs' or 'none' for push-only)
# @param $4: Action ('sync', 'pull', 'push')
process_repo() {
    repo_dir="$1"; repo_url="$2"; strategy="$3"; action="$4"

    _log "Processing '$repo_dir'"

    if ! [ -d "$repo_dir" ]; then
        _log "Cloning '$repo_dir'..."
        if git clone -q "$repo_url" "$repo_dir"; then _success "Clone complete."; else _error "Clone failed."; fi
        printf "\n"; return
    fi

    case "$action" in
        sync|pull)
            printf "  Pulling with strategy: ${C_BOLD}%s${C_RESET}\n" "$strategy"

            # --- FIX: Added --no-rebase to force a merge ---
            # This prevents "divergent branches" error and allows --strategy-option to work.
            if git -C "$repo_dir" pull -q --no-rebase --strategy-option="$strategy"; then
            # --- END FIX ---
                _success "Pull complete."

                if [ "$action" = "sync" ]; then
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

run_cli_status() {
    repos_to_process="${1:-$ALL_REPOS}"
    _log "Checking Git Status for Repositories"
    printf "%s" "$repos_to_process" | while IFS=: read -r repo_dir repo_url;
        do
        [ -z "$repo_dir" ] && continue
        if ! echo "$repo_dir" | grep -q ':'; then
            repo_url=$(printf "%s" "$ALL_REPOS" | grep "^${repo_dir}:" | cut -d: -f2-)
        fi

        if ! [ -d "$repo_dir" ]; then
            _warn "'$repo_dir' not cloned yet."
            printf "\n"
            continue
        fi

        _log "Checking '$repo_dir'"

        # Check for uncommitted changes (staged and unstaged)
        if ! git -C "$repo_dir" diff-index --quiet HEAD -- 2>/dev/null; then
            _warn "Has uncommitted changes (staged or unstaged)"
            printf "  ${C_YELLOW}Files changed:${C_RESET}\n"
            git -C "$repo_dir" status --short | sed 's/^/    /'
        else
            _success "Working tree clean"
        fi

        # Check for unpushed commits
        unpushed=$(git -C "$repo_dir" log @{u}.. --oneline 2>/dev/null | wc -l)
        if [ "$unpushed" -gt 0 ]; then
            _warn "Has $unpushed unpushed commit(s)"
            printf "  ${C_YELLOW}Unpushed commits:${C_RESET}\n"
            git -C "$repo_dir" log @{u}.. --oneline | sed 's/^/    /'
        else
            # Check if branch tracks a remote
            if git -C "$repo_dir" rev-parse @{u} >/dev/null 2>&1; then
                _success "All commits pushed"
            else
                _warn "Branch does not track a remote"
            fi
        fi

        printf "\n"
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
    # --- New Shortcuts ---
    elif [ "$char" = "o" ]; then # NEW: 'o' for Local
        key="local"
    elif [ "$char" = "e" ]; then
        key="remote"
    elif [ "$char" = "s" ]; then
        key="sync"
    elif [ "$char" = "p" ]; then
        key="push"
    elif [ "$char" = "l" ]; then # NEW: 'l' for Pull
        key="pull"
    elif [ "$char" = "t" ]; then
        key="status"
    elif [ "$char" = "k" ]; then
        key="selectnotok"
    # --- End New Shortcuts ---
    elif [ "$char" = "a" ]; then
        key="selectall"
    elif [ "$char" = "u" ]; then
        key="unselectall"
    elif [ "$char" = "r" ]; then
        key="refresh"
    elif [ "$char" = "q" ]; then
        key="quit"
    fi
    printf "%s" "$key"
}

draw_interface() {
    _clear_screen; _move_cursor 0 0
    # Get terminal width
    _t_width=${COLUMNS:-$(tput cols)}

    printf "${C_BOLD}${C_CYAN}╔══════════════════════════════════════════════════════════════════════╗\n"
    printf "║                  gcl.sh - Git Sync Manager                     ║\n"
    printf "╚══════════════════════════════════════════════════════════════════════╝${C_RESET}\n"
    # UPDATED Help Text (Removed C_YELLOW)
    printf "  Navigate: ↑/↓  Switch: TAB  Toggle: SPACE  Run: ENTER  Quit: q\n"
    printf "  Repo List:  ${C_BOLD}a${C_RESET}/${C_BOLD}u${C_RESET} (All/None)  ${C_BOLD}k${C_RESET} (Not OK)  ${C_BOLD}r${C_RESET} (Refresh)\n"
    printf "  Shortcuts:  ${C_BOLD}o${C_RESET}/${C_BOLD}e${C_RESET} (Strategy)  ${C_BOLD}s${C_RESET}/${C_BOLD}p${C_RESET}/${C_BOLD}l${C_RESET}/${C_BOLD}t${C_RESET} (Action)\n\n"


    # --- Strategy Selection (HIGHLIGHT FIX) ---
    _line=7;
    _move_cursor $_line 2; printf "${C_BOLD}${C_BLUE}MERGE STRATEGY (On Conflict):${C_RESET}"

    _line=$((_line + 1)); _move_cursor $_line 4
    # MODIFIED: Label for Local (L O CAL)
    _line_text=$(printf "[%s] L${C_BOLD}O${C_RESET}CAL  (Keep local changes)" "$([ "$_strategy_selected" -eq 0 ] && printf "●" || printf " ")")
    if [ "$_current_field" -eq 0 ]; then
        printf "${C_BG_BLUE}%s${C_RESET}" "$_line_text" # Reverted: No padding
    else
        printf "%s" "$_line_text"
    fi

    _line=$((_line + 1)); _move_cursor $_line 4
    _line_text=$(printf "[%s] R${C_BOLD}E${C_RESET}MOTE (Overwrite with remote)" "$([ "$_strategy_selected" -eq 1 ] && printf "●" || printf " ")")
    if [ "$_current_field" -eq 0 ]; then
        printf "${C_BG_BLUE}%s${C_RESET}" "$_line_text" # Reverted: No padding
    else
        printf "%s" "$_line_text"
    fi
    printf "\n"

    # --- Action Selection (HIGHLIGHT FIX) ---
    _line=$((_line + 2)); _move_cursor $_line 2; printf "${C_BOLD}${C_BLUE}ACTION:${C_RESET}"

    _line=$((_line + 1)); _move_cursor $_line 4
    _line_text=$(printf "[%s] ${C_BOLD}S${C_RESET}YNC   (Remote <-> Local)" "$([ "$_action_selected" -eq 0 ] && printf "●" || printf " ")")
    [ "$_current_field" -eq 1 ] && printf "${C_BG_BLUE}%s${C_RESET}" "$_line_text" || printf "%s" "$_line_text" # Reverted

    _line=$((_line + 1)); _move_cursor $_line 4
    _line_text=$(printf "[%s] ${C_BOLD}P${C_RESET}USH   (Local -> Remote)" "$([ "$_action_selected" -eq 1 ] && printf "●" || printf " ")")
    [ "$_current_field" -eq 1 ] && printf "${C_BG_BLUE}%s${C_RESET}" "$_line_text" || printf "%s" "$_line_text" # Reverted

    _line=$((_line + 1)); _move_cursor $_line 4
    _line_text=$(printf "[%s] PU${C_BOLD}L${C_RESET}L (Remote -> Local)" "$([ "$_action_selected" -eq 2 ] && printf "●" || printf " ")")
    [ "$_current_field" -eq 1 ] && printf "${C_BG_BLUE}%s${C_RESET}" "$_line_text" || printf "%s" "$_line_text" # Reverted

    _line=$((_line + 1)); _move_cursor $_line 4
    # MODIFIED: Label for Status (S T ATUS)
    _line_text=$(printf "[%s] S${C_BOLD}T${C_RESET}ATUS (Check repos)" "$([ "$_action_selected" -eq 3 ] && printf "●" || printf " ")")
    [ "$_current_field" -eq 1 ] && printf "${C_BG_BLUE}%s${C_RESET}" "$_line_text" || printf "%s" "$_line_text" # Reverted
    printf "\n"

    # --- Repository Selection (HIGHLIGHT FIX) ---
    _line=$((_line + 2));
    _move_cursor $_line 2;  printf "${C_BOLD}${C_BLUE}REPOSITORIES (Toggle with SPACE):${C_RESET}"
    _move_cursor $_line 40; printf "${C_BOLD}${C_BLUE}STATUS:${C_RESET}"

    _run_button_line=$((_line + _repo_count + 2))

    i=0
    while [ "$i" -lt "$_repo_count" ]; do
        _line=$((_line + 1));

        repo_name=$(echo "$_repo_list" | sed -n "$((i + 1))p")
        is_selected=$(echo "$_repo_selection" | cut -c $((i + 1)))
        status_string=$(echo "$_repo_status_list" | sed -n "$((i + 1))p")
        marker="$([ "$is_selected" = "y" ] && printf "✓" || printf " ")"

        repo_line=$(printf "[%s] %-30.30s" "$marker" "$repo_name")
        _full_line=$(printf "%s  %s" "$repo_line" "$status_string")

        _move_cursor $_line 4
        if [ "$_current_field" -eq 2 ] && [ "$i" -eq "$_repo_cursor_index" ]; then
            _line_width=$((_t_width - 4))
            printf "${C_BG_BLUE}%-${_line_width}.${_line_width}s${C_RESET}" "$_full_line"
        else
            printf "%s" "$repo_line"
            _move_cursor $_line 40
            printf "%s" "$status_string"
        fi

        i=$((i + 1))
    done


    # --- Execute Button (HIGHLIGHT FIX) ---
    _move_cursor $_run_button_line 2
    # MODIFIED: Removed trailing spaces from text
    _line_text="  ${C_BOLD}[ RUN ]${C_RESET}"
    if [ "$_current_field" -eq 3 ]; then
        printf "${C_BG_GREEN}%s${C_RESET}" "$_line_text" # Reverted
    else
        printf "%s" "$_line_text"
    fi
    _move_cursor $(($_run_button_line + 2)) 0
}

run_tui_action() {
    _restore_term; _clear_screen
    strategy="theirs"; [ "$_strategy_selected" -eq 0 ] && strategy="ours"

    # Build the list of selected repos
    selected_repos=""
    i=0
    while IFS= read -r repo_name || [ -n "$repo_name" ]; do
        is_selected=$(echo "$_repo_selection" | cut -c $((i + 1)))
        if [ "$is_selected" = "y" ]; then
            selected_repos="${selected_repos}${repo_name}
"
        fi
        i=$((i + 1))
    done <<EOF
$_repo_list
EOF

    if [ -z "$selected_repos" ]; then
        _warn "No repositories selected. Nothing to do."
    else
        case "$_action_selected" in
            0) run_cli_sync "$([ "$_strategy_selected" -eq 0 ] && echo "local" || echo "remote")" "$selected_repos" ;;
            1) run_cli_push "$selected_repos" ;;
            2) run_cli_pull "$selected_repos" ;;
            3) run_cli_status "$selected_repos" ;;
        esac
    fi

    printf "\n${C_GREEN}${C_BOLD}All tasks complete!${C_RESET}\n"
    printf "${C_YELLOW}Press 'm' to return to menu or any other key to exit.${C_RESET}\n"

    # --- BUG FIX: Use 'read -r' to consume the newline ---
    # This prevents the 'enter' from being passed to the next TUI loop
    read -r choice
    case "$choice" in
        m*|M*) return 0 ;; # Return to menu
        *) return 1 ;;     # Exit
    esac
    # --- END BUG FIX ---
}

# --- FUNCTION: To refresh repo statuses ---
_refresh_repo_statuses() {
    # Temporarily show a loading message
    _clear_screen; _move_cursor 5 5;
    printf "${C_BOLD}${C_YELLOW}Refreshing repository statuses...${C_RESET}"

    _repo_status_list=""
    i=1
    while [ "$i" -le "$_repo_count" ]; do
        repo_name=$(echo "$_repo_list" | sed -n "${i}p")
        status=$(_get_repo_status "$repo_name")
        _repo_status_list="${_repo_status_list}${status}
"
        i=$((i+1))
    done
}


run_interactive_mode() {
    # --- Initialize TUI-specific repo variables ---
    # Extract just the repo names, trimming leading/trailing whitespace
    _repo_list=$(printf "%s" "$ALL_REPOS" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | cut -d: -f1 | sed '/^$/d')
    _repo_count=$(echo "$_repo_list" | wc -l)

    # Initialize all repos to be selected ('y')
    _repo_selection=""
    i=1; while [ "$i" -le "$_repo_count" ]; do _repo_selection="${_repo_selection}y"; i=$((i+1)); done

    # --- Pre-load all repository statuses ---
    _refresh_repo_statuses # Call the new function

    # Reset cursor positions
    _repo_cursor_index=0
    _current_field=0

    trap '_restore_term' EXIT INT TERM; _save_term
    stty -icanon -echo; _hide_cursor

    _return_to_menu=0

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

            # --- Repo Selection Shortcuts ---
            selectall) # 'a'
                _repo_selection=""
                i=1; while [ "$i" -le "$_repo_count" ]; do _repo_selection="${_repo_selection}y"; i=$((i+1)); done
                ;;
            unselectall) # 'u'
                _repo_selection=""
                i=1; while [ "$i" -le "$_repo_count" ]; do _repo_selection="${_repo_selection}n"; i=$((i+1)); done
                ;;
            selectnotok) # 'k'
                OK_STRING=$(printf "${C_GREEN}OK${C_RESET}")
                new_selection=""
                i=0
                while [ "$i" -lt "$_repo_count" ]; do
                    status=$(echo "$_repo_status_list" | sed -n "$((i + 1))p")
                    if [ "$status" != "$OK_STRING" ]; then
                        new_selection="${new_selection}y"
                    else
                        new_selection="${new_selection}n"
                    fi
                    i=$((i + 1))
                done
                _repo_selection="$new_selection"
                ;;
            refresh) # 'r'
                _refresh_repo_statuses
                ;;

            # --- Menu Shortcuts (MODIFIED) ---
            local)  _strategy_selected=0 ;; # 'o'
            remote) _strategy_selected=1 ;; # 'e'
            sync)   _action_selected=0 ;; # 's'
            push)   _action_selected=1 ;; # 'p'
            pull)   _action_selected=2 ;; # 'l'
            status) _action_selected=3 ;; # 't'

            space)
                case "$_current_field" in
                    0) _strategy_selected=$((1 - _strategy_selected)) ;;
                    1) _action_selected=$(((_action_selected + 1) % 4)) ;;
                    2) # Toggle repo selection
                        current_char=$(echo "$_repo_selection" | cut -c $((_repo_cursor_index + 1)))
                        new_char=$([ "$current_char" = "y" ] && echo "n" || echo "y")
                        _repo_selection=$(echo "$_repo_selection" | sed "s/./$new_char/$((_repo_cursor_index + 1))")
                        ;;
                esac
                ;;
            enter)
                run_tui_action
                if [ $? -eq 0 ]; then
                    _return_to_menu=1
                fi
                break
                ;;
            quit) break ;;
        esac
    done
    _restore_term

    # If user wants to return to menu, restart interactive mode
    if [ "$_return_to_menu" -eq 1 ]; then
        run_interactive_mode
    fi
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
    printf "  ${C_GREEN}status${C_RESET}\t\t\tChecks git status for all repos.\n"
    printf "  ${C_GREEN}help${C_RESET}\t\t\tShows this help message.\n\E[0m\n"
}

# --- Main Entry Point ---
main() {
    case "$1" in
        sync) run_cli_sync "$2" ;;
        push) run_cli_push ;;
        pull) run_cli_pull ;;
        status) run_cli_status ;;
        help|-h|--help) show_help ;;
        "") run_interactive_mode ;;
        *) _error "Invalid command: $1"; show_host_help; exit 1 ;;
    esac
}

main "$@"
