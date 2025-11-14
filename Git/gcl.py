#!/usr/bin/env python3
"""
gcl.py - A Python git clone/pull/push manager with TUI and CLI modes.
Converted from gcl.sh with identical functionality.
"""

import os
import sys
import subprocess
import termios
import tty
from typing import List, Tuple, Optional

# --- Configuration: Repository Lists ---
PUBLIC_REPOS = """
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
"""

PRIVATE_REPOS = """
front-Notes_md:git@github.com:diegonmarcos/front-Notes_md.git
z-lecole42:git@github.com:diegonmarcos/lecole42.git
z-dev:git@github.com:diegonmarcos/dev.git
"""

ALL_REPOS = PUBLIC_REPOS + PRIVATE_REPOS

# --- Color and Terminal Control ---
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    BG_BLUE = "\033[44m"
    BG_GREEN = "\033[42m"


class Terminal:
    """Terminal control utilities"""

    def __init__(self):
        self.saved_settings = None

    @staticmethod
    def clear_screen():
        print("\033[2J\033[H", end="", flush=True)

    @staticmethod
    def move_cursor(row: int, col: int):
        print(f"\033[{row};{col}H", end="", flush=True)

    @staticmethod
    def hide_cursor():
        print("\033[?25l", end="", flush=True)

    @staticmethod
    def show_cursor():
        print("\033[?25h", end="", flush=True)

    def save_term(self):
        self.saved_settings = termios.tcgetattr(sys.stdin)

    def restore_term(self):
        if self.saved_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.saved_settings)
        self.show_cursor()

    @staticmethod
    def set_raw_mode():
        tty.setraw(sys.stdin)


# --- Helper Functions ---
def log(message: str):
    print(f"{Colors.CYAN}==>{Colors.RESET} {Colors.BOLD}{message}{Colors.RESET}")


def success(message: str):
    print(f"{Colors.GREEN}  ✓ {message}{Colors.RESET}")


def error(message: str):
    print(f"{Colors.RED}  ✗ {message}{Colors.RESET}")


def warn(message: str):
    print(f"{Colors.YELLOW}  ⚠ {message}{Colors.RESET}")


def parse_repos(repo_string: str) -> List[Tuple[str, str]]:
    """Parse repository configuration string into list of (name, url) tuples"""
    repos = []
    for line in repo_string.strip().split('\n'):
        line = line.strip()
        if line and ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                repos.append((parts[0], parts[1]))
    return repos


def get_repo_url(repo_name: str) -> Optional[str]:
    """Get repository URL by name"""
    for name, url in parse_repos(ALL_REPOS):
        if name == repo_name:
            return url
    return None


# --- Core Git Functions ---
def process_repo(repo_dir: str, repo_url: str, strategy: str, action: str):
    """Process a single repository with the given action"""
    log(f"Processing '{repo_dir}'")

    if not os.path.isdir(repo_dir):
        log(f"Cloning '{repo_dir}'...")
        result = subprocess.run(['git', 'clone', '-q', repo_url, repo_dir],
                              capture_output=True)
        if result.returncode == 0:
            success("Clone complete.")
        else:
            error("Clone failed.")
        print()
        return

    if action in ['sync', 'pull']:
        print(f"  Pulling with strategy: {Colors.BOLD}{strategy}{Colors.RESET}")
        result = subprocess.run(['git', '-C', repo_dir, 'pull', '-q',
                               f'--strategy-option={strategy}'],
                              capture_output=True)
        if result.returncode == 0:
            success("Pull complete.")
            if action == 'sync':
                print("  Pushing changes...")
                result = subprocess.run(['git', '-C', repo_dir, 'push', '-q'],
                                      capture_output=True)
                if result.returncode == 0:
                    success("Push complete.")
                else:
                    warn("Push failed (no changes or permissions issue).")
        else:
            error("Pull failed.")

    elif action == 'push':
        print("  Staging all changes...")
        subprocess.run(['git', '-C', repo_dir, 'add', '.'])

        # Check if there are staged changes
        result = subprocess.run(['git', '-C', repo_dir, 'diff-index', '--quiet',
                               '--cached', 'HEAD', '--'],
                              capture_output=True)
        if result.returncode != 0:  # There are changes
            print("  Found changes, committing with default message 'fixes'...")
            result = subprocess.run(['git', '-C', repo_dir, 'commit', '-q', '-m', 'fixes'],
                                  capture_output=True)
            if result.returncode == 0:
                success("Commit complete.")
            else:
                error("Commit failed unexpectedly.")

        print("  Pushing changes...")
        result = subprocess.run(['git', '-C', repo_dir, 'push', '-q'],
                              capture_output=True)
        if result.returncode == 0:
            success("Push complete.")
        else:
            warn("Push failed (no changes or permissions issue).")

    print()


def check_repo_status(repo_dir: str, repo_url: str):
    """Check git status of a repository"""
    if not os.path.isdir(repo_dir):
        warn(f"'{repo_dir}' not cloned yet.")
        print()
        return

    log(f"Checking '{repo_dir}'")

    # Check for uncommitted changes
    result = subprocess.run(['git', '-C', repo_dir, 'diff-index', '--quiet', 'HEAD', '--'],
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if result.returncode != 0:
        warn("Has uncommitted changes (staged or unstaged)")
        print(f"  {Colors.YELLOW}Files changed:{Colors.RESET}")
        result = subprocess.run(['git', '-C', repo_dir, 'status', '--short'],
                              capture_output=True, text=True)
        for line in result.stdout.strip().split('\n'):
            if line:
                print(f"    {line}")
    else:
        success("Working tree clean")

    # Check for unpushed commits
    result = subprocess.run(['git', '-C', repo_dir, 'rev-parse', '@{u}'],
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if result.returncode == 0:
        # Branch tracks a remote
        result = subprocess.run(['git', '-C', repo_dir, 'log', '@{u}..', '--oneline'],
                              capture_output=True, text=True)
        commits = [l for l in result.stdout.strip().split('\n') if l]
        unpushed = len(commits)
        if unpushed > 0:
            warn(f"Has {unpushed} unpushed commit(s)")
            print(f"  {Colors.YELLOW}Unpushed commits:{Colors.RESET}")
            for line in commits:
                print(f"    {line}")
        else:
            success("All commits pushed")
    else:
        warn("Branch does not track a remote")

    print()


# --- CLI Actions ---
def run_cli_sync(strategy: str = 'remote', repos_filter: Optional[List[str]] = None):
    """Run bidirectional sync"""
    git_strategy = 'theirs' if strategy == 'remote' else 'ours'
    log(f"Starting Bidirectional Sync (Strategy: {git_strategy})")

    repos = parse_repos(ALL_REPOS)
    for repo_dir, repo_url in repos:
        if repos_filter is None or repo_dir in repos_filter:
            process_repo(repo_dir, repo_url, git_strategy, 'sync')


def run_cli_push(repos_filter: Optional[List[str]] = None):
    """Run push to all repositories"""
    log("Starting Push")

    repos = parse_repos(ALL_REPOS)
    for repo_dir, repo_url in repos:
        if repos_filter is None or repo_dir in repos_filter:
            process_repo(repo_dir, repo_url, 'none', 'push')


def run_cli_pull(repos_filter: Optional[List[str]] = None):
    """Run forced pull (remote overwrites local)"""
    log("Starting Forced Pull (Remote Overwrites Local on Conflict)")

    repos = parse_repos(ALL_REPOS)
    for repo_dir, repo_url in repos:
        if repos_filter is None or repo_dir in repos_filter:
            process_repo(repo_dir, repo_url, 'theirs', 'pull')


def run_cli_status(repos_filter: Optional[List[str]] = None):
    """Check git status for all repositories"""
    log("Checking Git Status for Repositories")

    repos = parse_repos(ALL_REPOS)
    for repo_dir, repo_url in repos:
        if repos_filter is None or repo_dir in repos_filter:
            check_repo_status(repo_dir, repo_url)


# --- TUI Functions ---
class TUIState:
    """State management for the TUI"""

    def __init__(self):
        self.strategy_selected = 1  # 0=LOCAL, 1=REMOTE (default)
        self.action_selected = 0    # 0=SYNC, 1=PUSH, 2=PULL, 3=STATUS
        self.repo_cursor_index = 0
        self.current_field = 0
        self.total_fields = 4

        # Parse repositories
        self.repos = parse_repos(ALL_REPOS)
        self.repo_count = len(self.repos)
        self.repo_selection = [True] * self.repo_count  # All selected by default

    def get_selected_repos(self) -> List[str]:
        """Get list of selected repository names"""
        return [self.repos[i][0] for i in range(self.repo_count)
                if self.repo_selection[i]]


def read_key() -> str:
    """Read a single key press and return its meaning"""
    char = sys.stdin.read(1)

    if char == '\033':  # Escape sequence
        next_chars = sys.stdin.read(2)
        if next_chars == '[A':
            return 'up'
        elif next_chars == '[B':
            return 'down'
    elif char in ['\n', '\r']:
        return 'enter'
    elif char == ' ':
        return 'space'
    elif char == '\t':
        return 'tab'
    elif char.lower() == 'a':
        return 'selectall'
    elif char.lower() == 'u':
        return 'unselectall'
    elif char.lower() == 'q':
        return 'quit'

    return ''


def draw_interface(state: TUIState):
    """Draw the TUI interface"""
    Terminal.clear_screen()
    line = 1

    # Header
    Terminal.move_cursor(line, 1)
    print(f"{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════╗", end="")
    line += 1
    Terminal.move_cursor(line, 1)
    print(f"║                  gcl.py - Git Sync Manager                     ║", end="")
    line += 1
    Terminal.move_cursor(line, 1)
    print(f"╚══════════════════════════════════════════════════════════════════════╝{Colors.RESET}", end="")
    line += 1

    # Help text
    Terminal.move_cursor(line, 3)
    print(f"{Colors.YELLOW}Navigate: ↑/↓  Switch: TAB  Toggle: SPACE  Run: ENTER  Quit: q{Colors.RESET}", end="")
    line += 1
    Terminal.move_cursor(line, 3)
    print(f"{Colors.YELLOW}Select All: a  Unselect All: u{Colors.RESET}", end="")
    line += 2

    # Strategy Selection
    Terminal.move_cursor(line, 3)
    print(f"{Colors.BOLD}{Colors.BLUE}MERGE STRATEGY (On Conflict):{Colors.RESET}", end="")
    line += 1

    Terminal.move_cursor(line, 5)
    bg = Colors.BG_BLUE if state.current_field == 0 else ""
    marker = "●" if state.strategy_selected == 0 else " "
    print(f"{bg}[{marker}] LOCAL  (Keep local changes){Colors.RESET}", end="")
    line += 1

    Terminal.move_cursor(line, 5)
    bg = Colors.BG_BLUE if state.current_field == 0 else ""
    marker = "●" if state.strategy_selected == 1 else " "
    print(f"{bg}[{marker}] REMOTE (Overwrite with remote){Colors.RESET}", end="")
    line += 2

    # Action Selection
    Terminal.move_cursor(line, 3)
    print(f"{Colors.BOLD}{Colors.BLUE}ACTION:{Colors.RESET}", end="")
    line += 1

    actions = [
        (0, "SYNC   (Remote <-> Local)"),
        (1, "PUSH   (Local -> Remote)"),
        (2, "PULL   (Remote -> Local)"),
        (3, "STATUS (Check repos)")
    ]

    for idx, label in actions:
        Terminal.move_cursor(line, 5)
        bg = Colors.BG_BLUE if state.current_field == 1 else ""
        marker = "●" if state.action_selected == idx else " "
        print(f"{bg}[{marker}] {label}{Colors.RESET}", end="")
        line += 1

    line += 1

    # Repository Selection
    Terminal.move_cursor(line, 3)
    print(f"{Colors.BOLD}{Colors.BLUE}REPOSITORIES (Toggle with SPACE):{Colors.RESET}", end="")
    line += 1

    for i, (repo_name, _) in enumerate(state.repos):
        Terminal.move_cursor(line, 5)
        bg = Colors.BG_BLUE if state.current_field == 2 and i == state.repo_cursor_index else ""
        marker = "✓" if state.repo_selection[i] else " "
        print(f"{bg}[{marker}] {repo_name}{Colors.RESET}", end="")
        line += 1

    line += 1

    # Execute Button
    Terminal.move_cursor(line, 3)
    bg = Colors.BG_GREEN if state.current_field == 3 else ""
    print(f"{bg}{Colors.BOLD}  [ RUN ]  {Colors.RESET}", end="")

    sys.stdout.flush()


def run_tui_action(state: TUIState, term: Terminal) -> bool:
    """Execute the selected action. Returns True to return to menu, False to exit"""
    term.restore_term()
    Terminal.clear_screen()

    selected_repos = state.get_selected_repos()

    if not selected_repos:
        warn("No repositories selected. Nothing to do.")
    else:
        strategy = 'local' if state.strategy_selected == 0 else 'remote'

        if state.action_selected == 0:
            run_cli_sync(strategy, selected_repos)
        elif state.action_selected == 1:
            run_cli_push(selected_repos)
        elif state.action_selected == 2:
            run_cli_pull(selected_repos)
        elif state.action_selected == 3:
            run_cli_status(selected_repos)

    print(f"\n{Colors.GREEN}{Colors.BOLD}All tasks complete!{Colors.RESET}")
    print(f"{Colors.YELLOW}Press 'm' to return to menu or any other key to exit.{Colors.RESET}")

    # Read a single character
    choice = sys.stdin.read(1)

    return choice.lower() == 'm'


def run_interactive_mode():
    """Run the interactive TUI mode"""
    state = TUIState()
    term = Terminal()

    term.save_term()
    term.set_raw_mode()
    Terminal.hide_cursor()

    return_to_menu = False

    try:
        while True:
            draw_interface(state)
            key = read_key()

            if key == 'up':
                if state.current_field == 2:  # In repo list
                    state.repo_cursor_index = (state.repo_cursor_index - 1) % state.repo_count
                else:
                    state.current_field = (state.current_field - 1) % state.total_fields

            elif key == 'down':
                if state.current_field == 2:  # In repo list
                    state.repo_cursor_index = (state.repo_cursor_index + 1) % state.repo_count
                else:
                    state.current_field = (state.current_field + 1) % state.total_fields

            elif key == 'tab':
                state.current_field = (state.current_field + 1) % state.total_fields

            elif key == 'selectall':
                state.repo_selection = [True] * state.repo_count

            elif key == 'unselectall':
                state.repo_selection = [False] * state.repo_count

            elif key == 'space':
                if state.current_field == 0:
                    state.strategy_selected = 1 - state.strategy_selected
                elif state.current_field == 1:
                    state.action_selected = (state.action_selected + 1) % 4
                elif state.current_field == 2:
                    idx = state.repo_cursor_index
                    state.repo_selection[idx] = not state.repo_selection[idx]
                elif state.current_field == 3:
                    return_to_menu = run_tui_action(state, term)
                    break

            elif key == 'enter':
                if state.current_field == 3:
                    return_to_menu = run_tui_action(state, term)
                    break

            elif key == 'quit':
                break

    finally:
        term.restore_term()

    # If user wants to return to menu, restart
    if return_to_menu:
        run_interactive_mode()


# --- Main Entry Point ---
def show_help():
    """Show help message"""
    print(f"{Colors.BOLD}{Colors.CYAN}gcl.py - Git Clone/Pull/Push Manager{Colors.RESET}\n")
    print("Manages multiple git repositories via a TUI or command-line arguments.\n")
    print(f"{Colors.BOLD}{Colors.YELLOW}USAGE:{Colors.RESET}")
    print(f"  {Colors.BOLD}gcl.py{Colors.RESET} [command] [options]\n")
    print(f"{Colors.BOLD}{Colors.YELLOW}COMMANDS:{Colors.RESET}")
    print("  (no command)\t\tLaunches the interactive TUI menu.")
    print(f"  {Colors.GREEN}sync [local|remote]{Colors.RESET}\tBidirectional sync. Default: 'remote'.")
    print(f"  {Colors.GREEN}push{Colors.RESET}\t\t\tPushes committed changes.")
    print(f"  {Colors.GREEN}pull{Colors.RESET}\t\t\tPulls using 'remote' strategy.")
    print(f"  {Colors.GREEN}status{Colors.RESET}\t\t\tChecks git status for all repos.")
    print(f"  {Colors.GREEN}help{Colors.RESET}\t\t\tShows this help message.\n")


def main():
    """Main entry point"""
    if len(sys.argv) == 1:
        # No arguments - run interactive mode
        try:
            run_interactive_mode()
        except KeyboardInterrupt:
            print("\n\nExiting...")
            sys.exit(0)
    else:
        command = sys.argv[1]

        if command == 'sync':
            strategy = sys.argv[2] if len(sys.argv) > 2 else 'remote'
            run_cli_sync(strategy)
        elif command == 'push':
            run_cli_push()
        elif command == 'pull':
            run_cli_pull()
        elif command == 'status':
            run_cli_status()
        elif command in ['help', '-h', '--help']:
            show_help()
        else:
            error(f"Invalid command: {command}")
            show_help()
            sys.exit(1)


if __name__ == '__main__':
    main()
