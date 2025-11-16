# gcl.py - Python Version

## Overview

This is a Python port of the `gcl.sh` shell script. It provides the same git management functionality with CLI commands.

## Status

✅ **CLI Mode**: Fully functional
✅ **TUI Mode**: Fully functional

## Requirements

- Python 3.6+
- Git installed
- Same repository access as shell version

## Installation

No installation needed. The script is standalone.

```bash
chmod +x gcl.py
```

## Usage

### TUI Mode (Interactive)

```bash
# Launch interactive TUI
python3 gcl.py

# Or make it executable
chmod +x gcl.py
./gcl.py
```

**TUI Keyboard Shortcuts:**
- `[w]` - Toggle working directory (current vs custom)
- `[s]` - Sync all repos (bidirectional)
- `[p]` - Push all repos
- `[l]` - Pull all repos
- `[u]` - List untracked files
- `[y]` - Restore symlinks
- `[t]` - Refresh status only (fast)
- `[f]` - Refresh fetch status (checks remote)
- `[r]` - Refresh both status and fetch
- `[q]` - Quit

### CLI Mode (Command Line)

```bash
# Show help
python3 gcl.py --help

# Check status of all repos
python3 gcl.py status

# Sync all repos (remote strategy)
python3 gcl.py sync

# Sync all repos (local strategy)
python3 gcl.py sync local

# Push all repos
python3 gcl.py push

# Pull all repos
python3 gcl.py pull

# List untracked files
python3 gcl.py untracked

# Restore symlinks
python3 gcl.py symlinks
python3 gcl.py symlinks /path/to/repo
```

## Features

### ✅ Implemented

1. **CLI Commands**
   - `sync [local|remote]` - Bidirectional sync with strategy
   - `push` - Push committed changes
   - `pull` - Pull with remote strategy
   - `status` - Check git status
   - `untracked` - List all untracked files
   - `symlinks [path]` - Restore 0.spec symlinks

2. **TUI Features**
   - Interactive terminal UI with curses
   - Three-column display (repos, local status, remote status)
   - Working directory selection (current vs custom path)
   - Keyboard shortcuts for all actions
   - Real-time status refresh (t/f/r keys)
   - Color-coded status indicators

3. **Git Operations**
   - Auto-commit before pull
   - Merge conflict resolution with strategy
   - Long path detection and auto-fix
   - Symlink detection and auto-fix
   - Failed merge abort

4. **Error Handling**
   - Filesystem limitations (long paths, symlinks)
   - Detailed error messages
   - Auto-configuration for git issues

## Why Python Version?

### Advantages

1. **Better Error Handling**
   - Structured exception handling
   - Type hints for clarity
   - Easier to debug

2. **Portability**
   - Works on Windows (with git bash)
   - More consistent across platforms
   - Standard library usage

3. **Extensibility**
   - Easier to add features
   - Can use Python libraries (GitPython, Rich, etc.)
   - Better code organization

4. **Testing**
   - Easier to write unit tests
   - Better integration with CI/CD
   - More maintainable

### When to Use Shell vs Python

**Use Shell Version (`gcl.sh`):**
- ✅ You prefer pure shell scripting
- ✅ You don't have Python installed
- ✅ You're on a minimal system

**Use Python Version (`gcl.py`):**
- ✅ You want both TUI and CLI functionality
- ✅ You want to integrate into Python scripts
- ✅ You're automating with cron/systemd
- ✅ You want better error messages and structure
- ✅ You prefer Python over shell scripting
- ✅ You want easier extensibility

## Examples

### Check Status

```bash
python3 gcl.py status
```

Output:
```
==> Checking Git Status for Repositories
==> Checking 'front-Github_profile'
  ✓ Working tree clean
  ✓ All commits pushed

==> Checking 'front-Github_io'
  ⚠ Has uncommitted changes (staged or unstaged)
  Files changed:
    M index.html
    ?? new-file.txt
```

### Sync with Error Handling

```bash
python3 gcl.py sync
```

If there's a long path error:
```
==> Processing 'front-Notes_md'
  Found uncommitted changes, committing before pull...
  ✓ Changes committed.
  Pulling with strategy: theirs
  ✗ Pull failed.
  ⚠ Filesystem limitation: Path/filename exceeds system limits.
  ⚠ Attempting automatic fix...
  ✓ Enabled core.longpaths for this repo.
  ⚠ Please re-run sync/pull for this repo.
```

### Restore Symlinks

```bash
python3 gcl.py symlinks /home/diego/Documents/Git/front-Notes_md
```

## Differences from Shell Version

### Similarities

Both versions now have:
- ✅ Full TUI interface with curses
- ✅ Same color codes and message format
- ✅ Same error detection and auto-fix
- ✅ Same keyboard shortcuts
- ✅ Same three-column status display
- ✅ Working directory selection
- ✅ All CLI commands

### Python Advantages

Python version offers:
- Better code organization with classes
- Type hints for clarity
- Structured exception handling
- Easier to extend and maintain
- Better integration with Python tools

### Future Plans

- [ ] Add progress bars for operations (using `rich` library)
- [ ] Add parallel repository processing
- [ ] Add configuration file support (.gcl.yaml)
- [ ] Add repo selection by tags
- [ ] Add custom repo groups
- [ ] Add unit tests
- [ ] Optional: Enhanced TUI with `rich` library

## Integration

### TUI Screenshot

When you run `python3 gcl.py` without arguments, you'll see:

```
╔═════════════════════════════╗
║ gcl.py - Git Sync Manager   ║
╚═════════════════════════════╝

Working Directory:
  [ ] Current: /home/diego/Documents/Git
  [✓] Custom:  /home/diego/Documents/Git

Repository                     Local Status    Remote Status
───────────────────────────────────────────────────────────────────────────
front-Github_profile          OK              Up to Date
front-Github_io               Uncommitted     Not Checked
back-System                   OK              Up to Date
...

Actions:
  [s] Sync (bidirectional)
  [p] Push
  [l] Pull
  [u] Untracked files
  [y] Restore symlinks

  [t] Refresh status only
  [f] Refresh fetch only
  [r] Refresh both

  [w] Toggle working dir
  [q] Quit
```

### With Shell Script

You can use both versions interchangeably:

```bash
# Use Python TUI for interactive work
python3 gcl.py

# Use Python CLI for automation
python3 gcl.py status > status.log

# Or use shell version if you prefer
./gcl.sh
```

### With Cron

```cron
# Daily sync at 3 AM
0 3 * * * cd /home/diego/Documents/Git && python3 gcl.py sync >> /var/log/gcl-sync.log 2>&1
```

### With Python Scripts

```python
import subprocess

# Run sync
result = subprocess.run(['python3', 'gcl.py', 'sync'],
                       capture_output=True, text=True)
print(result.stdout)
```

## Troubleshooting

### Import Errors

If you get import errors, make sure Python 3.6+ is installed:
```bash
python3 --version
```

### Permission Denied

Make sure script is executable:
```bash
chmod +x gcl.py
```

### Git Not Found

Make sure git is in PATH:
```bash
which git
git --version
```

## Contributing

The Python version is still evolving. If you want to help:

1. Implement TUI with `rich` or `curses`
2. Add unit tests
3. Improve error handling
4. Add configuration file support

## License

Same as shell version - use freely!
