#!/usr/bin/env python3

"""
gcl.py - Git Clone/Pull/Push Manager (Python version)
A TUI-based git repository manager with CLI support
"""

import os
import sys
import subprocess
import curses
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import argparse
from dataclasses import dataclass
import time

# --- Configuration: Repository Lists ---
PUBLIC_REPOS = {
    "front-Github_profile": "git@github.com:diegonmarcos/diegonmarcos.git",
    "front-Github_io": "git@github.com:diegonmarcos/diegonmarcos.github.io.git",
    "back-System": "git@github.com:diegonmarcos/back-System.git",
    "back-Algo": "git@github.com:diegonmarcos/back-Algo.git",
    "back-Graphic": "git@github.com:diegonmarcos/back-Graphic.git",
    "cyber-Cyberwarfare": "git@github.com:diegonmarcos/cyber-Cyberwarfare.git",
    "ops-Tooling": "git@github.com:diegonmarcos/ops-Tooling.git",
    "ops-Mylibs": "git@github.com:diegonmarcos/ops-Mylibs.git",
    "ml-MachineLearning": "git@github.com:diegonmarcos/ml-MachineLearning.git",
    "ml-DataScience": "git@github.com:diegonmarcos/ml-DataScience.git",
    "ml-Agentic": "git@github.com:diegonmarcos/ml-Agentic.git",
}

PRIVATE_REPOS = {
    "front-Notes_md": "git@github.com:diegonmarcos/front-Notes_md.git",
    "z-lecole42": "git@github.com:diegonmarcos/lecole42.git",
    "z-dev": "git@github.com:diegonmarcos/dev.git",
}

ALL_REPOS = {**PUBLIC_REPOS, **PRIVATE_REPOS}

# --- Color Codes (for non-curses output) ---
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"

# --- Helper Functions ---
def log(msg: str):
    """Print log message"""
    print(f"{Colors.CYAN}==>{Colors.RESET} {Colors.BOLD}{msg}{Colors.RESET}")

def success(msg: str):
    """Print success message"""
    print(f"{Colors.GREEN}  ✓ {msg}{Colors.RESET}")

def error(msg: str):
    """Print error message"""
    print(f"{Colors.RED}  ✗ {msg}{Colors.RESET}")

def warn(msg: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}  ⚠ {msg}{Colors.RESET}")

# --- Git Functions ---
def run_git(repo_dir: str, *args, capture=True) -> Tuple[int, str]:
    """Run git command in repository"""
    try:
        result = subprocess.run(
            ['git', '-C', repo_dir] + list(args),
            capture_output=capture,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 1, "Git command timed out"
    except Exception as e:
        return 1, str(e)

def get_repo_status(repo_dir: str) -> str:
    """Get local repository status"""
    if not Path(repo_dir).is_dir():
        return f"{Colors.YELLOW}Not Cloned{Colors.RESET}"

    # Check for uncommitted changes
    ret, _ = run_git(repo_dir, 'diff-index', '--quiet', 'HEAD', '--')
    if ret != 0:
        return f"{Colors.YELLOW}Uncommitted{Colors.RESET}"

    # Check if branch tracks remote
    ret, _ = run_git(repo_dir, 'rev-parse', '@{u}')
    if ret != 0:
        return f"{Colors.RED}No Remote{Colors.RESET}"

    # Check for unpushed commits
    ret, output = run_git(repo_dir, 'log', '@{u}..', '--oneline')
    if ret == 0 and output.strip():
        count = len(output.strip().split('\n'))
        return f"{Colors.YELLOW}{count} Unpushed{Colors.RESET}"

    return f"{Colors.GREEN}OK{Colors.RESET}"

def get_repo_fetch_status(repo_dir: str) -> str:
    """Get remote fetch status"""
    if not Path(repo_dir).is_dir():
        return f"{Colors.YELLOW}Not Cloned{Colors.RESET}"

    # Check if branch tracks remote
    ret, _ = run_git(repo_dir, 'rev-parse', '@{u}')
    if ret != 0:
        return f"{Colors.RED}No Remote{Colors.RESET}"

    # Fetch from remote
    ret, _ = run_git(repo_dir, 'fetch', '--quiet')
    if ret != 0:
        return f"{Colors.RED}Fetch Failed{Colors.RESET}"

    # Check for unpulled commits
    ret, output = run_git(repo_dir, 'log', 'HEAD..@{u}', '--oneline')
    if ret == 0 and output.strip():
        count = len(output.strip().split('\n'))
        return f"{Colors.RED}{count} To Pull{Colors.RESET}"

    return f"{Colors.GREEN}Up to Date{Colors.RESET}"

def process_repo(repo_dir: str, repo_url: str, strategy: str, action: str):
    """Process a repository with given action"""
    log(f"Processing '{repo_dir}'")

    # Clone if doesn't exist
    if not Path(repo_dir).is_dir():
        log(f"Cloning '{repo_dir}'...")
        ret, output = run_git('.', 'clone', repo_url, repo_dir, capture=True)
        if ret == 0:
            success("Clone complete.")
        else:
            error("Clone failed.")
            print(output)
        print()
        return

    if action in ['sync', 'pull']:
        # Commit uncommitted changes before pull
        ret, _ = run_git(repo_dir, 'diff-index', '--quiet', 'HEAD', '--')
        if ret != 0:
            print("  Found uncommitted changes, committing before pull...")
            run_git(repo_dir, 'add', '.')
            ret, _ = run_git(repo_dir, 'diff-index', '--quiet', '--cached', 'HEAD', '--')
            if ret != 0:
                ret, _ = run_git(repo_dir, 'commit', '-q', '-m', 'Auto-commit before pull')
                if ret == 0:
                    success("Changes committed.")
                else:
                    error("Commit failed. Cannot pull with uncommitted changes.")
                    print()
                    return

        print(f"  Pulling with strategy: {Colors.BOLD}{strategy}{Colors.RESET}")
        ret, output = run_git(repo_dir, 'pull', '--no-rebase', f'--strategy-option={strategy}')

        if ret == 0:
            success("Pull complete.")

            if action == 'sync':
                print("  Staging all changes...")
                run_git(repo_dir, 'add', '.')
                ret, _ = run_git(repo_dir, 'diff-index', '--quiet', '--cached', 'HEAD', '--')
                if ret != 0:
                    print("  Found changes, committing with default message 'fixes'...")
                    ret, _ = run_git(repo_dir, 'commit', '-q', '-m', 'fixes')
                    if ret == 0:
                        success("Commit complete.")
                    else:
                        error("Commit failed unexpectedly.")

                print("  Pushing changes...")
                ret, output = run_git(repo_dir, 'push')
                if ret == 0:
                    success("Push complete.")
                else:
                    error("Push failed.")
        else:
            error("Pull failed.")
            # Check for specific errors
            if "File name too long" in output or "Filename too long" in output:
                warn("Filesystem limitation: Path/filename exceeds system limits.")
                warn("Attempting automatic fix...")
                ret, _ = run_git(repo_dir, 'config', 'core.longpaths', 'true')
                if ret == 0:
                    success("Enabled core.longpaths for this repo.")
                    warn("Please re-run sync/pull for this repo.")
            elif "symlink" in output:
                warn("Symlink creation failed. Attempting fix...")
                ret, _ = run_git(repo_dir, 'config', 'core.symlinks', 'false')
                if ret == 0:
                    success("Disabled symlinks for this repo.")
                    warn("Please re-run sync/pull for this repo.")

            # Abort failed merge
            ret, _ = run_git(repo_dir, 'rev-parse', 'MERGE_HEAD')
            if ret == 0:
                warn("Aborting failed merge...")
                run_git(repo_dir, 'merge', '--abort')

            print(f"  {Colors.YELLOW}Error details:{Colors.RESET}")
            for line in output.split('\n'):
                print(f"    {line}")

    elif action == 'push':
        print("  Staging all changes...")
        run_git(repo_dir, 'add', '.')
        ret, _ = run_git(repo_dir, 'diff-index', '--quiet', '--cached', 'HEAD', '--')
        if ret != 0:
            print("  Found changes, committing with default message 'fixes'...")
            ret, _ = run_git(repo_dir, 'commit', '-q', '-m', 'fixes')
            if ret == 0:
                success("Commit complete.")
            else:
                error("Commit failed unexpectedly.")

        print("  Pushing changes...")
        ret, output = run_git(repo_dir, 'push')
        if ret == 0:
            success("Push complete.")
        else:
            error("Push failed.")

    print()

# --- CLI Actions ---
def run_cli_sync(strategy: str = 'theirs', repos: Optional[List[str]] = None):
    """Run bidirectional sync"""
    git_strategy = 'ours' if strategy == 'local' else 'theirs'
    log(f"Starting Bidirectional Sync (Strategy: {git_strategy})")

    repos_to_process = repos if repos else list(ALL_REPOS.keys())
    for repo_dir in repos_to_process:
        repo_url = ALL_REPOS.get(repo_dir, '')
        if repo_url:
            process_repo(repo_dir, repo_url, git_strategy, 'sync')

def run_cli_push(repos: Optional[List[str]] = None):
    """Run push"""
    log("Starting Push")
    repos_to_process = repos if repos else list(ALL_REPOS.keys())
    for repo_dir in repos_to_process:
        repo_url = ALL_REPOS.get(repo_dir, '')
        if repo_url:
            process_repo(repo_dir, repo_url, 'none', 'push')

def run_cli_pull(repos: Optional[List[str]] = None):
    """Run pull"""
    log("Starting Forced Pull (Remote Overwrites Local on Conflict)")
    repos_to_process = repos if repos else list(ALL_REPOS.keys())
    for repo_dir in repos_to_process:
        repo_url = ALL_REPOS.get(repo_dir, '')
        if repo_url:
            process_repo(repo_dir, repo_url, 'theirs', 'pull')

def run_cli_status(repos: Optional[List[str]] = None):
    """Check repository status"""
    log("Checking Git Status for Repositories")
    repos_to_process = repos if repos else list(ALL_REPOS.keys())

    for repo_dir in repos_to_process:
        if not Path(repo_dir).is_dir():
            warn(f"'{repo_dir}' not cloned yet.")
            print()
            continue

        log(f"Checking '{repo_dir}'")

        # Check for uncommitted changes
        ret, _ = run_git(repo_dir, 'diff-index', '--quiet', 'HEAD', '--')
        if ret != 0:
            warn("Has uncommitted changes (staged or unstaged)")
            print(f"  {Colors.YELLOW}Files changed:{Colors.RESET}")
            _, output = run_git(repo_dir, 'status', '--short')
            for line in output.split('\n'):
                if line.strip():
                    print(f"    {line}")
        else:
            success("Working tree clean")

        # Check for unpushed commits
        ret, output = run_git(repo_dir, 'log', '@{u}..', '--oneline')
        if ret == 0 and output.strip():
            count = len(output.strip().split('\n'))
            warn(f"Has {count} unpushed commit(s)")
            print(f"  {Colors.YELLOW}Unpushed commits:{Colors.RESET}")
            for line in output.split('\n'):
                if line.strip():
                    print(f"    {line}")
        else:
            ret, _ = run_git(repo_dir, 'rev-parse', '@{u}')
            if ret == 0:
                success("All commits pushed")
            else:
                warn("Branch does not track a remote")

        print()

def run_cli_untracked(repos: Optional[List[str]] = None):
    """List untracked files"""
    log("Listing ALL Untracked Files (including ignored files)")
    repos_to_process = repos if repos else list(ALL_REPOS.keys())

    for repo_dir in repos_to_process:
        if not Path(repo_dir).is_dir():
            warn(f"'{repo_dir}' not cloned yet.")
            print()
            continue

        log(f"Checking '{repo_dir}'")

        # Get ALL untracked files
        ret, output = run_git(repo_dir, 'ls-files', '--others')

        if ret == 0 and output.strip():
            count = len(output.strip().split('\n'))
            warn(f"Has {count} untracked file(s)")
            print(f"  {Colors.YELLOW}Untracked files:{Colors.RESET}")
            for line in output.split('\n')[:50]:  # Limit to first 50
                if line.strip():
                    print(f"    {line}")
            if count > 50:
                print(f"    ... and {count - 50} more files")
        else:
            success("No untracked files")

        print()

def restore_symlinks(repo_path: str):
    """Run the restore-spec-symlinks script"""
    script_dir = Path(__file__).parent
    script_path = script_dir / "restore-spec-symlinks.sh"

    if not script_path.exists():
        error(f"Script not found: {script_path}")
        return

    log("Restoring 0.spec symlinks...")
    ret = subprocess.call(['bash', str(script_path), repo_path])
    if ret == 0:
        success("Symlink restoration complete!")
    else:
        error("Symlink restoration failed!")

# --- TUI Implementation ---
@dataclass
class TUIState:
    """State for TUI interface"""
    workdir_selected: int = 1  # 0=current dir, 1=custom path
    workdir_path: str = "/home/diego/Documents/Git"
    repo_status_list: List[str] = None
    repo_fetch_status_list: List[str] = None

    def __post_init__(self):
        if self.repo_status_list is None:
            self.repo_status_list = []
        if self.repo_fetch_status_list is None:
            self.repo_fetch_status_list = []

class TUI:
    """Terminal User Interface for git manager"""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.state = TUIState()
        self.repo_names = list(ALL_REPOS.keys())
        self.repo_count = len(self.repo_names)

        # Check minimum terminal size
        max_y, max_x = stdscr.getmaxyx()
        min_height = 25
        min_width = 75

        if max_y < min_height or max_x < min_width:
            stdscr.clear()
            stdscr.addstr(0, 0, f"Terminal too small! Minimum size: {min_width}x{min_height}")
            stdscr.addstr(1, 0, f"Current size: {max_x}x{max_y}")
            stdscr.addstr(2, 0, "Please resize your terminal and try again.")
            stdscr.addstr(4, 0, "Press any key to exit...")
            stdscr.refresh()
            stdscr.getch()
            raise Exception("Terminal too small")

        # Initialize curses colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_BLUE, -1)
        curses.init_pair(5, curses.COLOR_CYAN, -1)
        curses.init_pair(6, curses.COLOR_MAGENTA, -1)

        # Color constants
        self.C_RED = curses.color_pair(1)
        self.C_GREEN = curses.color_pair(2)
        self.C_YELLOW = curses.color_pair(3)
        self.C_BLUE = curses.color_pair(4)
        self.C_CYAN = curses.color_pair(5)
        self.C_MAGENTA = curses.color_pair(6)
        self.C_BOLD = curses.A_BOLD

        # Initialize status lists with placeholders
        self.state.repo_status_list = ["Not Checked"] * self.repo_count
        self.state.repo_fetch_status_list = ["Not Checked"] * self.repo_count

        # Hide cursor
        curses.curs_set(0)

        # Initial status refresh (local only for speed)
        self.refresh_status_only()

    def get_working_dir(self) -> str:
        """Get current working directory based on selection"""
        if self.state.workdir_selected == 0:
            return os.getcwd()
        return self.state.workdir_path

    def refresh_status_only(self):
        """Refresh local status only (fast)"""
        work_dir = self.get_working_dir()
        os.chdir(work_dir)

        for i, repo_name in enumerate(self.repo_names):
            repo_dir = os.path.join(work_dir, repo_name)
            self.state.repo_status_list[i] = get_repo_status(repo_dir)

    def refresh_fetch_only(self):
        """Refresh remote fetch status only"""
        work_dir = self.get_working_dir()
        os.chdir(work_dir)

        for i, repo_name in enumerate(self.repo_names):
            repo_dir = os.path.join(work_dir, repo_name)
            self.state.repo_fetch_status_list[i] = get_repo_fetch_status(repo_dir)

    def refresh_both(self):
        """Refresh both local and remote status"""
        self.refresh_status_only()
        self.refresh_fetch_only()

    def draw_header(self):
        """Draw the header"""
        self.stdscr.clear()
        max_y, max_x = self.stdscr.getmaxyx()

        try:
            # Title box
            title = " gcl.py - Git Sync Manager "
            self.stdscr.addstr(1, 2, "╔" + "═" * (len(title)) + "╗", self.C_CYAN | self.C_BOLD)
            self.stdscr.addstr(2, 2, "║", self.C_CYAN | self.C_BOLD)
            self.stdscr.addstr(2, 3, title, self.C_CYAN | self.C_BOLD)
            self.stdscr.addstr(2, 3 + len(title), "║", self.C_CYAN | self.C_BOLD)
            self.stdscr.addstr(3, 2, "╚" + "═" * (len(title)) + "╝", self.C_CYAN | self.C_BOLD)

            # Working directory selection
            line = 5
            self.stdscr.addstr(line, 2, "Working Directory:", self.C_BOLD)
            line += 1

            # Option 1: Current directory
            marker1 = "[✓]" if self.state.workdir_selected == 0 else "[ ]"
            self.stdscr.addstr(line, 4, marker1, self.C_YELLOW)
            self.stdscr.addstr(line, 8, "Current: ", self.C_BOLD)
            cwd = os.getcwd()
            self.stdscr.addstr(line, 17, cwd[:max_x - 20] if len(cwd) > max_x - 20 else cwd)
            line += 1

            # Option 2: Custom path
            marker2 = "[✓]" if self.state.workdir_selected == 1 else "[ ]"
            self.stdscr.addstr(line, 4, marker2, self.C_YELLOW)
            self.stdscr.addstr(line, 8, "Custom:  ", self.C_BOLD)
            custom_path = self.state.workdir_path
            self.stdscr.addstr(line, 17, custom_path[:max_x - 20] if len(custom_path) > max_x - 20 else custom_path)

            return line + 2
        except curses.error:
            return 9  # Default line position if header fails

    def draw_repo_list(self, start_line: int):
        """Draw the repository list with three columns"""
        max_y, max_x = self.stdscr.getmaxyx()
        line = start_line

        # Check if we have room for headers
        if line >= max_y - 3:
            return line

        try:
            # Column headers
            self.stdscr.addstr(line, 2, "Repository", self.C_CYAN | self.C_BOLD)
            self.stdscr.addstr(line, 35, "Local Status", self.C_CYAN | self.C_BOLD)
            self.stdscr.addstr(line, 60, "Remote Status", self.C_CYAN | self.C_BOLD)
            line += 1

            # Separator
            self.stdscr.addstr(line, 2, "─" * 75, self.C_CYAN)
            line += 1
        except curses.error:
            return line

        # Repository rows
        repos_drawn = 0
        for i, repo_name in enumerate(self.repo_names):
            # Stop if we're running out of space (leave room for actions menu)
            if line + i >= max_y - 15:
                # Show indicator that there are more repos
                if i < len(self.repo_names):
                    remaining = len(self.repo_names) - i
                    try:
                        self.stdscr.addstr(line + i, 2, f"... and {remaining} more repos (resize terminal to see all)", self.C_YELLOW)
                    except curses.error:
                        pass
                break

            try:
                # Repository name
                self.stdscr.addstr(line + i, 2, repo_name[:30])

                # Local status (parse color from ANSI codes)
                local_status = self.state.repo_status_list[i]
                self.draw_colored_status(line + i, 35, local_status)

                # Remote status
                remote_status = self.state.repo_fetch_status_list[i]
                self.draw_colored_status(line + i, 60, remote_status)

                repos_drawn += 1
            except curses.error:
                break

        return line + repos_drawn + 1

    def draw_colored_status(self, y: int, x: int, status_text: str):
        """Draw status text with appropriate color"""
        max_y, max_x = self.stdscr.getmaxyx()

        # Don't draw if outside screen bounds
        if y >= max_y - 1 or x >= max_x - 1:
            return

        # Remove ANSI color codes and determine color
        clean_text = status_text
        color = curses.A_NORMAL

        if "Not Cloned" in status_text or "Not Checked" in status_text:
            color = self.C_YELLOW
            clean_text = status_text.replace(Colors.YELLOW, "").replace(Colors.RESET, "")
        elif "OK" in status_text or "Up to Date" in status_text or "Clean" in status_text:
            color = self.C_GREEN
            clean_text = status_text.replace(Colors.GREEN, "").replace(Colors.RESET, "")
        elif "To Pull" in status_text or "Unpushed" in status_text or "Uncommitted" in status_text:
            color = self.C_RED if "To Pull" in status_text else self.C_YELLOW
            clean_text = status_text.replace(Colors.RED, "").replace(Colors.YELLOW, "").replace(Colors.RESET, "")
        elif "No Remote" in status_text or "Fetch Failed" in status_text:
            color = self.C_RED
            clean_text = status_text.replace(Colors.RED, "").replace(Colors.RESET, "")

        try:
            self.stdscr.addstr(y, x, clean_text[:20], color)
        except curses.error:
            # Silently ignore if we can't write (edge of screen)
            pass

    def draw_actions(self, start_line: int):
        """Draw action menu"""
        max_y, max_x = self.stdscr.getmaxyx()
        line = start_line

        # Check if we have room for the actions header
        if line >= max_y - 1:
            return line

        try:
            self.stdscr.addstr(line, 2, "Actions:", self.C_CYAN | self.C_BOLD)
        except curses.error:
            return line
        line += 1

        actions = [
            ("s", "Sync (bidirectional)"),
            ("p", "Push"),
            ("l", "Pull"),
            ("u", "Untracked files"),
            ("y", "Restore symlinks"),
            ("", ""),
            ("t", "Refresh status only"),
            ("f", "Refresh fetch only"),
            ("r", "Refresh both"),
            ("", ""),
            ("w", "Toggle working dir"),
            ("q", "Quit"),
        ]

        for key, desc in actions:
            # Stop if we're at the bottom of the screen
            if line >= max_y - 1:
                break

            if key:
                try:
                    self.stdscr.addstr(line, 4, f"[{key}]", self.C_YELLOW | self.C_BOLD)
                    self.stdscr.addstr(line, 8, desc)
                except curses.error:
                    break
            line += 1

        return line

    def draw_screen(self):
        """Draw the entire screen"""
        line = self.draw_header()
        line = self.draw_repo_list(line)
        self.draw_actions(line)
        self.stdscr.refresh()

    def show_message(self, message: str):
        """Show a message and wait for key press"""
        self.stdscr.clear()
        self.stdscr.addstr(1, 2, message, self.C_CYAN | self.C_BOLD)
        self.stdscr.addstr(3, 2, "Press 'q' to quit or any other key to return to menu...", self.C_YELLOW)
        self.stdscr.refresh()

        while True:
            key = self.stdscr.getch()
            if key == ord('q'):
                return False
            else:
                return True

    def execute_action(self, action: str, strategy: str = 'remote'):
        """Execute action and show results"""
        # Clear screen and show we're working
        self.stdscr.clear()
        self.stdscr.addstr(1, 2, f"Executing {action}...", self.C_CYAN | self.C_BOLD)
        self.stdscr.addstr(2, 2, "Please wait...", self.C_YELLOW)
        self.stdscr.refresh()

        # Restore terminal for command output
        curses.endwin()

        # Execute the action
        work_dir = self.get_working_dir()
        os.chdir(work_dir)

        if action == 'sync':
            run_cli_sync(strategy)
        elif action == 'push':
            run_cli_push()
        elif action == 'pull':
            run_cli_pull()
        elif action == 'status':
            run_cli_status()
        elif action == 'untracked':
            run_cli_untracked()
        elif action == 'symlinks':
            restore_symlinks(work_dir)

        # Wait for user
        print(f"\n{Colors.YELLOW}Press 'q' to quit or any other key to return to menu...{Colors.RESET}")

        # Get single character input
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        # Reinitialize curses
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        curses.curs_set(0)

        # Reinitialize colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_BLUE, -1)
        curses.init_pair(5, curses.COLOR_CYAN, -1)
        curses.init_pair(6, curses.COLOR_MAGENTA, -1)

        if ch == 'q':
            return False

        # Refresh status after action
        self.refresh_both()
        return True

    def run(self):
        """Main TUI loop"""
        self.draw_screen()

        while True:
            key = self.stdscr.getch()

            if key == ord('q'):
                break
            elif key == ord('w'):
                # Toggle working directory
                self.state.workdir_selected = 1 - self.state.workdir_selected
                self.refresh_both()
                self.draw_screen()
            elif key == ord('t'):
                # Refresh status only
                self.stdscr.addstr(0, 0, "Refreshing status...", self.C_YELLOW)
                self.stdscr.refresh()
                self.refresh_status_only()
                self.draw_screen()
            elif key == ord('f'):
                # Refresh fetch only
                self.stdscr.addstr(0, 0, "Fetching from remote...", self.C_YELLOW)
                self.stdscr.refresh()
                self.refresh_fetch_only()
                self.draw_screen()
            elif key == ord('r'):
                # Refresh both
                self.stdscr.addstr(0, 0, "Refreshing all...", self.C_YELLOW)
                self.stdscr.refresh()
                self.refresh_both()
                self.draw_screen()
            elif key == ord('s'):
                # Sync - ask for strategy
                if not self.execute_action('sync', 'remote'):
                    break
                self.draw_screen()
            elif key == ord('p'):
                # Push
                if not self.execute_action('push'):
                    break
                self.draw_screen()
            elif key == ord('l'):
                # Pull
                if not self.execute_action('pull'):
                    break
                self.draw_screen()
            elif key == ord('u'):
                # Untracked
                if not self.execute_action('untracked'):
                    break
                self.draw_screen()
            elif key == ord('y'):
                # Symlinks
                if not self.execute_action('symlinks'):
                    break
                self.draw_screen()

def run_tui():
    """Launch the TUI"""
    try:
        curses.wrapper(lambda stdscr: TUI(stdscr).run())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        if "Terminal too small" in str(e):
            sys.exit(1)
        else:
            print(f"\n{Colors.RED}TUI Error: {e}{Colors.RESET}")
            print(f"\n{Colors.YELLOW}You can still use CLI commands:{Colors.RESET}")
            print("  python3 gcl.py status")
            print("  python3 gcl.py sync")
            print("  python3 gcl.py --help")
            sys.exit(1)

# --- Main CLI ---
def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Git Clone/Pull/Push Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  (no command)        Launch the interactive TUI menu
  sync [local|remote] Bidirectional sync (default: remote)
  push                Push committed changes
  pull                Pull using 'remote' strategy
  status              Check git status for all repos
  untracked           List ALL untracked files (including ignored)
  symlinks [path]     Restore 0.spec symlinks
        """
    )

    parser.add_argument('command', nargs='?', default='',
                      help='Command to execute')
    parser.add_argument('args', nargs='*',
                      help='Additional arguments')

    args = parser.parse_args()

    # Change to working directory if needed
    os.chdir('/home/diego/Documents/Git')

    if not args.command:
        # Launch TUI
        run_tui()
        sys.exit(0)

    cmd = args.command.lower()

    if cmd == 'sync':
        strategy = args.args[0] if args.args else 'remote'
        run_cli_sync(strategy)
    elif cmd == 'push':
        run_cli_push()
    elif cmd == 'pull':
        run_cli_pull()
    elif cmd == 'status':
        run_cli_status()
    elif cmd == 'untracked':
        run_cli_untracked()
    elif cmd == 'symlinks':
        repo_path = args.args[0] if args.args else '/home/diego/Documents/Git/front-Notes_md'
        restore_symlinks(repo_path)
    elif cmd in ['help', '-h', '--help']:
        parser.print_help()
    else:
        error(f"Invalid command: {cmd}")
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
