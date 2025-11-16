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
    workdir_selected: int = 1
    workdir_path: str = str(Path.home() / "Documents/Git")
    strategy_selected: int = 1  # 0=local, 1=remote
    action_selected: int = 0    # 0=sync, 1=push, 2=pull, 3=status, 4=untracked
    repo_cursor_index: int = 0
    repo_selections: List[bool] = None
    current_field: int = 3      # Start in the repo list
    
    repo_status_list: List[str] = None
    repo_fetch_status_list: List[str] = None

    def __post_init__(self):
        if self.repo_selections is None:
            self.repo_selections = []
        if self.repo_status_list is None:
            self.repo_status_list = []
        if self.repo_fetch_status_list is None:
            self.repo_fetch_status_list = []

class TUI:
    """Terminal User Interface for git manager"""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.state = TUIState()
        self.repo_names = sorted(list(ALL_REPOS.keys()))
        self.repo_count = len(self.repo_names)
        
        self.FIELD_WORKDIR = 0
        self.FIELD_STRATEGY = 1
        self.FIELD_ACTION = 2
        self.FIELD_REPOS = 3
        self.FIELD_RUN = 4
        self.TOTAL_FIELDS = 5

        self.STRATEGIES = ["L(o)cal  (Keep local changes)", "R(e)mote (Overwrite with remote)"]
        self.ACTIONS = ["(S)ync   (Remote <-> Local)", "(P)ush   (Local -> Remote)", "Pu(l)l   (Remote -> Local)", "Sta(t)us (Check repos)", "U(n)tracked (List all untracked)"]

        max_y, max_x = stdscr.getmaxyx()
        if max_y < 30 or max_x < 80:
            raise Exception(f"Terminal too small! Minimum: 80x30, Current: {max_x}x{max_y}")

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_BLUE, -1)
        curses.init_pair(5, curses.COLOR_CYAN, -1)
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_GREEN)

        self.C_RED = curses.color_pair(1)
        self.C_GREEN = curses.color_pair(2)
        self.C_YELLOW = curses.color_pair(3)
        self.C_BLUE = curses.color_pair(4)
        self.C_CYAN = curses.color_pair(5)
        self.C_BOLD = curses.A_BOLD
        self.C_HIGHLIGHT = curses.color_pair(7)
        self.C_RUN_HL = curses.color_pair(8)

        self.state.repo_selections = [True] * self.repo_count
        self.state.repo_status_list = ["Not Checked"] * self.repo_count
        self.state.repo_fetch_status_list = ["Not Checked"] * self.repo_count

        curses.curs_set(0)
        self.stdscr.keypad(True)
        self.refresh_status_only()

    def get_working_dir(self) -> str:
        if self.state.workdir_selected == 0:
            return os.getcwd()
        return self.state.workdir_path

    def refresh_status_only(self):
        work_dir = self.get_working_dir()
        if not Path(work_dir).is_dir(): return
        
        original_dir = os.getcwd()
        os.chdir(work_dir)
        for i, repo_name in enumerate(self.repo_names):
            self.state.repo_status_list[i] = get_repo_status(repo_name)
        os.chdir(original_dir)

    def refresh_fetch_only(self):
        work_dir = self.get_working_dir()
        if not Path(work_dir).is_dir(): return

        original_dir = os.getcwd()
        os.chdir(work_dir)
        for i, repo_name in enumerate(self.repo_names):
            self.state.repo_fetch_status_list[i] = get_repo_fetch_status(repo_name)
        os.chdir(original_dir)

    def refresh_both(self):
        self.refresh_status_only()
        self.refresh_fetch_only()

    def _draw_dynamic_title_box(self, text: str):
        padded_text = f" {text} "
        width = len(padded_text)
        try:
            self.stdscr.addstr(0, 0, "╔" + "═" * width + "╗", self.C_CYAN | self.C_BOLD)
            self.stdscr.addstr(1, 0, f"║{padded_text}║", self.C_CYAN | self.C_BOLD)
            self.stdscr.addstr(2, 0, "╚" + "═" * width + "╝", self.C_CYAN | self.C_BOLD)
        except curses.error: pass

    def _draw_selection_list(self, y, title, options, selected_index, is_active_field):
        self.stdscr.addstr(y, 2, title, self.C_BLUE | self.C_BOLD)
        self.stdscr.addstr(y + 1, 2, "─" * (len(title)), self.C_BLUE)
        y += 2
        for i, option_text in enumerate(options):
            attr = self.C_HIGHLIGHT if is_active_field and i == selected_index else curses.A_NORMAL
            
            final_attr = attr
            if i == selected_index:
                final_attr = final_attr | self.C_BOLD
            
            marker = "●" if i == selected_index else " "
            self.stdscr.addstr(y + i, 4, f"[{marker}] {option_text}", final_attr)
        return y + len(options)

    def draw_colored_status(self, y: int, x: int, status_text: str, base_attr=curses.A_NORMAL):
        max_y, max_x = self.stdscr.getmaxyx()
        if y >= max_y or x >= max_x: return

        clean_text = status_text.replace(Colors.RESET, "")
        color = curses.A_NORMAL
        if Colors.YELLOW in status_text: color = self.C_YELLOW
        if Colors.GREEN in status_text: color = self.C_GREEN
        if Colors.RED in status_text: color = self.C_RED
        
        clean_text = clean_text.replace(Colors.YELLOW, "").replace(Colors.GREEN, "").replace(Colors.RED, "")
        
        try:
            self.stdscr.addstr(y, x, clean_text.ljust(20), color | base_attr)
        except curses.error:
            pass

    def draw_screen(self):
        self.stdscr.clear()
        max_y, max_x = self.stdscr.getmaxyx()
        
        self._draw_dynamic_title_box("gcl.py - Git Sync Manager")
        
        line = 4
        workdir_opts = [f"Current Directory (.)", f"Custom Path: {self.state.workdir_path}"]
        line = self._draw_selection_list(line, "WORKING DIRECTORY:", workdir_opts, self.state.workdir_selected, self.state.current_field == self.FIELD_WORKDIR)
        
        line = self._draw_selection_list(line, "MERGE STRATEGY (On Conflict):", self.STRATEGIES, self.state.strategy_selected, self.state.current_field == self.FIELD_STRATEGY)

        line = self._draw_selection_list(line, "ACTION:", self.ACTIONS, self.state.action_selected, self.state.current_field == self.FIELD_ACTION)

        repo_title = "REPOSITORIES (Toggle with SPACE):"
        self.stdscr.addstr(line, 2, repo_title, self.C_BLUE | self.C_BOLD)
        self.stdscr.addstr(line + 1, 2, "─" * len(repo_title), self.C_BLUE)
        
        local_title = "LOCAL STATUS:"
        self.stdscr.addstr(line, 40, local_title, self.C_BLUE | self.C_BOLD)
        self.stdscr.addstr(line + 1, 40, "─" * len(local_title), self.C_BLUE)

        remote_title = "REMOTE STATUS:"
        self.stdscr.addstr(line, 60, remote_title, self.C_BLUE | self.C_BOLD)
        self.stdscr.addstr(line + 1, 60, "─" * len(remote_title), self.C_BLUE)
        line += 2
        
        for i in range(self.repo_count):
            if line >= max_y - 8: break
            
            is_active = self.state.current_field == self.FIELD_REPOS and i == self.state.repo_cursor_index
            attr = self.C_HIGHLIGHT if is_active else curses.A_NORMAL
            marker = "✓" if self.state.repo_selections[i] else " "
            repo_text = f"[{marker}] {self.repo_names[i]}"

            self.stdscr.addstr(line, 0, " " * (max_x), attr)
            self.stdscr.addstr(line, 2, repo_text, attr)
            self.draw_colored_status(line, 40, self.state.repo_status_list[i], base_attr=attr)
            self.draw_colored_status(line, 60, self.state.repo_fetch_status_list[i], base_attr=attr)
            line += 1
        
        run_line = line + 1
        run_attr = self.C_RUN_HL if self.state.current_field == self.FIELD_RUN else self.C_BOLD
        self.stdscr.addstr(run_line, 4, "[ RUN ]", run_attr)

        help_line = run_line + 3
        if help_line < max_y - 7:
            self.stdscr.addstr(help_line, 2, "KEYBOARD SHORTCUTS", self.C_BLUE | self.C_BOLD)
            help_line += 1
            self.stdscr.addstr(help_line, 2, "─" * (max_x - 4), self.C_BLUE)
            help_line += 1

            # Navigate
            self.stdscr.addstr(help_line, 2, "Navigate:", self.C_BOLD)
            self.stdscr.addstr(help_line, 12, " (")
            self.stdscr.addstr("↑/↓", self.C_YELLOW | self.C_BOLD)
            self.stdscr.addstr(") List | (")
            self.stdscr.addstr("TAB", self.C_YELLOW | self.C_BOLD)
            self.stdscr.addstr(") Field | (")
            self.stdscr.addstr("SPACE", self.C_YELLOW | self.C_BOLD)
            self.stdscr.addstr(") Toggle | (")
            self.stdscr.addstr("ENTER", self.C_YELLOW | self.C_BOLD)
            self.stdscr.addstr(") Run | (")
            self.stdscr.addstr("q", self.C_YELLOW | self.C_BOLD)
            self.stdscr.addstr(") Quit")
            help_line += 1

            # Select
            self.stdscr.addstr(help_line, 2, "Select:  ", self.C_BOLD)
            self.stdscr.addstr(help_line, 12, " (")
            self.stdscr.addstr("a", self.C_YELLOW | self.C_BOLD)
            self.stdscr.addstr(") All | (")
            self.stdscr.addstr("u", self.C_YELLOW | self.C_BOLD)
            self.stdscr.addstr(") None | (")
            self.stdscr.addstr("k", self.C_YELLOW | self.C_BOLD)
            self.stdscr.addstr(") Not OK")
            help_line += 1

            # Strategy
            self.stdscr.addstr(help_line, 2, "Strategy:", self.C_BOLD)
            self.stdscr.addstr(help_line, 12, " (")
            self.stdscr.addstr("o", self.C_YELLOW | self.C_BOLD)
            self.stdscr.addstr(") Local | (")
            self.stdscr.addstr("e", self.C_YELLOW | self.C_BOLD)
            self.stdscr.addstr(") Remote")
            help_line += 1

            # Actions
            self.stdscr.addstr(help_line, 2, "Actions: ", self.C_BOLD)
            self.stdscr.addstr(help_line, 12, " (")
            self.stdscr.addstr("s", self.C_YELLOW | self.C_BOLD)
            self.stdscr.addstr(") Sync | (")
            self.stdscr.addstr("p", self.C_YELLOW | self.C_BOLD)
            self.stdscr.addstr(") Push | (")
            self.stdscr.addstr("l", self.C_YELLOW | self.C_BOLD)
            self.stdscr.addstr(") Pull")
            help_line += 1
            self.stdscr.addstr(help_line, 12, " (")
            self.stdscr.addstr("n", self.C_YELLOW | self.C_BOLD)
            self.stdscr.addstr(") Untracked | (")
            self.stdscr.addstr("t", self.C_YELLOW | self.C_BOLD)
            self.stdscr.addstr(") Status | (")
            self.stdscr.addstr("f", self.C_YELLOW | self.C_BOLD)
            self.stdscr.addstr(") Fetch | (")
            self.stdscr.addstr("r", self.C_YELLOW | self.C_BOLD)
            self.stdscr.addstr(") Refresh")
            help_line += 1
            
            # Tools
            self.stdscr.addstr(help_line, 2, "Tools:   ", self.C_BOLD)
            self.stdscr.addstr(help_line, 12, " (")
            self.stdscr.addstr("w", self.C_YELLOW | self.C_BOLD)
            self.stdscr.addstr(") Toggle Workdir")
        
        self.stdscr.refresh()

    def execute_action(self) -> bool:
        action_map = ['sync', 'push', 'pull', 'status', 'untracked']
        strategy_map = ['local', 'theirs']

        action = action_map[self.state.action_selected]
        strategy = strategy_map[self.state.strategy_selected]
        
        selected_repos = [self.repo_names[i] for i, s in enumerate(self.state.repo_selections) if s]
        
        if not selected_repos:
            self.show_message("No repositories selected. Nothing to do.")
            return True

        self.stdscr.clear()
        self.stdscr.addstr(1, 2, f"Executing {action}...", self.C_CYAN | self.C_BOLD)
        self.stdscr.refresh()
        curses.endwin()

        work_dir = self.get_working_dir()
        original_dir = os.getcwd()
        os.chdir(work_dir)

        print("\n" + "="*60)
        
        if action == 'sync': run_cli_sync(strategy, repos=selected_repos)
        elif action == 'push': run_cli_push(repos=selected_repos)
        elif action == 'pull': run_cli_pull(repos=selected_repos)
        elif action == 'status': run_cli_status(repos=selected_repos)
        elif action == 'untracked': run_cli_untracked(repos=selected_repos)

        print("="*60)
        print(f"\n{Colors.YELLOW}Press 'q' to quit or any other key to return to menu...{Colors.RESET}")
        
        import tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        
        os.chdir(original_dir)
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        
        if ch.lower() == 'q':
            return False
        
        self.refresh_both()
        return True

    def show_message(self, message: str):
        self.stdscr.clear()
        self.stdscr.addstr(1, 2, message, self.C_CYAN | self.C_BOLD)
        self.stdscr.addstr(3, 2, "Press any key to return...", self.C_YELLOW)
        self.stdscr.refresh()
        self.stdscr.getch()

    def run(self):
        while True:
            self.draw_screen()
            key = self.stdscr.getch()

            if key == ord('q'): break
            
            if key == ord('\t') or key == curses.KEY_RIGHT:
                self.state.current_field = (self.state.current_field + 1) % self.TOTAL_FIELDS
            elif key == curses.KEY_BTAB or key == curses.KEY_LEFT:
                self.state.current_field = (self.state.current_field - 1 + self.TOTAL_FIELDS) % self.TOTAL_FIELDS
            elif key == ord('\n') or key == curses.KEY_ENTER:
                if not self.execute_action(): break
                continue
            
            field = self.state.current_field
            if field == self.FIELD_WORKDIR:
                if key in [curses.KEY_UP, curses.KEY_DOWN, ord(' ')]:
                    self.state.workdir_selected = 1 - self.state.workdir_selected
            elif field == self.FIELD_STRATEGY:
                if key in [curses.KEY_UP, curses.KEY_DOWN, ord(' ')]:
                    self.state.strategy_selected = 1 - self.state.strategy_selected
            elif field == self.FIELD_ACTION:
                if key == curses.KEY_UP:
                    self.state.action_selected = (self.state.action_selected - 1 + len(self.ACTIONS)) % len(self.ACTIONS)
                elif key in [curses.KEY_DOWN, ord(' ')]:
                    self.state.action_selected = (self.state.action_selected + 1) % len(self.ACTIONS)
            elif field == self.FIELD_REPOS:
                if key == curses.KEY_UP:
                    self.state.repo_cursor_index = (self.state.repo_cursor_index - 1 + self.repo_count) % self.repo_count
                elif key == curses.KEY_DOWN:
                    self.state.repo_cursor_index = (self.state.repo_cursor_index + 1) % self.repo_count
                elif key == ord(' '):
                    idx = self.state.repo_cursor_index
                    self.state.repo_selections[idx] = not self.state.repo_selections[idx]
                elif key == ord('a'):
                    self.state.repo_selections = [True] * self.repo_count
                elif key == ord('u'):
                    self.state.repo_selections = [False] * self.repo_count
                elif key == ord('k'):
                    self.state.repo_selections = ["OK" not in s for s in self.state.repo_status_list]
            
            # Global shortcuts
            if key == ord('o'): self.state.strategy_selected = 0
            elif key == ord('e'): self.state.strategy_selected = 1
            elif key == ord('s'): self.state.action_selected = 0
            elif key == ord('p'): self.state.action_selected = 1
            elif key == ord('l'): self.state.action_selected = 2
            elif key == ord('t'): self.state.action_selected = 3
            elif key == ord('n'): self.state.action_selected = 4
            elif key == ord('r'): self.refresh_both()

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
