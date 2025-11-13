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


def draw_menu(stdscr, title, options, current_idx):
    """Draw the menu with the current selection highlighted."""
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    # Draw header
    header = "=== Git Clone/Pull Manager - Diego's Repositories ==="
    stdscr.addstr(0, max(0, (w - len(header)) // 2), header, curses.A_BOLD)

    # Draw title
    stdscr.addstr(2, 2, title, curses.A_UNDERLINE)

    # Draw options
    for idx, option in enumerate(options):
        y = 4 + idx
        if y >= h - 2:  # Prevent drawing outside screen
            break

        if idx == current_idx:
            # Highlight current selection
            stdscr.addstr(y, 4, f"→ {option}", curses.A_REVERSE | curses.A_BOLD)
        else:
            stdscr.addstr(y, 4, f"  {option}")

    # Draw instructions
    instructions = "Use ↑↓ arrows to navigate, Enter to select, q to quit"
    stdscr.addstr(h - 2, 2, instructions, curses.A_DIM)

    stdscr.refresh()


def show_menu(stdscr, title, options):
    """Show an interactive menu and return the selected index."""
    curses.curs_set(0)  # Hide cursor
    current_idx = 0

    # Initialize color pairs if available
    if curses.has_colors():
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)

    while True:
        draw_menu(stdscr, title, options, current_idx)

        key = stdscr.getch()

        if key == curses.KEY_UP:
            current_idx = (current_idx - 1) % len(options)
        elif key == curses.KEY_DOWN:
            current_idx = (current_idx + 1) % len(options)
        elif key == ord('\n'):  # Enter key
            return current_idx
        elif key == ord('q') or key == ord('Q'):
            return None


def clone_or_pull(repo_name, url, merge_strategy):
    """Clone a repository if it doesn't exist, or pull if it does."""
    if os.path.isdir(repo_name):
        print(f"Pulling {repo_name} (keeping {merge_strategy} version on conflicts)...")
        try:
            result = subprocess.run(
                ['git', '-C', repo_name, 'pull', '-s', 'recursive', '-X', merge_strategy],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"  ✓ {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Error: {e.stderr.strip()}")
            return False
    else:
        print(f"Cloning {repo_name}...")
        try:
            result = subprocess.run(
                ['git', 'clone', url, repo_name],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"  ✓ Cloned successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Error: {e.stderr.strip()}")
            return False


def process_repositories(mode, strategy):
    """Process all repositories based on mode and strategy."""
    # Clear screen for repository processing
    os.system('clear')

    url_type = 'https' if mode == 0 else 'ssh'
    merge_strategy = 'ours' if strategy == 0 else 'theirs'
    strategy_name = 'LOCAL' if strategy == 0 else 'REMOTE'
    mode_name = 'HTTPS (Public only)' if mode == 0 else 'SSH (All repos)'

    print("=" * 70)
    print(f"  Git Clone/Pull Manager - Diego's Repositories")
    print("=" * 70)
    print(f"Mode: {mode_name}")
    print(f"Strategy: Keep {strategy_name} changes on conflicts")
    print("=" * 70)
    print()

    success_count = 0
    fail_count = 0
    processed = 0

    for repo_name, repo_info in REPOSITORIES.items():
        # Skip private repos in HTTPS mode
        if mode == 0 and not repo_info['public']:
            continue

        url = repo_info[url_type]
        if clone_or_pull(repo_name, url, merge_strategy):
            success_count += 1
        else:
            fail_count += 1
        processed += 1
        print()

    print("=" * 70)
    print(f"Summary: {success_count} successful, {fail_count} failed, {processed} total")
    print("=" * 70)
    print()


def main(stdscr):
    """Main program loop with curses interface."""
    while True:
        # Main menu - Select mode
        mode_options = [
            "HTTPS - Public repositories only (11 repos)",
            "SSH   - All repositories including private (14 repos)",
            "Exit"
        ]

        mode_index = show_menu(stdscr, "Select Mode:", mode_options)

        if mode_index is None or mode_index == 2:
            break

        # Strategy menu
        strategy_options = [
            "Keep LOCAL changes on conflicts (merge -X ours)",
            "Keep REMOTE changes on conflicts (merge -X theirs) [recommended]",
            "Back to main menu"
        ]

        strategy_index = show_menu(
            stdscr,
            f"Selected: {mode_options[mode_index]}\n\nSelect Merge Strategy:",
            strategy_options
        )

        if strategy_index is None or strategy_index == 2:
            continue

        # Exit curses mode temporarily for git operations
        curses.endwin()

        # Process repositories
        process_repositories(mode_index, strategy_index)

        # Wait for user
        input("\nPress Enter to continue...")

        # Reinitialize curses
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
        print("\nGoodbye!")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)
