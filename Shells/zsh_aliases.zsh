#!/bin/zsh
# Zsh Aliases Configuration
# Source this file in your ~/.zshrc: source /path/to/zsh_aliases.zsh

# ============================================================================
# Python Aliases
# ============================================================================
alias py='python3'
alias python='python3'
alias pip='pip3'

# ============================================================================
# Directory Navigation
# ============================================================================
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias .....='cd ../../../..'

# Quick directory navigation with pushd/popd
alias d='dirs -v | head -10'
alias 1='cd -'
alias 2='cd -2'
alias 3='cd -3'
alias 4='cd -4'
alias 5='cd -5'

# ============================================================================
# List Directory Contents
# ============================================================================
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias ls='ls --color=auto'
alias lh='ls -lh'
alias lt='ls -ltr'  # Sort by modification time

# ============================================================================
# Git Aliases
# ============================================================================
alias gs='git status'
alias ga='git add'
alias gaa='git add --all'
alias gc='git commit'
alias gcm='git commit -m'
alias gp='git push'
alias gl='git log --oneline --graph --decorate'
alias gla='git log --oneline --graph --decorate --all'
alias gd='git diff'
alias gds='git diff --staged'
alias gco='git checkout'
alias gb='git branch'
alias gba='git branch -a'
alias gpl='git pull'
alias gcl='git clone'
alias gst='git stash'
alias gstp='git stash pop'

# ============================================================================
# Grep with Colors
# ============================================================================
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'

# ============================================================================
# Safety Aliases (prompt before overwrite/delete)
# ============================================================================
alias cp='cp -i'
alias mv='mv -i'
alias rm='rm -i'

# ============================================================================
# System Information
# ============================================================================
alias df='df -h'
alias du='du -h'
alias duh='du -h --max-depth=1 | sort -h'
alias free='free -h'
alias psg='ps aux | grep -v grep | grep -i -e VSZ -e'
alias mem='free -h && sync && echo 3 | sudo tee /proc/sys/vm/drop_caches && free -h'

# ============================================================================
# Networking
# ============================================================================
alias ports='netstat -tulanp'
alias myip='curl -s ifconfig.me'
alias localip='ip addr show | grep "inet " | grep -v 127.0.0.1 | awk "{print \$2}"'
alias ping='ping -c 5'
alias fastping='ping -c 100 -s.2'

# ============================================================================
# Misc Utilities
# ============================================================================
alias c='clear'
alias h='history'
alias hg='history | grep'
alias path='echo -e ${PATH//:/\\n}'
alias reload='source ~/.zshrc'
alias week='date +%V'
alias timer='echo "Timer started. Stop with Ctrl-D." && date && time cat && date'

# ============================================================================
# Quick Edit Config Files
# ============================================================================
alias editzsh='${EDITOR:-nano} ~/.zshrc'
alias sourcezsh='source ~/.zshrc'

# ============================================================================
# Development Shortcuts
# ============================================================================
alias serve='python3 -m http.server'
alias jn='jupyter notebook'
alias dcu='docker-compose up'
alias dcd='docker-compose down'
alias dps='docker ps'
alias dpsa='docker ps -a'

# ============================================================================
# Functions
# ============================================================================

# Create directory and cd into it
mkcd() {
    mkdir -p "$1" && cd "$1"
}

# Extract any archive
extract() {
    if [ -f "$1" ]; then
        case "$1" in
            *.tar.bz2)   tar xjf "$1"     ;;
            *.tar.gz)    tar xzf "$1"     ;;
            *.bz2)       bunzip2 "$1"     ;;
            *.rar)       unrar x "$1"     ;;
            *.gz)        gunzip "$1"      ;;
            *.tar)       tar xf "$1"      ;;
            *.tbz2)      tar xjf "$1"     ;;
            *.tgz)       tar xzf "$1"     ;;
            *.zip)       unzip "$1"       ;;
            *.Z)         uncompress "$1"  ;;
            *.7z)        7z x "$1"        ;;
            *.deb)       ar x "$1"        ;;
            *.tar.xz)    tar xf "$1"      ;;
            *.tar.zst)   unzstd "$1"      ;;
            *)           echo "'$1' cannot be extracted via extract()" ;;
        esac
    else
        echo "'$1' is not a valid file"
    fi
}

# Quick find
qfind() {
    find . -name "*$1*"
}

# Backup file with timestamp
backup() {
    if [ -f "$1" ]; then
        cp "$1" "$1.backup.$(date +%Y%m%d_%H%M%S)"
        echo "Backup created: $1.backup.$(date +%Y%m%d_%H%M%S)"
    else
        echo "File not found: $1"
    fi
}

# Create a new directory and enter it
mkd() {
    mkdir -p "$@" && cd "$_"
}

# Get current git branch
git_current_branch() {
    git branch 2>/dev/null | sed -n '/\* /s///p'
}

# Quick git commit with message
gcam() {
    git add --all && git commit -m "$1"
}

# Quick git push to current branch
gpsh() {
    git push origin $(git_current_branch)
}

echo "Zsh aliases loaded successfully!"
