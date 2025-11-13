#!/usr/bin/env fish
# Fish Shell Aliases Configuration
# Source this file in your ~/.config/fish/config.fish: source /path/to/fish_aliases.fish

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

# ============================================================================
# List Directory Contents
# ============================================================================
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias lh='ls -lh'
alias lt='ls -ltr'

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
alias free='free -h'

# ============================================================================
# Networking
# ============================================================================
alias ports='netstat -tulanp'
alias myip='curl -s ifconfig.me'
alias ping='ping -c 5'

# ============================================================================
# Misc Utilities
# ============================================================================
alias c='clear'
alias h='history'
alias reload='source ~/.config/fish/config.fish'

# ============================================================================
# Quick Edit Config Files
# ============================================================================
alias editfish='$EDITOR ~/.config/fish/config.fish'
alias sourcefish='source ~/.config/fish/config.fish'

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
function mkcd
    mkdir -p $argv[1]; and cd $argv[1]
end

# Extract any archive
function extract
    if test -f $argv[1]
        switch $argv[1]
            case '*.tar.bz2'
                tar xjf $argv[1]
            case '*.tar.gz'
                tar xzf $argv[1]
            case '*.bz2'
                bunzip2 $argv[1]
            case '*.rar'
                unrar x $argv[1]
            case '*.gz'
                gunzip $argv[1]
            case '*.tar'
                tar xf $argv[1]
            case '*.tbz2'
                tar xjf $argv[1]
            case '*.tgz'
                tar xzf $argv[1]
            case '*.zip'
                unzip $argv[1]
            case '*.Z'
                uncompress $argv[1]
            case '*.7z'
                7z x $argv[1]
            case '*.deb'
                ar x $argv[1]
            case '*.tar.xz'
                tar xf $argv[1]
            case '*.tar.zst'
                unzstd $argv[1]
            case '*'
                echo "'$argv[1]' cannot be extracted via extract()"
        end
    else
        echo "'$argv[1]' is not a valid file"
    end
end

# Quick find
function qfind
    find . -name "*$argv[1]*"
end

# Backup file with timestamp
function backup
    if test -f $argv[1]
        set timestamp (date +%Y%m%d_%H%M%S)
        cp $argv[1] "$argv[1].backup.$timestamp"
        echo "Backup created: $argv[1].backup.$timestamp"
    else
        echo "File not found: $argv[1]"
    end
end

# Create a new directory and enter it
function mkd
    mkdir -p $argv; and cd $argv[-1]
end

# Get current git branch
function git_current_branch
    git branch 2>/dev/null | sed -n '/\* /s///p'
end

# Quick git commit with message
function gcam
    git add --all; and git commit -m $argv[1]
end

# Quick git push to current branch
function gpsh
    git push origin (git_current_branch)
end

# Print path with newlines
function path
    echo $PATH | tr ' ' '\n'
end

echo "Fish aliases loaded successfully!"
