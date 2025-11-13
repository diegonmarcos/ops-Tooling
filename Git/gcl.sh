#!/bin/sh

# POSIX-compliant single-page interactive git clone/pull manager

# Repository lists
PUBLIC_REPOS="
profile:https://github.com/diegonmarcos/diegonmarcos.git:git@github.com:diegonmarcos/diegonmarcos.git
back-Mylibs:https://github.com/diegonmarcos/back-Mylibs.git:git@github.com:diegonmarcos/back-Mylibs.git
back-System:https://github.com/diegonmarcos/back-System.git:git@github.com:diegonmarcos/back-System.git
back-Algo:https://github.com/diegonmarcos/back-Algo.git:git@github.com:diegonmarcos/back-Algo.git
back-Graphic:https://github.com/diegonmarcos/back-Graphic.git:git@github.com:diegonmarcos/back-Graphic.git
website:https://github.com/diegonmarcos/diegonmarcos.github.io.git:git@github.com:diegonmarcos/diegonmarcos.github.io.git
cyber-Cyberwarfare:https://github.com/diegonmarcos/cyber-Cyberwarfare.git:git@github.com:diegonmarcos/cyber-Cyberwarfare.git
ops-Tooling:https://github.com/diegonmarcos/ops-Tooling.git:git@github.com:diegonmarcos/ops-Tooling.git
ml-MachineLearning:https://github.com/diegonmarcos/ml-MachineLearning.git:git@github.com:diegonmarcos/ml-MachineLearning.git
ml-DataScience:https://github.com/diegonmarcos/ml-DataScience.git:git@github.com:diegonmarcos/ml-DataScience.git
ml-Agentic:https://github.com/diegonmarcos/ml-Agentic.git:git@github.com:diegonmarcos/ml-Agentic.git
"

PRIVATE_REPOS="
front-Notes_md:https://github.com/diegonmarcos/front-Notes_md.git:git@github.com:diegonmarcos/front-Notes_md.git
lecole42:https://github.com/diegonmarcos/lecole42.git:git@github.com:diegonmarcos/lecole42.git
dev:https://github.com/diegonmarcos/dev.git:git@github.com:diegonmarcos/dev.git
"

# State variables
_mode_selected=1          # 0=HTTPS, 1=SSH (default)
_strategy_selected=1      # 0=LOCAL, 1=REMOTE (default)
_current_field=0          # 0=mode, 1=strategy, 2=run button
_total_fields=3

# Terminal control functions
_clear_screen() {
    tput clear
}

_move_cursor() {
    tput cup "$1" "$2"
}

_hide_cursor() {
    tput civis 2>/dev/null || true
}

_show_cursor() {
    tput cnorm 2>/dev/null || true
}

_bold() {
    tput bold 2>/dev/null || true
}

_reverse() {
    tput rev 2>/dev/null || true
}

_normal() {
    tput sgr0 2>/dev/null || true
}

# Color functions
_color_red() {
    tput setaf 1 2>/dev/null || true
}

_color_green() {
    tput setaf 2 2>/dev/null || true
}

_color_yellow() {
    tput setaf 3 2>/dev/null || true
}

_color_blue() {
    tput setaf 4 2>/dev/null || true
}

_color_magenta() {
    tput setaf 5 2>/dev/null || true
}

_color_cyan() {
    tput setaf 6 2>/dev/null || true
}

_color_white() {
    tput setaf 7 2>/dev/null || true
}

_bg_green() {
    tput setab 2 2>/dev/null || true
}

_bg_blue() {
    tput setab 4 2>/dev/null || true
}

_save_term() {
    _SAVED_TERM=$(stty -g)
}

_restore_term() {
    stty "$_SAVED_TERM" 2>/dev/null || true
    _show_cursor
}

# Read a single character
_read_key() {
    _char=""
    _key=""

    _char=$(dd bs=1 count=1 2>/dev/null)

    if [ "$_char" = "$(printf '\033')" ]; then
        _char2=$(dd bs=1 count=1 2>/dev/null)
        if [ "$_char2" = "[" ]; then
            _char3=$(dd bs=1 count=1 2>/dev/null)
            case "$_char3" in
                A) _key="up" ;;
                B) _key="down" ;;
                C) _key="right" ;;
                D) _key="left" ;;
                *) _key="unknown" ;;
            esac
        else
            _key="esc"
        fi
    elif [ "$_char" = "$(printf '\n')" ] || [ "$_char" = "$(printf '\r')" ]; then
        _key="enter"
    elif [ "$_char" = "$(printf '\t')" ] || [ "$_char" = " " ]; then
        _key="space"
    elif [ "$_char" = "q" ] || [ "$_char" = "Q" ]; then
        _key="quit"
    else
        _key="other"
    fi

    printf "%s" "$_key"
}

# Draw checkbox or radio button
_draw_checkbox() {
    _selected="$1"
    if [ "$_selected" = "1" ]; then
        printf "[✓]"
    else
        printf "[ ]"
    fi
}

_draw_radio() {
    _selected="$1"
    if [ "$_selected" = "1" ]; then
        printf "(●)"
    else
        printf "( )"
    fi
}

# Draw the complete interface
draw_interface() {
    _clear_screen
    _move_cursor 0 0

    # Header
    _bold
    _color_cyan
    printf "╔══════════════════════════════════════════════════════════════════════╗\n"
    printf "║       Git Clone/Pull Manager - Diego's Repositories                 ║\n"
    printf "╚══════════════════════════════════════════════════════════════════════╝\n"
    _normal
    printf "\n"

    # Description
    _color_white
    printf "  "
    _bold
    printf "Description: "
    _normal
    _color_white
    printf "Manage multiple GitHub repositories with a single command.\n"
    printf "               Clone new repos or pull updates from all your projects at once.\n"
    _normal
    printf "\n"

    # Help text
    _color_yellow
    printf "  Navigation: "
    _normal
    printf "↑↓ arrows | "
    _color_yellow
    printf "Select: "
    _normal
    printf "SPACE/TAB | "
    _color_yellow
    printf "Execute: "
    _normal
    printf "ENTER | "
    _color_yellow
    printf "Quit: "
    _normal
    printf "q\n"
    printf "\n"
    _color_blue
    printf "────────────────────────────────────────────────────────────────────────\n"
    _normal
    printf "\n"

    # Section 1: Mode selection
    _line=11
    _move_cursor $_line 2
    _bold
    _color_magenta
    printf "MODE SELECTION"
    _normal

    _line=$((_line + 1))
    _move_cursor $_line 2
    _color_white
    printf "Choose how to authenticate with GitHub:"
    _normal

    _line=$((_line + 2))
    _move_cursor $_line 4

    # Highlight if this is the current field
    if [ "$_current_field" = "0" ]; then
        _bg_blue
        _bold
    fi

    if [ "$_mode_selected" = "0" ]; then
        _color_green
        printf " ● "
        _normal
        if [ "$_current_field" = "0" ]; then
            _bg_blue
            _bold
        fi
        printf "HTTPS "
    else
        _color_white
        printf " ○ HTTPS "
    fi
    _normal
    _color_white
    printf "  - Public repositories only (11 repos)"
    _normal

    _line=$((_line + 1))
    _move_cursor $_line 4

    if [ "$_current_field" = "0" ]; then
        _bg_blue
        _bold
    fi

    if [ "$_mode_selected" = "1" ]; then
        _color_green
        printf " ● "
        _normal
        if [ "$_current_field" = "0" ]; then
            _bg_blue
            _bold
        fi
        printf "SSH   "
    else
        _color_white
        printf " ○ SSH   "
    fi
    _normal
    _color_white
    printf "  - All repositories including private (14 repos)"
    _normal

    # Section 2: Strategy selection
    _line=$((_line + 3))
    _move_cursor $_line 2
    _color_blue
    printf "────────────────────────────────────────────────────────────────────────"
    _normal

    _line=$((_line + 2))
    _move_cursor $_line 2
    _bold
    _color_magenta
    printf "MERGE STRATEGY"
    _normal

    _line=$((_line + 1))
    _move_cursor $_line 2
    _color_white
    printf "How to handle conflicts when pulling:"
    _normal

    _line=$((_line + 2))
    _move_cursor $_line 4

    if [ "$_current_field" = "1" ]; then
        _bg_blue
        _bold
    fi

    if [ "$_strategy_selected" = "0" ]; then
        _color_green
        printf " ● "
        _normal
        if [ "$_current_field" = "1" ]; then
            _bg_blue
            _bold
        fi
        printf "LOCAL  "
    else
        _color_white
        printf " ○ LOCAL  "
    fi
    _normal
    _color_white
    printf " - Keep your local changes on conflicts (merge -X ours)"
    _normal

    _line=$((_line + 1))
    _move_cursor $_line 4

    if [ "$_current_field" = "1" ]; then
        _bg_blue
        _bold
    fi

    if [ "$_strategy_selected" = "1" ]; then
        _color_green
        printf " ● "
        _normal
        if [ "$_current_field" = "1" ]; then
            _bg_blue
            _bold
        fi
        printf "REMOTE "
    else
        _color_white
        printf " ○ REMOTE "
    fi
    _normal
    _color_white
    printf " - Keep remote changes on conflicts (merge -X theirs) "
    _color_yellow
    printf "[recommended]"
    _normal

    # Execute button
    _line=$((_line + 3))
    _move_cursor $_line 2
    _color_blue
    printf "────────────────────────────────────────────────────────────────────────"
    _normal

    _line=$((_line + 2))
    _move_cursor $_line 4

    if [ "$_current_field" = "2" ]; then
        _bg_green
        _bold
        printf "                    [ ▶ RUN CLONE/PULL ]                    "
        _normal
    else
        _color_green
        _bold
        printf "                    [ ▶ RUN CLONE/PULL ]                    "
        _normal
    fi

    # Footer
    _line=$((_line + 3))
    _move_cursor $_line 2
    _color_blue
    printf "────────────────────────────────────────────────────────────────────────"
    _normal

    _line=$((_line + 1))
    _move_cursor $_line 2
    _bold
    _color_cyan
    printf "Current Selection: "
    _normal

    if [ "$_mode_selected" = "0" ]; then
        _color_yellow
        _bold
        printf "HTTPS"
        _normal
    else
        _color_yellow
        _bold
        printf "SSH"
        _normal
    fi

    _color_white
    printf " + "
    _normal

    if [ "$_strategy_selected" = "0" ]; then
        _color_yellow
        _bold
        printf "LOCAL"
        _normal
    else
        _color_yellow
        _bold
        printf "REMOTE"
        _normal
    fi

    # Move cursor away
    _move_cursor $((_line + 2)) 0
}

# Clone or pull repository
clone_or_pull() {
    _merge_strategy="$1"
    _repo="$2"
    _url="$3"

    if [ -d "$_repo" ]; then
        _color_cyan
        printf "Pulling "
        _bold
        printf "%s" "$_repo"
        _normal
        _color_cyan
        printf " (keeping %s version on conflicts)...\n" "$_merge_strategy"
        _normal
        if git -C "$_repo" pull -s recursive -X "$_merge_strategy" >/dev/null 2>&1; then
            _color_green
            printf "  ✓ Success\n"
            _normal
            return 0
        else
            _color_red
            printf "  ✗ Failed\n"
            _normal
            return 1
        fi
    else
        _color_cyan
        printf "Cloning "
        _bold
        printf "%s" "$_repo"
        _normal
        _color_cyan
        printf "...\n"
        _normal
        if git clone "$_url" "$_repo" >/dev/null 2>&1; then
            _color_green
            printf "  ✓ Success\n"
            _normal
            return 0
        else
            _color_red
            printf "  ✗ Failed\n"
            _normal
            return 1
        fi
    fi
}

# Process repositories
process_repositories() {
    _restore_term
    _clear_screen

    # Determine URL type and merge strategy
    if [ "$_mode_selected" = "0" ]; then
        _url_type="https"
        _mode_name="HTTPS (Public only)"
        _repos="$PUBLIC_REPOS"
    else
        _url_type="ssh"
        _mode_name="SSH (All repos)"
        _repos="${PUBLIC_REPOS}${PRIVATE_REPOS}"
    fi

    if [ "$_strategy_selected" = "0" ]; then
        _merge_strategy="ours"
        _strategy_name="LOCAL"
    else
        _merge_strategy="theirs"
        _strategy_name="REMOTE"
    fi

    _bold
    _color_cyan
    printf "╔══════════════════════════════════════════════════════════════════════╗\n"
    printf "║       Processing Repositories                                        ║\n"
    printf "╚══════════════════════════════════════════════════════════════════════╝\n"
    _normal
    printf "\n"
    _color_yellow
    printf "Mode: "
    _normal
    _bold
    printf "%s\n" "$_mode_name"
    _normal
    _color_yellow
    printf "Strategy: "
    _normal
    _bold
    printf "Keep %s changes on conflicts\n" "$_strategy_name"
    _normal
    _color_blue
    printf "════════════════════════════════════════════════════════════════════════\n"
    _normal
    printf "\n"

    _success=0
    _fail=0

    # Process each repository
    printf "%s" "$_repos" | while IFS=: read -r _repo _https_url _ssh_url; do
        [ -z "$_repo" ] && continue

        if [ "$_url_type" = "https" ]; then
            _url="$_https_url"
        else
            _url="$_ssh_url"
        fi

        if clone_or_pull "$_merge_strategy" "$_repo" "$_url"; then
            _success=$((_success + 1))
        else
            _fail=$((_fail + 1))
        fi
        printf "\n"
    done

    _color_blue
    printf "════════════════════════════════════════════════════════════════════════\n"
    _normal
    _color_green
    _bold
    printf "Processing complete!\n"
    _normal
    _color_blue
    printf "════════════════════════════════════════════════════════════════════════\n"
    _normal
    printf "\n"
}

# Main loop
main() {
    trap '_restore_term' EXIT INT TERM
    _save_term

    stty -icanon -echo min 1 time 0
    _hide_cursor

    while true; do
        draw_interface

        _key=$(_read_key)

        case "$_key" in
            up)
                _current_field=$((_current_field - 1))
                [ "$_current_field" -lt 0 ] && _current_field=$((_total_fields - 1))
                ;;
            down)
                _current_field=$((_current_field + 1))
                [ "$_current_field" -ge "$_total_fields" ] && _current_field=0
                ;;
            space)
                # Toggle current selection
                if [ "$_current_field" = "0" ]; then
                    # Toggle mode
                    if [ "$_mode_selected" = "0" ]; then
                        _mode_selected=1
                    else
                        _mode_selected=0
                    fi
                elif [ "$_current_field" = "1" ]; then
                    # Toggle strategy
                    if [ "$_strategy_selected" = "0" ]; then
                        _strategy_selected=1
                    else
                        _strategy_selected=0
                    fi
                elif [ "$_current_field" = "2" ]; then
                    # Run button pressed with space
                    process_repositories
                    printf "\nPress Enter to continue..."
                    _restore_term
                    read -r _dummy
                    _save_term
                    stty -icanon -echo min 1 time 0
                    _hide_cursor
                fi
                ;;
            enter)
                # Execute if on run button, otherwise toggle
                if [ "$_current_field" = "2" ]; then
                    process_repositories
                    printf "\nPress Enter to continue..."
                    _restore_term
                    read -r _dummy
                    _save_term
                    stty -icanon -echo min 1 time 0
                    _hide_cursor
                else
                    # Same as space for other fields
                    if [ "$_current_field" = "0" ]; then
                        if [ "$_mode_selected" = "0" ]; then
                            _mode_selected=1
                        else
                            _mode_selected=0
                        fi
                    elif [ "$_current_field" = "1" ]; then
                        if [ "$_strategy_selected" = "0" ]; then
                            _strategy_selected=1
                        else
                            _strategy_selected=0
                        fi
                    fi
                fi
                ;;
            quit)
                break
                ;;
        esac
    done

    _restore_term
    _clear_screen
    printf "Goodbye!\n"
}

main
