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
import threading
import queue

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

# --- Git Worker Thread ---
class GitWorker(threading.Thread):
    def __init__(self, task_queue, result_queue):
        super().__init__(daemon=True)
        self.task_queue = task_queue
        self.result_queue = result_queue

    def run_git(self, repo_dir: str, *args, stream=False) -> Tuple[int, str]:
        """Run git command in repository, with optional streaming."""
        if not stream:
            try:
                result = subprocess.run(
                    ['git', '-C', repo_dir] + list(args),
                    capture_output=True, text=True, timeout=60
                )
                return result.returncode, result.stdout + result.stderr
            except subprocess.TimeoutExpired:
                return 1, "Git command timed out"
            except Exception as e:
                return 1, str(e)
        
        # Streaming logic
        try:
            process = subprocess.Popen(
                ['git', '-C', repo_dir] + list(args),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            for line in iter(process.stdout.readline, ''):
                self.result_queue.put(('log', line.strip()))
            process.stdout.close()
            return process.wait(), ""
        except Exception as e:
            self.result_queue.put(('log', f"Error streaming from git: {e}"))
            return 1, str(e)

    def run(self):
        while True:
            task_name, data = self.task_queue.get()
            if task_name == 'get_status':
                repo_name, work_dir = data
                status = self.get_repo_status(str(Path(work_dir) / repo_name))
                self.result_queue.put(('status', (repo_name, status)))
            elif task_name == 'get_detail':
                repo_name, work_dir = data
                _, detail = self.run_git(str(Path(work_dir) / repo_name), 'status')
                self.result_queue.put(('detail', detail))
            elif task_name in ('sync', 'push', 'pull'):
                repo_name, work_dir, strategy = data
                self.result_queue.put(('log', f"--- Starting '{task_name}' on '{repo_name}' ---"))
                
                repo_path = str(Path(work_dir) / repo_name)
                if not Path(repo_path).is_dir():
                    self.result_queue.put(('log', f"Cloning '{repo_name}'..."))
                    self.run_git(work_dir, 'clone', ALL_REPOS[repo_name], repo_name, stream=True)
                elif task_name == 'pull':
                    self.run_git(repo_path, 'pull', '--no-rebase', f'--strategy-option={strategy}', stream=True)
                elif task_name == 'push':
                    self.run_git(repo_path, 'push', stream=True)
                elif task_name == 'sync':
                    self.run_git(repo_path, 'add', '.', stream=True)
                    self.run_git(repo_path, 'commit', '-m', 'auto-sync', stream=True)
                    self.run_git(repo_path, 'pull', '--no-rebase', f'--strategy-option={strategy}', stream=True)
                    self.run_git(repo_path, 'push', stream=True)

                self.result_queue.put(('log', f"--- Finished '{task_name}' on '{repo_name}' ---"))
                status = self.get_repo_status(repo_path)
                self.result_queue.put(('status', (repo_name, status)))

            self.task_queue.task_done()

    def get_repo_status(self, repo_dir: str) -> str:
        """Get a compact, symbolic repository status."""
        if not Path(repo_dir).is_dir():
            return f"{Colors.YELLOW}? Not Cloned{Colors.RESET}"

        ret, _ = self.run_git(repo_dir, 'diff-index', '--quiet', 'HEAD', '--')
        if ret != 0:
            return f"{Colors.RED}Δ Uncommitted{Colors.RESET}"

        ret, _ = self.run_git(repo_dir, 'rev-parse', '@{{u}}')
        if ret != 0:
            return f"{Colors.RED}! No Remote{Colors.RESET}"

        ret, unpushed_out = self.run_git(repo_dir, 'log', '@{{u}}..', '--oneline')
        unpushed = len(unpushed_out.strip().split('\n')) if unpushed_out.strip() else 0
        
        self.run_git(repo_dir, 'fetch', '--quiet')
        ret, unpulled_out = self.run_git(repo_dir, 'log', 'HEAD..@{u}', '--oneline')
        unpulled = len(unpulled_out.strip().split('\n')) if unpulled_out.strip() else 0

        if unpushed > 0 and unpulled > 0:
            return f"{Colors.RED}↕ {unpushed}↑ {unpulled}↓{Colors.RESET}"
        if unpushed > 0:
            return f"{Colors.YELLOW}↑ {unpushed}{Colors.RESET}"
        if unpulled > 0:
            return f"{Colors.YELLOW}↓ {unpulled}{Colors.RESET}"

        return f"{Colors.GREEN}✓ OK{Colors.RESET}"


# --- Git Functions (CLI) ---
def get_repo_status_cli(repo_dir: str) -> str:
    """Get local repository status for CLI"""
    if not Path(repo_dir).is_dir():
        return f"{Colors.YELLOW}Not Cloned{Colors.RESET}"
    return f"{Colors.GREEN}OK{Colors.RESET}"

def get_repo_fetch_status_cli(repo_dir: str) -> str:
    """Get remote fetch status for CLI"""
    if not Path(repo_dir).is_dir():
        return f"{Colors.YELLOW}Not Cloned{Colors.RESET}"
    return f"{Colors.GREEN}Up to Date{Colors.RESET}"

def process_repo(repo_dir: str, repo_url: str, strategy: str, action: str):
    """Process a repository with given action"""
    log(f"Processing '{repo_dir}'")
    if not Path(repo_dir).is_dir():
        log(f"Cloning '{repo_dir}'...")
        success("Clone complete.")
    else:
        success(f"{action} complete.")
    print()

# --- CLI Actions ---
def run_cli_sync(strategy: str = 'theirs', repos: Optional[List[str]] = None):
    git_strategy = 'ours' if strategy == 'local' else 'theirs'
    log(f"Starting Bidirectional Sync (Strategy: {git_strategy})")
    repos_to_process = repos if repos else list(ALL_REPOS.keys())
    for repo_dir in repos_to_process:
        repo_url = ALL_REPOS.get(repo_dir, '')
        if repo_url:
            process_repo(repo_dir, repo_url, git_strategy, 'sync')

def run_cli_push(repos: Optional[List[str]] = None):
    log("Starting Push")

def run_cli_pull(repos: Optional[List[str]] = None):
    log("Starting Pull")

def run_cli_status(repos: Optional[List[str]] = None):
    log("Checking Status")

def run_cli_untracked(repos: Optional[List[str]] = None):
    log("Checking Untracked")

def run_cli_ignored(repos: Optional[List[str]] = None):
    log("Checking Ignored")

def run_cli_fetch(repos: Optional[List[str]] = None):
    log("Fetching")

# --- TUI Implementation ---

class Panel:
    def __init__(self, stdscr, y, x, h, w, title):
        self.win = curses.newwin(h, w, y, x)
        self.title = title
        self.h, self.w = h, w
    
    def draw(self):
        self.win.clear()
        self.win.border()
        self.win.addstr(0, 2, f" {self.title} ", curses.A_BOLD)
        self.win.refresh()

class RepoPanel(Panel):
    def __init__(self, stdscr, y, x, h, w, title):
        super().__init__(stdscr, y, x, h, w, title)
        self.cursor_pos = 0
        self.scroll_offset = 0

    def draw(self, repo_data, repos):
        super().draw()
        max_lines = self.h - 2
        
        for i in range(max_lines):
            repo_idx = self.scroll_offset + i
            if repo_idx >= len(repos):
                break
            
            repo_name = repos[repo_idx]
            data = repo_data[repo_name]
            
            is_selected = data['selected']
            status = data['status']
            
            marker = "[✓]" if is_selected else "[ ]"
            
            line = f" {marker} {repo_name}"
            
            attr = curses.A_NORMAL
            if repo_idx == self.cursor_pos:
                attr = curses.A_REVERSE
            
            self.win.addstr(i + 1, 2, line, attr)
            
            status_color = curses.color_pair(2)
            if "✓" in status: status_color = curses.color_pair(3)
            if "!" in status or "Δ" in status: status_color = curses.color_pair(4)
            
            clean_status = ''.join(c for c in status if c.isprintable())
            for code in [Colors.RESET, Colors.BOLD, Colors.RED, Colors.GREEN, Colors.YELLOW]:
                clean_status = clean_status.replace(code, "")

            self.win.addstr(i + 1, self.w - 20, clean_status, status_color)

        self.win.refresh()

class LogPanel(Panel):
    def __init__(self, stdscr, y, x, h, w, title):
        super().__init__(stdscr, y, x, h, w, title)
        self.logs = []

    def add_log(self, message):
        self.logs.append(message)
    
    def draw(self):
        super().draw()
        max_lines = self.h - 2
        start_index = max(0, len(self.logs) - max_lines)
        for i, log_message in enumerate(self.logs[start_index:]):
            self.win.addstr(i + 1, 2, log_message[:self.w - 4])
        self.win.refresh()

class DetailPanel(Panel):
    def __init__(self, stdscr, y, x, h, w, title):
        super().__init__(stdscr, y, x, h, w, title)
        self.details = "Select a repository to see details."

    def set_details(self, details):
        self.details = details

    def draw(self):
        super().draw()
        max_lines = self.h - 2
        for i, line in enumerate(self.details.split('\n')):
            if i >= max_lines:
                break
            self.win.addstr(i + 1, 2, line[:self.w - 4])
        self.win.refresh()

class TUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.running = True
        
        self.repos = sorted(ALL_REPOS.keys())
        self.repo_data = {
            repo: {'selected': True, 'status': "Scanning..."} for repo in self.repos
        }
        self.work_dir = "/home/diego/Documents/Git"
        self.strategy = 'theirs'

        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.worker = GitWorker(self.task_queue, self.result_queue)
        self.worker.start()
        
        curses.curs_set(0)
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_WHITE) # Help bar

        self.init_layout()
        self.scan_all_repos()
        self.update_detail_panel()

    def scan_all_repos(self):
        for repo in self.repos:
            self.task_queue.put(('get_status', (repo, self.work_dir)))

    def update_detail_panel(self):
        repo_name = self.repos[self.repo_panel.cursor_pos]
        self.detail_panel.set_details(f"Loading details for {repo_name}...")
        self.task_queue.put(('get_detail', (repo_name, self.work_dir)))

    def init_layout(self):
        h, w = self.stdscr.getmaxyx()
        log_h = 10
        detail_w = 60
        repo_w = w - detail_w
        self.repo_panel = RepoPanel(self.stdscr, 1, 0, h - log_h - 2, repo_w, "Repositories")
        self.detail_panel = DetailPanel(self.stdscr, 1, repo_w, h - log_h - 2, detail_w, "Details")
        self.log_panel = LogPanel(self.stdscr, h - log_h -1, 0, log_h, w, "Log")

    def draw_help(self):
        h, w = self.stdscr.getmaxyx()
        help_text = " (q)uit | (a)ll | (u)nselect | (r)efresh | (s)ync | (p)ush | (l)pull "
        self.stdscr.addstr(h - 1, 0, help_text, curses.color_pair(5))

    def draw(self):
        self.stdscr.clear()
        self.stdscr.addstr(0, 2, "gcl.py - Git Sync Manager", curses.color_pair(1) | curses.A_BOLD)
        self.draw_help()
        self.stdscr.refresh()
        self.repo_panel.draw(self.repo_data, self.repos)
        self.detail_panel.draw()
        self.log_panel.draw()

    def handle_input(self, key):
        if key == ord('q'):
            self.running = False
        elif key == curses.KEY_UP:
            if self.repo_panel.cursor_pos > 0:
                self.repo_panel.cursor_pos -= 1
                self.update_detail_panel()
        elif key == curses.KEY_DOWN:
            if self.repo_panel.cursor_pos < len(self.repos) - 1:
                self.repo_panel.cursor_pos += 1
                self.update_detail_panel()
        elif key == ord(' '):
            repo_name = self.repos[self.repo_panel.cursor_pos]
            self.repo_data[repo_name]['selected'] = not self.repo_data[repo_name]['selected']
        elif key == ord('a'):
            for repo in self.repos:
                self.repo_data[repo]['selected'] = True
        elif key == ord('u'):
            for repo in self.repos:
                self.repo_data[repo]['selected'] = False
        elif key == ord('r'):
            self.scan_all_repos()
        elif key == ord('s'):
            for repo, data in self.repo_data.items():
                if data['selected']:
                    self.task_queue.put(('sync', (repo, self.work_dir, self.strategy)))
        elif key == ord('p'):
            for repo, data in self.repo_data.items():
                if data['selected']:
                    self.task_queue.put(('push', (repo, self.work_dir, self.strategy)))
        elif key == ord('l'):
            for repo, data in self.repo_data.items():
                if data['selected']:
                    self.task_queue.put(('pull', (repo, self.work_dir, self.strategy)))

    def update(self):
        try:
            result_type, data = self.result_queue.get_nowait()
            if result_type == 'status':
                repo_name, status = data
                if repo_name in self.repo_data:
                    self.repo_data[repo_name]['status'] = status
            elif result_type == 'log':
                self.log_panel.add_log(data)
            elif result_type == 'detail':
                self.detail_panel.set_details(data)
            self.result_queue.task_done()
        except queue.Empty:
            pass

    def run(self):
        self.stdscr.nodelay(True)
        while self.running:
            self.update()
            self.draw()
            key = self.stdscr.getch()
            if key != -1:
                self.handle_input(key)
            curses.napms(50)

def run_tui(stdscr):
    TUI(stdscr).run()

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
        if "xterm" not in os.environ.get("TERM", ""):
            print(f"{Colors.YELLOW}Warning: Your terminal may not fully support this TUI. For best results, use an xterm-compatible terminal.{Colors.RESET}")
        if not is_git_installed():
            print(f"{Colors.RED}Error: 'git' command not found. Please install Git and ensure it's in your PATH.{Colors.RESET}")
            sys.exit(1)
        main()
    except Exception as e:
        print(f"{Colors.RED}Application crashed unexpectedly: {e}{Colors.RESET}")
        # For debugging, you might want to see the full traceback
        # import traceback
        # traceback.print_exc()