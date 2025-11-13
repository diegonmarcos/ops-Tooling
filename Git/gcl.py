#!/usr/bin/env python3

import os
import subprocess
import sys
import curses

# Repository definitions
REPOSITORIES = {
    'profile': {
        'https': 'https://github.com/diegonmarcos/diegonmarcos.git',
        'ssh': 'git@github.com:diegonmarcos/diegonmarcos.git',
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
    'website': {
        'https': 'https://github.com/diegonmarcos/diegonmarcos.github.io.git',
        'ssh': 'git@github.com:diegonmarcos/diegonmarcos.github.io.git',
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
    'lecole42': {
        'https': 'https://github.com/diegonmarcos/lecole42.git',
        'ssh': 'git@github.com:diegonmarcos/lecole42.git',
        'public': False
    },
    'dev': {
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
        self.current_field = 0  # 0=mode, 1=strategy, 2=run button
        self.total_fields = 3

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
        if max_y < 25 or max_x < 74:
            stdscr.addstr(0, 0, "Terminal too small!")
            stdscr.addstr(1, 0, f"Minimum: 25 rows x 74 cols")
            stdscr.addstr(2, 0, f"Current: {max_y} rows x {max_x} cols")
            stdscr.addstr(4, 0, "Please resize and press any key...")
            stdscr.refresh()
            stdscr.getch()
            return

        line = 0

        # Header
        header = "╔══════════════════════════════════════════════════════════════════════╗"
        title = "║   Git Clone/Pull Manager - Manage all repos in one command          ║"
        footer_line = "╚══════════════════════════════════════════════════════════════════════╝"

        if line < max_y - 1:
            stdscr.addstr(line, 0, header, curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
        line += 1
        if line < max_y - 1:
            stdscr.addstr(line, 0, title, curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
        line += 1
        if line < max_y - 1:
            stdscr.addstr(line, 0, footer_line, curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
        line += 1

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
        line += 1

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

        # RUN button
        button_text = "              [ ▶ RUN CLONE/PULL ]              "
        if self.current_field == 2:
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
            stdscr.addstr(mode_text, curses.color_pair(COLOR_CURRENT) | curses.A_BOLD)
            stdscr.addstr(" + ", curses.A_NORMAL)
            stdscr.addstr(strategy_text, curses.color_pair(COLOR_CURRENT) | curses.A_BOLD)

        stdscr.refresh()

    def handle_key(self, key):
        """Handle keyboard input."""
        if key == curses.KEY_UP:
            self.current_field = (self.current_field - 1) % self.total_fields
        elif key == curses.KEY_DOWN:
            self.current_field = (self.current_field + 1) % self.total_fields
        elif key in (ord(' '), ord('\t')):  # Space or Tab
            self.toggle_selection()
        elif key == ord('\n'):  # Enter
            if self.current_field == 2:
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

    def clone_or_pull(self, repo_name, url, merge_strategy):
        """Clone a repository if it doesn't exist, or pull if it does."""
        if os.path.isdir(repo_name):
            print(f"\033[96mPulling \033[1m{repo_name}\033[0m\033[96m (keeping {merge_strategy} version on conflicts)...\033[0m")
            try:
                subprocess.run(
                    ['git', '-C', repo_name, 'pull', '-s', 'recursive', '-X', merge_strategy],
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(f"\033[92m  ✓ Success\033[0m")
                return True
            except subprocess.CalledProcessError:
                print(f"\033[91m  ✗ Failed\033[0m")
                return False
        else:
            print(f"\033[96mCloning \033[1m{repo_name}\033[0m\033[96m...\033[0m")
            try:
                subprocess.run(
                    ['git', 'clone', url, repo_name],
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(f"\033[92m  ✓ Success\033[0m")
                return True
            except subprocess.CalledProcessError:
                print(f"\033[91m  ✗ Failed\033[0m")
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

        # Print header
        print("\033[1m\033[96m╔══════════════════════════════════════════════════════════════════════╗\033[0m")
        print("\033[1m\033[96m║       Processing Repositories                                        ║\033[0m")
        print("\033[1m\033[96m╚══════════════════════════════════════════════════════════════════════╝\033[0m")
        print()
        print(f"\033[93mMode: \033[0m\033[1m{mode_name}\033[0m")
        print(f"\033[93mStrategy: \033[0m\033[1mKeep {strategy_name} changes on conflicts\033[0m")
        print("\033[94m════════════════════════════════════════════════════════════════════════\033[0m")
        print()

        success_count = 0
        fail_count = 0

        for repo_name, repo_info in REPOSITORIES.items():
            # Skip private repos in HTTPS mode
            if self.mode_selected == 0 and not repo_info['public']:
                continue

            url = repo_info[url_type]
            if self.clone_or_pull(repo_name, url, merge_strategy):
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


def main():
    """Entry point."""
    manager = GitManager()
    try:
        curses.wrapper(manager.run)
        print("Goodbye!")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
