#!/usr/bin/env python3

"""
gcl.py - Git Clone/Pull/Push Manager (Python version)
A TUI-based git repository manager with CLI support
Matches the gcl.sh TUI layout and functionality
"""

import os
import sys
import subprocess
import curses
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import argparse
from dataclasses import dataclass
import threading
import queue
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
    print(f"{Colors.CYAN}===>{Colors.RESET} {Colors.BOLD}{msg}{Colors.RESET}")

def success(msg: str):
    """Print success message"""
    print(f"{Colors.GREEN}  ✓ {msg}{Colors.RESET}")

def error(msg: str):
    """Print error message"""
    print(f"{Colors.RED}  ✗ {msg}{Colors.RESET}")

def warn(msg: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}  ⚠ {msg}{Colors.RESET}")

# --- Git Helper Functions ---
def run_git(repo_dir: str, *args, timeout=60) -> Tuple[int, str]:
    """Run git command and return (returncode, output)"""
    try:
        result = subprocess.run(
            ['git', '-C', repo_dir] + list(args),
            capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 1, "Git command timed out"
    except Exception as e:
        return 1, str(e)

def get_repo_local_status(repo_dir: str) -> str:
    """Get local repository status (uncommitted changes, unpushed commits)"""
    if not Path(repo_dir).is_dir():
        return "Not Cloned"

    # Check for uncommitted changes
    ret, _ = run_git(repo_dir, 'diff-index', '--quiet', 'HEAD', '--')
    if ret != 0:
        return "Uncommitted"

    # Check if branch tracks a remote
    ret, _ = run_git(repo_dir, 'rev-parse', '@{u}')
    if ret != 0:
        return "No Remote"

    # Check for unpushed commits
    ret, unpushed_out = run_git(repo_dir, 'log', '@{u}..', '--oneline')
    unpushed = len(unpushed_out.strip().split('\n')) if unpushed_out.strip() else 0
    if unpushed > 0:
        return f"{unpushed} Unpushed"

    return "OK"

def get_repo_remote_status(repo_dir: str) -> str:
    """Get remote repository status (unpulled commits after fetch)"""
    if not Path(repo_dir).is_dir():
        return "Not Cloned"

    # Check if branch tracks a remote
    ret, _ = run_git(repo_dir, 'rev-parse', '@{u}')
    if ret != 0:
        return "No Remote"

    # Fetch from remote
    ret, _ = run_git(repo_dir, 'fetch', '--quiet')
    if ret != 0:
        return "Fetch Failed"

    # Check for unpulled commits
    ret, unpulled_out = run_git(repo_dir, 'log', 'HEAD..@{u}', '--oneline')
    unpulled = len(unpulled_out.strip().split('\n')) if unpulled_out.strip() else 0
    if unpulled > 0:
        return f"{unpulled} To Pull"

    return "Up to Date"

def process_repo(repo_dir: str, repo_url: str, strategy: str, action: str, work_dir: str) -> List[str]:
    """Process a repository with given action, return list of log messages"""
    logs = []
    logs.append(f"==> Processing '{repo_dir}'")

    repo_path = str(Path(work_dir) / repo_dir)

    if not Path(repo_path).is_dir():
        logs.append(f"  Cloning '{repo_dir}'...")
        ret, output = run_git(work_dir, 'clone', repo_url, repo_dir)
        if ret == 0:
            logs.append(f"  ✓ Clone complete.")
        else:
            logs.append(f"  ✗ Clone failed: {output}")
        return logs

    if action == 'sync':
        # Commit uncommitted changes
        ret, _ = run_git(repo_path, 'diff-index', '--quiet', 'HEAD', '--')
        if ret != 0:
            logs.append("  Found uncommitted changes, committing before pull...")
            run_git(repo_path, 'add', '.')
            ret, _ = run_git(repo_path, 'commit', '-q', '-m', 'Auto-commit before pull')
            if ret == 0:
                logs.append("  ✓ Changes committed.")
            else:
                logs.append("  ✗ Commit failed.")
                return logs

        # Pull
        logs.append(f"  Pulling with strategy: {strategy}")
        ret, output = run_git(repo_path, 'pull', '--no-rebase', f'--strategy-option={strategy}')
        if ret == 0:
            logs.append("  ✓ Pull complete.")

            # Add and commit any changes
            run_git(repo_path, 'add', '.')
            ret, _ = run_git(repo_path, 'diff-index', '--quiet', '--cached', 'HEAD', '--')
            if ret != 0:
                logs.append("  Found changes, committing with default message 'fixes'...")
                ret, _ = run_git(repo_path, 'commit', '-q', '-m', 'fixes')
                if ret == 0:
                    logs.append("  ✓ Commit complete.")

            # Push
            logs.append("  Pushing changes...")
            ret, _ = run_git(repo_path, 'push')
            if ret == 0:
                logs.append("  ✓ Push complete.")
            else:
                logs.append("  ✗ Push failed.")
        else:
            logs.append(f"  ✗ Pull failed: {output[:200]}")

    elif action == 'push':
        run_git(repo_path, 'add', '.')
        ret, _ = run_git(repo_path, 'diff-index', '--quiet', '--cached', 'HEAD', '--')
        if ret != 0:
            logs.append("  Found changes, committing with default message 'fixes'...")
            ret, _ = run_git(repo_path, 'commit', '-q', '-m', 'fixes')
            if ret == 0:
                logs.append("  ✓ Commit complete.")

        logs.append("  Pushing changes...")
        ret, _ = run_git(repo_path, 'push')
        if ret == 0:
            logs.append("  ✓ Push complete.")
        else:
            logs.append("  ✗ Push failed.")

    elif action == 'pull':
        # Commit uncommitted changes
        ret, _ = run_git(repo_path, 'diff-index', '--quiet', 'HEAD', '--')
        if ret != 0:
            logs.append("  Found uncommitted changes, committing before pull...")
            run_git(repo_path, 'add', '.')
            ret, _ = run_git(repo_path, 'commit', '-q', '-m', 'Auto-commit before pull')
            if ret == 0:
                logs.append("  ✓ Changes committed.")

        logs.append(f"  Pulling with strategy: {strategy}")
        ret, output = run_git(repo_path, 'pull', '--no-rebase', f'--strategy-option={strategy}')
        if ret == 0:
            logs.append("  ✓ Pull complete.")
        else:
            logs.append(f"  ✗ Pull failed: {output[:200]}")

    elif action == 'status':
        logs.append(f"  Checking '{repo_dir}'")

        # Check for uncommitted changes
        ret, _ = run_git(repo_path, 'diff-index', '--quiet', 'HEAD', '--')
        if ret != 0:
            logs.append("  ⚠ Has uncommitted changes")
            _, status_output = run_git(repo_path, 'status', '--short')
            for line in status_output.strip().split('\n')[:5]:
                logs.append(f"    {line}")
        else:
            logs.append("  ✓ Working tree clean")

        # Check for unpushed commits
        ret, unpushed_out = run_git(repo_path, 'log', '@{u}..', '--oneline')
        unpushed = len(unpushed_out.strip().split('\n')) if unpushed_out.strip() else 0
        if unpushed > 0:
            logs.append(f"  ⚠ Has {unpushed} unpushed commit(s)")
        else:
            ret, _ = run_git(repo_path, 'rev-parse', '@{u}')
            if ret == 0:
                logs.append("  ✓ All commits pushed")
            else:
                logs.append("  ⚠ Branch does not track a remote")

    elif action == 'fetch':
        logs.append(f"  Fetching in '{repo_dir}'...")
        ret, _ = run_git(repo_path, 'fetch')
        if ret == 0:
            logs.append("  ✓ Fetch complete.")
        else:
            logs.append("  ✗ Fetch failed.")

    elif action == 'untracked':
        logs.append(f"  Checking '{repo_dir}'")
        _, untracked_output = run_git(repo_path, 'ls-files', '--others', '--exclude-standard')
        if untracked_output.strip():
            untracked_files = untracked_output.strip().split('\n')
            logs.append(f"  ⚠ Has {len(untracked_files)} untracked file(s)")
            for f in untracked_files[:10]:
                logs.append(f"    {f}")
        else:
            logs.append("  ✓ No untracked files")

    elif action == 'ignored':
        logs.append(f"  Checking '{repo_dir}'")
        _, ignored_output = run_git(repo_path, 'ls-files', '--others', '--ignored', '--exclude-standard')
        if ignored_output.strip():
            ignored_files = ignored_output.strip().split('\n')
            logs.append(f"  ⚠ Has {len(ignored_files)} ignored file(s)")
            for f in ignored_files[:10]:
                logs.append(f"    {f}")
        else:
            logs.append("  ✓ No ignored files")

    return logs

# --- TUI Implementation ---

class TUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.running = True

        # State variables
        self.repos = sorted(ALL_REPOS.keys())
        self.repo_selection = [True] * len(self.repos)
        self.repo_local_status = ["Not Checked"] * len(self.repos)
        self.repo_remote_status = ["Not Checked"] * len(self.repos)

        self.workdir_selected = 1  # 0=current dir, 1=custom path
        self.workdir_path = "/home/diego/Documents/Git"
        self.strategy_selected = 1  # 0=local (ours), 1=remote (theirs)
        self.action_selected = 0  # 0=sync, 1=push, 2=pull, 3=status, 4=fetch, 5=untracked, 6=ignored
        self.repo_cursor = 0
        self.repo_scroll_offset = 0  # For scrolling through repos
        self.current_field = 0  # 0=workdir, 1=strategy, 2=action, 3=repos, 4=run
        self.total_fields = 5
        self.status_message = ""  # For showing refresh status

        # Initialize curses
        curses.curs_set(0)
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_CYAN)  # Highlight
            curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_GREEN)  # Run button

        # Do a quick local status scan on startup
        self.status_message = "Loading repository statuses..."
        self.draw()  # Show loading message
        self.refresh_local_status()

    def refresh_local_status(self):
        """Refresh local repository status (fast, no remote fetch)"""
        work_dir = "." if self.workdir_selected == 0 else self.workdir_path
        if not Path(work_dir).is_dir():
            return

        for i, repo in enumerate(self.repos):
            self.status_message = f"Refreshing local status... ({i+1}/{len(self.repos)})"
            self.draw()  # Update display during refresh
            repo_path = str(Path(work_dir) / repo)
            self.repo_local_status[i] = get_repo_local_status(repo_path)

        self.status_message = ""

    def refresh_remote_status(self):
        """Refresh remote repository status (slow, does fetch)"""
        work_dir = "." if self.workdir_selected == 0 else self.workdir_path
        if not Path(work_dir).is_dir():
            return

        for i, repo in enumerate(self.repos):
            self.status_message = f"Fetching remote status... ({i+1}/{len(self.repos)})"
            self.draw()  # Update display during refresh
            repo_path = str(Path(work_dir) / repo)
            self.repo_remote_status[i] = get_repo_remote_status(repo_path)

        self.status_message = ""

    def draw(self):
        """Draw the entire interface"""
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()

        row = 0

        # Title
        title = "╔══════════════════════════════════════════╗"
        self.stdscr.addstr(row, 2, title, curses.color_pair(1) | curses.A_BOLD)
        row += 1
        self.stdscr.addstr(row, 2, "║ gcl.py - Git Sync Manager               ║", curses.color_pair(1) | curses.A_BOLD)
        row += 1
        self.stdscr.addstr(row, 2, "╚══════════════════════════════════════════╝", curses.color_pair(1) | curses.A_BOLD)
        row += 2

        # Working Directory
        self.stdscr.addstr(row, 2, "WORKING DIRECTORY:", curses.color_pair(2) | curses.A_BOLD)
        row += 1
        self.stdscr.addstr(row, 2, "══════════════════", curses.color_pair(2))
        row += 1

        opt0 = f"[{'●' if self.workdir_selected == 0 else ' '}] Current Directory (.)"
        attr0 = curses.color_pair(6) if self.current_field == 0 and self.workdir_selected == 0 else curses.A_NORMAL
        self.stdscr.addstr(row, 4, opt0, attr0)
        row += 1

        opt1 = f"[{'●' if self.workdir_selected == 1 else ' '}] Custom Path: {self.workdir_path}"
        attr1 = curses.color_pair(6) if self.current_field == 0 and self.workdir_selected == 1 else curses.A_NORMAL
        self.stdscr.addstr(row, 4, opt1, attr1)
        row += 3

        # Merge Strategy
        self.stdscr.addstr(row, 2, "MERGE STRATEGY (On Conflict):", curses.color_pair(2) | curses.A_BOLD)
        row += 1
        self.stdscr.addstr(row, 2, "══════════════════════════════", curses.color_pair(2))
        row += 1

        # Strategy 0: LOCAL with 'O' highlighted
        marker0 = '●' if self.strategy_selected == 0 else ' '
        attr_s0 = curses.color_pair(6) if self.current_field == 1 and self.strategy_selected == 0 else curses.A_NORMAL
        if self.current_field == 1 and self.strategy_selected == 0:
            self.stdscr.addstr(row, 4, f"[{marker0}] LOCAL  (Keep local changes)", attr_s0)
        else:
            self.stdscr.addstr(row, 4, f"[{marker0}] L")
            self.stdscr.addstr(row, 9, "O", curses.color_pair(5) | curses.A_BOLD)
            self.stdscr.addstr(row, 10, "CAL  (Keep local changes)")
        row += 1

        # Strategy 1: REMOTE with 'E' highlighted
        marker1 = '●' if self.strategy_selected == 1 else ' '
        attr_s1 = curses.color_pair(6) if self.current_field == 1 and self.strategy_selected == 1 else curses.A_NORMAL
        if self.current_field == 1 and self.strategy_selected == 1:
            self.stdscr.addstr(row, 4, f"[{marker1}] REMOTE (Overwrite with remote)", attr_s1)
        else:
            self.stdscr.addstr(row, 4, f"[{marker1}] R")
            self.stdscr.addstr(row, 9, "E", curses.color_pair(5) | curses.A_BOLD)
            self.stdscr.addstr(row, 10, "MOTE (Overwrite with remote)")
        row += 3

        # Action
        self.stdscr.addstr(row, 2, "ACTION:", curses.color_pair(2) | curses.A_BOLD)
        row += 1
        self.stdscr.addstr(row, 2, "═══════", curses.color_pair(2))
        row += 1

        # Actions with highlighted shortcut letters
        actions_data = [
            (0, "SYNC   (Remote <-> Local)", "S", 0),
            (1, "PUSH   (Local -> Remote)", "P", 0),
            (2, "PULL   (Remote -> Local)", "PU", "L", "L (Remote -> Local)"),
            (None, None, None, None),  # blank line
            (3, "STATUS (Check repos)", "S", "T", "ATUS (Check repos)"),
            (4, "FETCH  (Fetch from remote)", "F", 0),
            (5, "UNTRACKED (List untracked files)", "U", "N", "TRACKED (List untracked files)"),
            (6, "IGNORED (List ignored files)", "I", 0),
        ]

        for action_info in actions_data:
            if action_info[0] is None:  # blank line
                row += 1
                continue

            action_idx = action_info[0]
            marker = '●' if self.action_selected == action_idx else ' '
            attr = curses.color_pair(6) if self.current_field == 2 and self.action_selected == action_idx else curses.A_NORMAL

            # If this action is currently selected, use solid highlight
            if self.current_field == 2 and self.action_selected == action_idx:
                self.stdscr.addstr(row, 4, f"[{marker}] {action_info[1]}", attr)
            else:
                # Draw with highlighted shortcut letter
                if action_idx == 0:  # SYNC
                    self.stdscr.addstr(row, 4, f"[{marker}] ")
                    self.stdscr.addstr(row, 8, "S", curses.color_pair(5) | curses.A_BOLD)
                    self.stdscr.addstr(row, 9, "YNC   (Remote <-> Local)")
                elif action_idx == 1:  # PUSH
                    self.stdscr.addstr(row, 4, f"[{marker}] ")
                    self.stdscr.addstr(row, 8, "P", curses.color_pair(5) | curses.A_BOLD)
                    self.stdscr.addstr(row, 9, "USH   (Local -> Remote)")
                elif action_idx == 2:  # PULL
                    self.stdscr.addstr(row, 4, f"[{marker}] PU")
                    self.stdscr.addstr(row, 10, "L", curses.color_pair(5) | curses.A_BOLD)
                    self.stdscr.addstr(row, 11, "L   (Remote -> Local)")
                elif action_idx == 3:  # STATUS
                    self.stdscr.addstr(row, 4, f"[{marker}] S")
                    self.stdscr.addstr(row, 9, "T", curses.color_pair(5) | curses.A_BOLD)
                    self.stdscr.addstr(row, 10, "ATUS (Check repos)")
                elif action_idx == 4:  # FETCH
                    self.stdscr.addstr(row, 4, f"[{marker}] ")
                    self.stdscr.addstr(row, 8, "F", curses.color_pair(5) | curses.A_BOLD)
                    self.stdscr.addstr(row, 9, "ETCH  (Fetch from remote)")
                elif action_idx == 5:  # UNTRACKED
                    self.stdscr.addstr(row, 4, f"[{marker}] U")
                    self.stdscr.addstr(row, 9, "N", curses.color_pair(5) | curses.A_BOLD)
                    self.stdscr.addstr(row, 10, "TRACKED (List untracked files)")
                elif action_idx == 6:  # IGNORED
                    self.stdscr.addstr(row, 4, f"[{marker}] ")
                    self.stdscr.addstr(row, 8, "I", curses.color_pair(5) | curses.A_BOLD)
                    self.stdscr.addstr(row, 9, "GNORED (List ignored files)")
            row += 1

        row += 2

        # Repositories
        repo_start_row = row
        self.stdscr.addstr(row, 2, "REPOSITORIES (Toggle with SPACE):", curses.color_pair(2) | curses.A_BOLD)
        self.stdscr.addstr(row, 40, "LOCAL STATUS:", curses.color_pair(2) | curses.A_BOLD)
        self.stdscr.addstr(row, 60, "REMOTE STATUS:", curses.color_pair(2) | curses.A_BOLD)
        row += 1
        self.stdscr.addstr(row, 2, "═════════════════════════════════", curses.color_pair(2))
        self.stdscr.addstr(row, 40, "═════════════", curses.color_pair(2))
        self.stdscr.addstr(row, 60, "══════════════", curses.color_pair(2))
        row += 1

        max_visible_repos = min(14, h - row - 10)  # Show up to 14 repos

        # Display repos with scrolling support
        for i in range(max_visible_repos):
            repo_idx = self.repo_scroll_offset + i
            if repo_idx >= len(self.repos):
                break

            marker = "✓" if self.repo_selection[repo_idx] else " "
            repo_line = f"[{marker}] {self.repos[repo_idx]:<30}"

            local_status = self.repo_local_status[repo_idx]
            remote_status = self.repo_remote_status[repo_idx]

            # Determine color for local status
            local_color = curses.A_NORMAL
            if "OK" in local_status:
                local_color = curses.color_pair(3)
            elif "Not Cloned" in local_status or "Uncommitted" in local_status or "Unpushed" in local_status:
                local_color = curses.color_pair(4)
            elif "No Remote" in local_status:
                local_color = curses.color_pair(4)

            # Determine color for remote status
            remote_color = curses.A_NORMAL
            if "Up to Date" in remote_status:
                remote_color = curses.color_pair(3)
            elif "Not Cloned" in remote_status or "To Pull" in remote_status or "Fetch Failed" in remote_status:
                remote_color = curses.color_pair(4)
            elif "Not Checked" in remote_status:
                remote_color = curses.color_pair(5)

            if self.current_field == 3 and repo_idx == self.repo_cursor:
                self.stdscr.addstr(row, 4, repo_line, curses.color_pair(6))
                self.stdscr.addstr(row, 40, f"{local_status:<18}", curses.color_pair(6))
                self.stdscr.addstr(row, 60, remote_status, curses.color_pair(6))
            else:
                self.stdscr.addstr(row, 4, repo_line)
                self.stdscr.addstr(row, 40, f"{local_status:<18}", local_color)
                self.stdscr.addstr(row, 60, remote_status, remote_color)
            row += 1

        row += 1

        # RUN button
        run_text = "   [ RUN ]   "
        run_attr = curses.color_pair(7) | curses.A_BOLD if self.current_field == 4 else curses.A_BOLD
        self.stdscr.addstr(row, 2, run_text, run_attr)
        row += 3

        # Status message (if refreshing)
        if self.status_message:
            row += 1
            self.stdscr.addstr(row, 2, self.status_message, curses.color_pair(5) | curses.A_BOLD)
            row += 1

        # Help text
        row = h - 8
        self.stdscr.addstr(row, 2, "KEYBOARD SHORTCUTS", curses.color_pair(2) | curses.A_BOLD)
        row += 1
        self.stdscr.addstr(row, 2, "═══════════════════", curses.color_pair(2))
        row += 1

        # Navigate line
        col = 2
        self.stdscr.addstr(row, col, "Navigate: (", curses.A_BOLD)
        col += 11
        self.stdscr.addstr(row, col, "↑", curses.color_pair(5) | curses.A_BOLD)
        col += 1
        self.stdscr.addstr(row, col, "/", curses.A_BOLD)
        col += 1
        self.stdscr.addstr(row, col, "↓", curses.color_pair(5) | curses.A_BOLD)
        col += 1
        self.stdscr.addstr(row, col, ") List | (")
        col += 10
        self.stdscr.addstr(row, col, "TAB", curses.color_pair(5) | curses.A_BOLD)
        col += 3
        self.stdscr.addstr(row, col, ") Field | (")
        col += 11
        self.stdscr.addstr(row, col, "SPACE", curses.color_pair(5) | curses.A_BOLD)
        col += 5
        self.stdscr.addstr(row, col, ") Toggle | (")
        col += 12
        self.stdscr.addstr(row, col, "ENTER", curses.color_pair(5) | curses.A_BOLD)
        col += 5
        self.stdscr.addstr(row, col, ") Run | (")
        col += 9
        self.stdscr.addstr(row, col, "q", curses.color_pair(5) | curses.A_BOLD)
        col += 1
        self.stdscr.addstr(row, col, ") Quit")
        row += 1

        # Select line
        col = 2
        self.stdscr.addstr(row, col, "Select:   (", curses.A_BOLD)
        col += 11
        self.stdscr.addstr(row, col, "a", curses.color_pair(5) | curses.A_BOLD)
        col += 1
        self.stdscr.addstr(row, col, ") All | (")
        col += 9
        self.stdscr.addstr(row, col, "u", curses.color_pair(5) | curses.A_BOLD)
        col += 1
        self.stdscr.addstr(row, col, ") None | (")
        col += 10
        self.stdscr.addstr(row, col, "k", curses.color_pair(5) | curses.A_BOLD)
        col += 1
        self.stdscr.addstr(row, col, ") Not OK")
        row += 1

        # Strategy line
        col = 2
        self.stdscr.addstr(row, col, "Strategy: (", curses.A_BOLD)
        col += 11
        self.stdscr.addstr(row, col, "o", curses.color_pair(5) | curses.A_BOLD)
        col += 1
        self.stdscr.addstr(row, col, ") Local | (")
        col += 11
        self.stdscr.addstr(row, col, "e", curses.color_pair(5) | curses.A_BOLD)
        col += 1
        self.stdscr.addstr(row, col, ") Remote")
        row += 1

        # Actions line
        col = 2
        self.stdscr.addstr(row, col, "Actions:  (", curses.A_BOLD)
        col += 11
        self.stdscr.addstr(row, col, "s", curses.color_pair(5) | curses.A_BOLD)
        col += 1
        self.stdscr.addstr(row, col, ") Sync | (")
        col += 10
        self.stdscr.addstr(row, col, "p", curses.color_pair(5) | curses.A_BOLD)
        col += 1
        self.stdscr.addstr(row, col, ") Push | (")
        col += 10
        self.stdscr.addstr(row, col, "l", curses.color_pair(5) | curses.A_BOLD)
        col += 1
        self.stdscr.addstr(row, col, ") Pull | (")
        col += 10
        self.stdscr.addstr(row, col, "f", curses.color_pair(5) | curses.A_BOLD)
        col += 1
        self.stdscr.addstr(row, col, ") Fetch")
        row += 1

        # Actions continued line
        col = 12
        self.stdscr.addstr(row, col, "(")
        col += 1
        self.stdscr.addstr(row, col, "n", curses.color_pair(5) | curses.A_BOLD)
        col += 1
        self.stdscr.addstr(row, col, ") Untracked | (")
        col += 15
        self.stdscr.addstr(row, col, "t", curses.color_pair(5) | curses.A_BOLD)
        col += 1
        self.stdscr.addstr(row, col, ") Status | (")
        col += 12
        self.stdscr.addstr(row, col, "r", curses.color_pair(5) | curses.A_BOLD)
        col += 1
        self.stdscr.addstr(row, col, ") Refresh")

        self.stdscr.refresh()

    def handle_input(self, key):
        """Handle keyboard input"""
        if key == ord('q'):
            self.running = False

        elif key == curses.KEY_UP:
            if self.current_field == 3:  # In repo list
                self.repo_cursor = max(0, self.repo_cursor - 1)
                # Adjust scroll offset if cursor goes above visible area
                if self.repo_cursor < self.repo_scroll_offset:
                    self.repo_scroll_offset = self.repo_cursor
            else:
                self.current_field = (self.current_field - 1) % self.total_fields

        elif key == curses.KEY_DOWN:
            if self.current_field == 3:  # In repo list
                self.repo_cursor = min(len(self.repos) - 1, self.repo_cursor + 1)
                # Adjust scroll offset if cursor goes below visible area
                h, w = self.stdscr.getmaxyx()
                max_visible = min(14, h - 30)
                if self.repo_cursor >= self.repo_scroll_offset + max_visible:
                    self.repo_scroll_offset = self.repo_cursor - max_visible + 1
            else:
                self.current_field = (self.current_field + 1) % self.total_fields

        elif key == ord('\t') or key == 9:  # TAB
            self.current_field = (self.current_field + 1) % self.total_fields

        elif key == ord(' '):  # SPACE
            if self.current_field == 0:  # Toggle workdir
                self.workdir_selected = 1 - self.workdir_selected
            elif self.current_field == 1:  # Toggle strategy
                self.strategy_selected = 1 - self.strategy_selected
            elif self.current_field == 2:  # Cycle action
                self.action_selected = (self.action_selected + 1) % 7
            elif self.current_field == 3:  # Toggle repo selection
                self.repo_selection[self.repo_cursor] = not self.repo_selection[self.repo_cursor]

        elif key == ord('\n') or key == ord('\r') or key == 10 or key == 13:  # ENTER
            self.execute_action()

        # Shortcuts
        elif key == ord('a'):  # Select all
            self.repo_selection = [True] * len(self.repos)

        elif key == ord('u'):  # Unselect all
            self.repo_selection = [False] * len(self.repos)

        elif key == ord('k'):  # Select not OK
            for i in range(len(self.repos)):
                if self.repo_local_status[i] != "OK":
                    self.repo_selection[i] = True
                else:
                    self.repo_selection[i] = False

        elif key == ord('o'):  # Local strategy
            self.strategy_selected = 0

        elif key == ord('e'):  # Remote strategy
            self.strategy_selected = 1

        elif key == ord('s'):  # Sync action
            self.action_selected = 0

        elif key == ord('p'):  # Push action
            self.action_selected = 1

        elif key == ord('l'):  # Pull action
            self.action_selected = 2

        elif key == ord('t'):  # Status action
            self.action_selected = 3
            self.refresh_local_status()

        elif key == ord('f'):  # Fetch action
            self.action_selected = 4
            self.refresh_remote_status()

        elif key == ord('n'):  # Untracked action
            self.action_selected = 5

        elif key == ord('i'):  # Ignored action
            self.action_selected = 6

        elif key == ord('r'):  # Refresh
            self.refresh_local_status()
            self.refresh_remote_status()

    def execute_action(self):
        """Execute the selected action on selected repos"""
        # Properly end curses mode
        curses.endwin()

        # Clear screen and show header
        os.system('clear')
        print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 63}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}                    Executing Actions...                       {Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 63}{Colors.RESET}")
        print()

        work_dir = "." if self.workdir_selected == 0 else self.workdir_path

        if not Path(work_dir).is_dir():
            error(f"Working directory does not exist: {work_dir}")
            print(f"\n{Colors.YELLOW}Press 'q' to quit or any other key to return to menu.{Colors.RESET}")

            choice = input()
            if choice.lower() == 'q':
                self.running = False
                return

            # Reinitialize curses and return
            self.stdscr = curses.initscr()
            curses.curs_set(0)
            if curses.has_colors():
                curses.start_color()
                curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
                curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
                curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
                curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
                curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
                curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_CYAN)
                curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_GREEN)

            # Refresh status when returning to menu
            self.status_message = "Refreshing repository statuses..."
            self.draw()
            self.refresh_local_status()
            self.draw()  # Redraw without status message
            return

        strategy = 'ours' if self.strategy_selected == 0 else 'theirs'
        action_names = ['sync', 'push', 'pull', 'status', 'fetch', 'untracked', 'ignored']
        action = action_names[self.action_selected]

        selected_repos = [self.repos[i] for i in range(len(self.repos)) if self.repo_selection[i]]

        if not selected_repos:
            warn("No repositories selected. Nothing to do.")
        else:
            for repo_name in selected_repos:
                repo_url = ALL_REPOS.get(repo_name, '')
                logs = process_repo(repo_name, repo_url, strategy, action, work_dir)
                for log_msg in logs:
                    print(log_msg)
                print()

        print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 63}{Colors.RESET}")
        print(f"{Colors.GREEN}{Colors.BOLD}                  All tasks complete!                          {Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 63}{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Press 'q' to quit or any other key to return to menu.{Colors.RESET}")

        # Wait for user input (requires pressing Enter, just like gcl.sh)
        choice = input()

        if choice.lower() == 'q':
            self.running = False
        else:
            # Reinitialize curses
            self.stdscr = curses.initscr()
            curses.curs_set(0)
            if curses.has_colors():
                curses.start_color()
                curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
                curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
                curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
                curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
                curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
                curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_CYAN)
                curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_GREEN)

            # Refresh status when returning to menu
            self.status_message = "Refreshing repository statuses..."
            self.draw()
            self.refresh_local_status()
            self.draw()  # Redraw without status message

    def run(self):
        """Main TUI loop"""
        while self.running:
            self.draw()
            key = self.stdscr.getch()
            if key != -1:
                self.handle_input(key)

def run_tui(stdscr):
    TUI(stdscr).run()

# --- CLI Actions ---
def run_cli_sync(strategy: str = 'remote', repos: Optional[List[str]] = None, work_dir: str = "."):
    git_strategy = 'ours' if strategy == 'local' else 'theirs'
    log(f"Starting Bidirectional Sync (Strategy: {git_strategy})")
    repos_to_process = repos if repos else list(ALL_REPOS.keys())
    for repo_name in repos_to_process:
        repo_url = ALL_REPOS.get(repo_name, '')
        if repo_url:
            logs = process_repo(repo_name, repo_url, git_strategy, 'sync', work_dir)
            for log_msg in logs:
                print(log_msg)
            print()

def run_cli_push(repos: Optional[List[str]] = None, work_dir: str = "."):
    log("Starting Push")
    repos_to_process = repos if repos else list(ALL_REPOS.keys())
    for repo_name in repos_to_process:
        repo_url = ALL_REPOS.get(repo_name, '')
        if repo_url:
            logs = process_repo(repo_name, repo_url, 'theirs', 'push', work_dir)
            for log_msg in logs:
                print(log_msg)
            print()

def run_cli_pull(repos: Optional[List[str]] = None, work_dir: str = "."):
    log("Starting Pull")
    repos_to_process = repos if repos else list(ALL_REPOS.keys())
    for repo_name in repos_to_process:
        repo_url = ALL_REPOS.get(repo_name, '')
        if repo_url:
            logs = process_repo(repo_name, repo_url, 'theirs', 'pull', work_dir)
            for log_msg in logs:
                print(log_msg)
            print()

def run_cli_status(repos: Optional[List[str]] = None, work_dir: str = "."):
    log("Checking Status")
    repos_to_process = repos if repos else list(ALL_REPOS.keys())
    for repo_name in repos_to_process:
        repo_url = ALL_REPOS.get(repo_name, '')
        if repo_url:
            logs = process_repo(repo_name, repo_url, 'theirs', 'status', work_dir)
            for log_msg in logs:
                print(log_msg)
            print()

def run_cli_untracked(repos: Optional[List[str]] = None, work_dir: str = "."):
    log("Listing Untracked Files")
    repos_to_process = repos if repos else list(ALL_REPOS.keys())
    for repo_name in repos_to_process:
        repo_url = ALL_REPOS.get(repo_name, '')
        if repo_url:
            logs = process_repo(repo_name, repo_url, 'theirs', 'untracked', work_dir)
            for log_msg in logs:
                print(log_msg)
            print()

def run_cli_ignored(repos: Optional[List[str]] = None, work_dir: str = "."):
    log("Listing Ignored Files")
    repos_to_process = repos if repos else list(ALL_REPOS.keys())
    for repo_name in repos_to_process:
        repo_url = ALL_REPOS.get(repo_name, '')
        if repo_url:
            logs = process_repo(repo_name, repo_url, 'theirs', 'ignored', work_dir)
            for log_msg in logs:
                print(log_msg)
            print()

def run_cli_fetch(repos: Optional[List[str]] = None, work_dir: str = "."):
    log("Fetching")
    repos_to_process = repos if repos else list(ALL_REPOS.keys())
    for repo_name in repos_to_process:
        repo_url = ALL_REPOS.get(repo_name, '')
        if repo_url:
            logs = process_repo(repo_name, repo_url, 'theirs', 'fetch', work_dir)
            for log_msg in logs:
                print(log_msg)
            print()

def main():
    """Main entry point for CLI and TUI"""
    parser = argparse.ArgumentParser(
        description='gcl.py - Git Clone/Pull/Push Manager',
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False # We will handle help manually
    )
    parser.add_argument('command', nargs='?', default=None, help='Command to execute')
    parser.add_argument('args', nargs='*', help='Additional arguments for the command')

    args = parser.parse_args()

    if args.command is None:
        try:
            curses.wrapper(run_tui)
        except curses.error as e:
            error(f"Curses error: {e}")
        sys.exit(0)

    cmd = args.command.lower()
    if cmd in ('help', '-h', '--help'):
        print(f"{Colors.BOLD}{Colors.CYAN}gcl.py - Git Clone/Pull/Push Manager{Colors.RESET}\n")
        print("Manages multiple git repositories via a TUI or command-line arguments.\n")
        print(f"{Colors.BOLD}{Colors.YELLOW}USAGE:{Colors.RESET}")
        print("  gcl.py [command] [options]\n")
        print(f"{Colors.BOLD}{Colors.YELLOW}COMMANDS:{Colors.RESET}")
        print(f"  (no command)\t\tLaunches the interactive TUI menu.")
        print(f"  {Colors.GREEN}sync [local|remote]{Colors.RESET}\tBidirectional sync. Default: 'remote'.")
        print(f"  {Colors.GREEN}push{Colors.RESET}\t\t\tPushes committed changes.")
        print(f"  {Colors.GREEN}pull{Colors.RESET}\t\t\tPulls using 'remote' strategy.")
        print(f"  {Colors.GREEN}fetch{Colors.RESET}\t\t\tFetches from remote.")
        print(f"  {Colors.GREEN}status{Colors.RESET}\t\t\tChecks git status for all repos.")
        print(f"  {Colors.GREEN}untracked{Colors.RESET}\t\tLists untracked files (excluding ignored).")
        print(f"  {Colors.GREEN}ignored{Colors.RESET}\t\t\tLists all ignored files.")
        print(f"  {Colors.GREEN}help{Colors.RESET}\t\t\tShows this help message.")
        sys.exit(0)

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
    elif cmd == 'ignored':
        run_cli_ignored()
    elif cmd == 'fetch':
        run_cli_fetch()
    else:
        error(f"Invalid command: {cmd}")
        parser.print_help()
        sys.exit(1)


def is_git_installed():
    """Check if git is installed"""
    try:
        subprocess.run(['git', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

if __name__ == "__main__":
    try:
        if not is_git_installed():
            print(f"{Colors.RED}Error: 'git' command not found. Please install Git and ensure it's in your PATH.{Colors.RESET}")
            sys.exit(1)
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}Application crashed unexpectedly: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
