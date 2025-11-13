#!/usr/bin/env python3

import os
import subprocess
import sys
import curses

# Repository definitions
REPOSITORIES = {
    'front-Github_profile': {
        'https': 'https://github.com/diegonmarcos/diegonmarcos.git',
        'ssh': 'git@github.com:diegonmarcos/diegonmarcos.git',
        'public': True
    },
    'front-Github_io': {
        'https': 'https://github.com/diegonmarcos/diegonmarcos.github.io.git',
        'ssh': 'git@github.com:diegonmarcos/diegonmarcos.github.io.git',
        'public': True
    },
    'back-Mylibs': {
        'https': 'https://github.com/diegonmarcos/back-Mylibs.git',
        'ssh': 'git@github.com:diegonmarcos/back-Mylibs.git',
        'public': True
    },
    'back-System': {
        'https': 'https://github.com/diegonmarcos/back-System.git',
        'ssh': 'git@github.com:diegonmarcos/back-System.git',
        'public': True
    },
    'back-Algo': {
        'https': 'https://github.com/diegonmarcos/back-Algo.git',
        'ssh': 'git@github.com:diegonmarcos/back-Algo.git',
        'public': True
    },
    'back-Graphic': {
        'https': 'https://github.com/diegonmarcos/back-Graphic.git',
        'ssh': 'git@github.com:diegonmarcos/back-Graphic.git',
        'public': True
    },
    'cyber-Cyberwarfare': {
        'https': 'https://github.com/diegonmarcos/cyber-Cyberwarfare.git',
        'ssh': 'git@github.com:diegonmarcos/cyber-Cyberwarfare.git',
        'public': True
    },
    'ops-Tooling': {
        'https': 'https://github.com/diegonmarcos/ops-Tooling.git',
        'ssh': 'git@github.com:diegonmarcos/ops-Tooling.git',
        'public': True
    },
    'ml-MachineLearning': {
        'https': 'https://github.com/diegonmarcos/ml-MachineLearning.git',
        'ssh': 'git@github.com:diegonmarcos/ml-MachineLearning.git',
        'public': True
    },
    'ml-DataScience': {
        'https': 'https://github.com/diegonmarcos/ml-DataScience.git',
        'ssh': 'git@github.com:diegonmarcos/ml-DataScience.git',
        'public': True
    },
    'ml-Agentic': {
        'https': 'https://github.com/diegonmarcos/ml-Agentic.git',
        'ssh': 'git@github.com:diegonmarcos/ml-Agentic.git',
        'public': True
    },
    'front-Notes_md': {
        'https': 'https://github.com/diegonmarcos/front-Notes_md.git',
        'ssh': 'git@github.com:diegonmarcos/front-Notes_md.git',
        'public': False
    },
    'z-lecole42': {
        'https': 'https://github.com/diegonmarcos/lecole42.git',
        'ssh': 'git@github.com:diegonmarcos/lecole42.git',
        'public': False
    },
    'z-dev': {
        'https': 'https://github.com/diegonmarcos/dev.git',
        'ssh': 'git@github.com:diegonmarcos/dev.git',
        'public': False
    }
}

# Color pair constants
COLOR_HEADER = 1
COLOR_TITLE = 2
COLOR_HELP = 3
COLOR_SELECTED = 4
COLOR_HIGHLIGHT = 5
COLOR_BUTTON = 6
COLOR_DIVIDER = 7
COLOR_CURRENT = 8


class GitManager:
    def __init__(self):
        self.mode_selected = 1  # 0=HTTPS, 1=SSH
        self.strategy_selected = 1  # 0=LOCAL, 1=REMOTE
        self.action_selected = 0  # 0=PULL, 1=SYNC (default PULL)
        self.current_field = 0  # 0=mode, 1=strategy, 2=action, 3=run button
        self.total_fields = 4

    def init_colors(self):
        """Initialize color pairs."""
        curses.init_pair(COLOR_HEADER, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_TITLE, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(COLOR_HELP, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(COLOR_SELECTED, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_HIGHLIGHT, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(COLOR_BUTTON, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_DIVIDER, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(COLOR_CURRENT, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    def draw_interface(self, stdscr):
        """Draw the complete interface."""
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()

        # Check minimum terminal size
        if max_y < 30 or max_x < 80:
            stdscr.addstr(0, 0, "Terminal too small!")
            stdscr.addstr(1, 0, f"Minimum: 30 rows x 80 cols")
            stdscr.addstr(2, 0, f"Current: {max_y} rows x {max_x} cols")
            stdscr.addstr(4, 0, "Please resize and press any key...")
            stdscr.refresh()
            stdscr.getch()
            return

        line = 0

        # Header
        header = "╔══════════════════════════════════════════════════════════════════════╗"
        title = "║       Git Clone/Pull Manager - Diego's Repositories                 ║"
        footer_line = "╚══════════════════════════════════════════════════════════════════════╝"

        if line < max_y - 1:
            stdscr.addstr(line, 0, header, curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
        line += 1
        if line < max_y - 1:
            stdscr.addstr(line, 0, title, curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
        line += 1
        if line < max_y - 1:
            stdscr.addstr(line, 0, footer_line, curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
        line += 2

        # Help text (compact)
        if line < max_y - 1:
            stdscr.addstr(line, 2, "↑↓:", curses.color_pair(COLOR_HELP))
            stdscr.addstr("Navigate ", curses.A_NORMAL)
            stdscr.addstr("SPACE:", curses.color_pair(COLOR_HELP))
            stdscr.addstr("Toggle ", curses.A_NORMAL)
            stdscr.addstr("ENTER:", curses.color_pair(COLOR_HELP))
            stdscr.addstr("Execute ", curses.A_NORMAL)
            stdscr.addstr("q:", curses.color_pair(COLOR_HELP))
            stdscr.addstr("Quit", curses.A_NORMAL)
        line += 2

        # Divider
        if line < max_y - 1:
            stdscr.addstr(line, 0, "─" * 72, curses.color_pair(COLOR_DIVIDER))
        line += 1

        # MODE SELECTION
        if line < max_y - 1:
            stdscr.addstr(line, 2, "MODE: ", curses.color_pair(COLOR_TITLE) | curses.A_BOLD)
            stdscr.addstr("Choose authentication method", curses.A_NORMAL)
        line += 1

        # HTTPS option
        if self.current_field == 0:
            attr = curses.color_pair(COLOR_HIGHLIGHT) | curses.A_BOLD
        else:
            attr = curses.A_NORMAL

        if line < max_y - 1:
            stdscr.addstr(line, 4, " ", attr)
            if self.mode_selected == 0:
                stdscr.addstr("● ", curses.color_pair(COLOR_SELECTED) | curses.A_BOLD | attr)
            else:
                stdscr.addstr("○ ", attr)
            stdscr.addstr("HTTPS ", attr)
            stdscr.addstr("  - Public repositories only (11 repos)", curses.A_NORMAL)
        line += 1

        # SSH option
        if self.current_field == 0:
            attr = curses.color_pair(COLOR_HIGHLIGHT) | curses.A_BOLD
        else:
            attr = curses.A_NORMAL

        if line < max_y - 1:
            stdscr.addstr(line, 4, " ", attr)
            if self.mode_selected == 1:
                stdscr.addstr("● ", curses.color_pair(COLOR_SELECTED) | curses.A_BOLD | attr)
            else:
                stdscr.addstr("○ ", attr)
            stdscr.addstr("SSH   ", attr)
            stdscr.addstr("  - All repositories including private (14 repos)", curses.A_NORMAL)
        line += 2

        # Divider
        if line < max_y - 1:
            stdscr.addstr(line, 0, "─" * 72, curses.color_pair(COLOR_DIVIDER))
        line += 1

        # MERGE STRATEGY
        if line < max_y - 1:
            stdscr.addstr(line, 2, "STRATEGY: ", curses.color_pair(COLOR_TITLE) | curses.A_BOLD)
            stdscr.addstr("How to handle conflicts", curses.A_NORMAL)
        line += 1

        # LOCAL option
        if self.current_field == 1:
            attr = curses.color_pair(COLOR_HIGHLIGHT) | curses.A_BOLD
        else:
            attr = curses.A_NORMAL

        if line < max_y - 1:
            stdscr.addstr(line, 4, " ", attr)
            if self.strategy_selected == 0:
                stdscr.addstr("● ", curses.color_pair(COLOR_SELECTED) | curses.A_BOLD | attr)
            else:
                stdscr.addstr("○ ", attr)
            stdscr.addstr("LOCAL  ", attr)
            stdscr.addstr(" - Keep your local changes on conflicts (merge -X ours)", curses.A_NORMAL)
        line += 1

        # REMOTE option
        if self.current_field == 1:
            attr = curses.color_pair(COLOR_HIGHLIGHT) | curses.A_BOLD
        else:
            attr = curses.A_NORMAL

        if line < max_y - 1:
            stdscr.addstr(line, 4, " ", attr)
            if self.strategy_selected == 1:
                stdscr.addstr("● ", curses.color_pair(COLOR_SELECTED) | curses.A_BOLD | attr)
            else:
                stdscr.addstr("○ ", attr)
            stdscr.addstr("REMOTE ", attr)
            stdscr.addstr(" - Keep remote changes (merge -X theirs) ", curses.A_NORMAL)
            stdscr.addstr("[recommended]", curses.color_pair(COLOR_HELP))
        line += 2

        # Divider
        if line < max_y - 1:
            stdscr.addstr(line, 0, "─" * 72, curses.color_pair(COLOR_DIVIDER))
        line += 1

        # SYNC ACTION
        if line < max_y - 1:
            stdscr.addstr(line, 2, "ACTION: ", curses.color_pair(COLOR_TITLE) | curses.A_BOLD)
            stdscr.addstr("Choose sync direction", curses.A_NORMAL)
        line += 1

        # PULL option
        if self.current_field == 2:
            attr = curses.color_pair(COLOR_HIGHLIGHT) | curses.A_BOLD
        else:
            attr = curses.A_NORMAL

        if line < max_y - 1:
            stdscr.addstr(line, 4, " ", attr)
            if self.action_selected == 0:
                stdscr.addstr("● ", curses.color_pair(COLOR_SELECTED) | curses.A_BOLD | attr)
            else:
                stdscr.addstr("○ ", attr)
            stdscr.addstr("PULL   ", attr)
            stdscr.addstr(" - Only pull from remote (one-way: remote → local)", curses.A_NORMAL)
        line += 1

        # SYNC option
        if self.current_field == 2:
            attr = curses.color_pair(COLOR_HIGHLIGHT) | curses.A_BOLD
        else:
            attr = curses.A_NORMAL

        if line < max_y - 1:
            stdscr.addstr(line, 4, " ", attr)
            if self.action_selected == 1:
                stdscr.addstr("● ", curses.color_pair(COLOR_SELECTED) | curses.A_BOLD | attr)
            else:
                stdscr.addstr("○ ", attr)
            stdscr.addstr("SYNC   ", attr)
            stdscr.addstr(" - Bidirectional sync (pull then push) ", curses.A_NORMAL)
            stdscr.addstr("[⚠ pushes changes]", curses.color_pair(COLOR_HELP))
        line += 2

        # Divider
        if line < max_y - 1:
            stdscr.addstr(line, 0, "─" * 72, curses.color_pair(COLOR_DIVIDER))
        line += 1

        # RUN button
        button_text = "              [ ▶ RUN SYNC ]                    "
        if self.current_field == 3:
            attr = curses.color_pair(COLOR_SELECTED) | curses.A_REVERSE | curses.A_BOLD
        else:
            attr = curses.color_pair(COLOR_BUTTON) | curses.A_BOLD

        if line < max_y - 1:
            stdscr.addstr(line, 10, button_text, attr)
        line += 2

        # Current selection
        if line < max_y - 1:
            stdscr.addstr(line, 2, "Selection: ", curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
            mode_text = "HTTPS" if self.mode_selected == 0 else "SSH"
            strategy_text = "LOCAL" if self.strategy_selected == 0 else "REMOTE"
            action_text = "PULL" if self.action_selected == 0 else "SYNC"
            stdscr.addstr(mode_text, curses.color_pair(COLOR_CURRENT) | curses.A_BOLD)
            stdscr.addstr(" + ", curses.A_NORMAL)
            stdscr.addstr(strategy_text, curses.color_pair(COLOR_CURRENT) | curses.A_BOLD)
            stdscr.addstr(" + ", curses.A_NORMAL)
            stdscr.addstr(action_text, curses.color_pair(COLOR_CURRENT) | curses.A_BOLD)

        stdscr.refresh()

    def handle_key(self, key):
        """Handle keyboard input."""
        if key == curses.KEY_UP:
            self.current_field = (self.current_field - 1) % self.total_fields
        elif key == curses.KEY_DOWN:
            self.current_field = (self.current_field + 1) % self.total_fields
        elif key in (ord(' '), ord('\t')):
            self.toggle_selection()
        elif key == ord('\n'):  # Enter
            if self.current_field == 3:
                return 'execute'
            else:
                self.toggle_selection()
        elif key in (ord('q'), ord('Q')):
            return 'quit'
        return None

    def toggle_selection(self):
        """Toggle the current selection."""
        if self.current_field == 0:
            self.mode_selected = 1 - self.mode_selected
        elif self.current_field == 1:
            self.strategy_selected = 1 - self.strategy_selected
        elif self.current_field == 2:
            self.action_selected = 1 - self.action_selected

    def clone_or_pull(self, repo_name, url, merge_strategy, do_push=False):
        """Clone a repository if it doesn't exist, or pull if it does."""
        if os.path.isdir(repo_name):
            print(f"\033[96mPulling \033[1m{repo_name}\033[0m\033[96m (keeping {merge_strategy} version on conflicts)...")
            try:
                subprocess.run(
                    ['git', '-C', repo_name, 'pull', '-s', 'recursive', '-X', merge_strategy],
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(f"\033[92m  ✓ Pull Success\033[0m")

                # Push if sync mode enabled
                if do_push:
                    print(f"\033[96m  Pushing changes to remote...")
                    try:
                        subprocess.run(
                            ['git', '-C', repo_name, 'push'],
                            capture_output=True,
                            text=True,
                            check=True
                        )
                        print(f"\033[92m  ✓ Push Success\033[0m")
                    except subprocess.CalledProcessError:
                        print(f"\033[93m  ⚠ Push Failed (no changes or permission denied)\033[0m")

                return True
            except subprocess.CalledProcessError:
                print(f"\033[91m  ✗ Pull Failed\033[0m")
                return False
        else:
            print(f"\033[96mCloning \033[1m{repo_name}\033[0m\033[96m...")
            try:
                subprocess.run(
                    ['git', 'clone', url, repo_name],
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(f"\033[92m  ✓ Clone Success\033[0m")
                return True
            except subprocess.CalledProcessError:
                print(f"\033[91m  ✗ Clone Failed\033[0m")
                return False

    def process_repositories(self):
        """Process all repositories based on current selections."""
        # Exit curses mode
        curses.endwin()

        # Clear screen
        os.system('clear')

        # Determine settings
        url_type = 'https' if self.mode_selected == 0 else 'ssh'
        merge_strategy = 'ours' if self.strategy_selected == 0 else 'theirs'
        strategy_name = 'LOCAL' if self.strategy_selected == 0 else 'REMOTE'
        mode_name = 'HTTPS (Public only)' if self.mode_selected == 0 else 'SSH (All repos)'
        action_name = 'PULL ONLY' if self.action_selected == 0 else 'BIDIRECTIONAL SYNC (Pull + Push)'
        do_push = self.action_selected == 1

        # Print header
        print("\033[1m\033[96m╔══════════════════════════════════════════════════════════════════════╗\033[0m")
        print("\033[1m\033[96m║       Processing Repositories                                        ║\033[0m")
        print("\033[1m\033[96m╚══════════════════════════════════════════════════════════════════════╝\033[0m")
        print()
        print(f"\033[93mMode: \033[0m\033[1m{mode_name}\033[0m")
        print(f"\033[93mStrategy: \033[0m\033[1mKeep {strategy_name} changes on conflicts\033[0m")
        print(f"\033[93mAction: \033[0m\033[1m{action_name}\033[0m")
        print("\033[94m════════════════════════════════════════════════════════════════════════\033[0m")
        print()

        success_count = 0
        fail_count = 0

        for repo_name, repo_info in REPOSITORIES.items():
            # Skip private repos in HTTPS mode
            if self.mode_selected == 0 and not repo_info['public']:
                continue

            url = repo_info[url_type]
            if self.clone_or_pull(repo_name, url, merge_strategy, do_push):
                success_count += 1
            else:
                fail_count += 1
            print()

        print("\033[94m════════════════════════════════════════════════════════════════════════\033[0m")
        print("\033[1m\033[92mProcessing complete!\033[0m")
        print("\033[94m════════════════════════════════════════════════════════════════════════\033[0m")
        print()

    def run(self, stdscr):
        """Main loop."""
        curses.curs_set(0)  # Hide cursor
        self.init_colors()

        while True:
            self.draw_interface(stdscr)
            key = stdscr.getch()
            action = self.handle_key(key)

            if action == 'quit':
                break
            elif action == 'execute':
                self.process_repositories()
                print("\nPress Enter to continue...")
                input()
                # Reinitialize curses
                stdscr.clear()
                stdscr.refresh()


def show_usage():
    """Show usage information."""
    # Header
    print("\033[1m\033[96m╔══════════════════════════════════════════════════════════════════════╗\033[0m")
    print("\033[1m\033[96m║       Git Clone/Pull Manager - Help                                 ║\033[0m")
    print("\033[1m\033[96m╚══════════════════════════════════════════════════════════════════════╝\033[0m")
    print()

    # Usage
    print("\033[1m\033[93mUSAGE:\033[0m")
    print("  gcl.py \033[96m[MODE] [STRATEGY] [ACTION]\033[0m")
    print()

    # Description
    print("\033[97mGit Clone/Pull Manager - Manage multiple GitHub repositories\033[0m")
    print()

    # Arguments
    print("\033[1m\033[93mARGUMENTS:\033[0m")
    print("  \033[96mMODE       \033[0mAuthentication mode: \033[92m'https'\033[0m or \033[92m'ssh'\033[0m")
    print("  \033[96mSTRATEGY   \033[0mMerge strategy: \033[92m'local'\033[0m or \033[92m'remote'\033[0m\033[97m (default: remote)\033[0m")
    print("  \033[96mACTION     \033[0mSync action: \033[92m'pull'\033[0m or \033[92m'sync'\033[0m\033[97m (default: pull)\033[0m")
    print()

    # Examples
    print("\033[1m\033[93mEXAMPLES:\033[0m")
    print("  \033[95m# Interactive TUI mode (menu interface)\033[0m")
    print("  \033[1m\033[92mgcl.py\033[0m")
    print()
    print("  \033[95m# CLI: SSH with remote strategy, pull only\033[0m")
    print("  \033[1m\033[92mgcl.py ssh remote pull\033[0m")
    print()
    print("  \033[95m# CLI: SSH with remote strategy, bidirectional sync\033[0m")
    print("  \033[1m\033[92mgcl.py ssh remote sync\033[0m")
    print()
    print("  \033[95m# CLI: HTTPS with local strategy, pull only (uses defaults)\033[0m")
    print("  \033[1m\033[92mgcl.py https local\033[0m")
    print()
    print("  \033[95m# CLI: SSH with defaults (remote strategy, pull only)\033[0m")
    print("  \033[1m\033[92mgcl.py ssh\033[0m")
    print()

    # Modes
    print("\033[1m\033[93mMODES:\033[0m")
    print("  \033[92mhttps  \033[0m- Use HTTPS URLs (public repositories only - 11 repos)")
    print("  \033[92mssh    \033[0m- Use SSH URLs (all repositories including private - 14 repos)")
    print()

    # Strategies
    print("\033[1m\033[93mSTRATEGIES:\033[0m")
    print("  \033[92mlocal   \033[0m- Keep local changes on conflicts (merge -X ours)")
    print("  \033[92mremote  \033[0m- Keep remote changes on conflicts (merge -X theirs) \033[93m[recommended]\033[0m")
    print()

    # Actions
    print("\033[1m\033[93mACTIONS:\033[0m")
    print("  \033[92mpull    \033[0m- Only pull from remote (one-way: remote → local)")
    print("  \033[92msync    \033[0m- Bidirectional sync (pull then push) \033[93m[⚠ pushes local commits]\033[0m")
    print()

    # Footer
    print("\033[94m════════════════════════════════════════════════════════════════════════\033[0m")


def main():
    """Entry point."""
    manager = GitManager()

    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help', 'help'):
        show_usage()
        sys.exit(0)

    # Check if arguments provided (CLI mode) or no arguments (interactive mode)
    if len(sys.argv) > 1:
        # Command-line mode with positional arguments
        mode_arg = sys.argv[1]
        strategy_arg = sys.argv[2] if len(sys.argv) > 2 else 'remote'
        action_arg = sys.argv[3] if len(sys.argv) > 3 else 'pull'

        # Validate mode
        if mode_arg.lower() not in ['https', 'ssh']:
            print(f"Error: Invalid mode '{mode_arg}'. Use 'https' or 'ssh'.")
            show_usage()
            sys.exit(1)

        # Validate strategy
        if strategy_arg.lower() not in ['local', 'remote']:
            print(f"Error: Invalid strategy '{strategy_arg}'. Use 'local' or 'remote'.")
            show_usage()
            sys.exit(1)

        # Validate action
        if action_arg.lower() not in ['pull', 'sync']:
            print(f"Error: Invalid action '{action_arg}'. Use 'pull' or 'sync'.")
            show_usage()
            sys.exit(1)

        print("\033[1m\033[96m╔══════════════════════════════════════════════════════════════════════╗\033[0m")
        print("\033[1m\033[96m║       Git Clone/Pull Manager - Diego's Repositories                 ║\033[0m")
        print("\033[1m\033[96m╚══════════════════════════════════════════════════════════════════════╝\033[0m")
        print()

        # Set mode, strategy, and action
        manager.mode_selected = 0 if mode_arg.lower() == 'https' else 1
        manager.strategy_selected = 0 if strategy_arg.lower() == 'local' else 1
        manager.action_selected = 0 if action_arg.lower() == 'pull' else 1

        # Display settings
        mode_name = 'HTTPS (Public only)' if manager.mode_selected == 0 else 'SSH (All repos)'
        strategy_name = 'LOCAL' if manager.strategy_selected == 0 else 'REMOTE'
        action_name = 'PULL ONLY' if manager.action_selected == 0 else 'BIDIRECTIONAL SYNC (Pull + Push)'

        print(f"\033[93mMode: \033[0m\033[1m{mode_name}\033[0m")
        print(f"\033[93mStrategy: \033[0m\033[1mKeep {strategy_name} changes on conflicts\033[0m")
        print(f"\033[93mAction: \033[0m\033[1m{action_name}\033[0m")
        print("\033[94m════════════════════════════════════════════════════════════════════════\033[0m")
        print()

        # Process repositories
        success_count = 0
        fail_count = 0

        url_type = 'https' if manager.mode_selected == 0 else 'ssh'
        merge_strategy = 'ours' if manager.strategy_selected == 0 else 'theirs'
        do_push = manager.action_selected == 1

        for repo_name, repo_info in REPOSITORIES.items():
            # Skip private repos in HTTPS mode
            if manager.mode_selected == 0 and not repo_info['public']:
                continue

            url = repo_info[url_type]
            if manager.clone_or_pull(repo_name, url, merge_strategy, do_push):
                success_count += 1
            else:
                fail_count += 1
            print()

        print("\033[94m════════════════════════════════════════════════════════════════════════\033[0m")
        print(f"\033[1m\033[92mComplete! Success: {success_count} | Failed: {fail_count}\033[0m")
        print("\033[94m════════════════════════════════════════════════════════════════════════\033[0m")

    else:
        # Interactive TUI mode
        try:
            curses.wrapper(manager.run)
            print("Goodbye!")
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Exiting...")
            sys.exit(0)
        except curses.error as e:
            # This can happen if the terminal is resized too small
            print(f"An error occurred: {e}")
            print("Please ensure your terminal is large enough and try again.")
            sys.exit(1)


if __name__ == "__main__":
    main()