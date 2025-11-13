#!/bin/sh

### Clone or pull with merge strategy
clone_or_pull() {
    _merge_strategy="$1"
    _repo="$2"
    _url="$3"

    if [ -d "$_repo" ]; then
        echo "Pulling $_repo (keeping $_merge_strategy version on conflicts)..."
        git -C "$_repo" pull -s recursive -X "$_merge_strategy"
    else
        echo "Cloning $_repo..."
        git clone "$_url" "$_repo"
    fi
}

main() {
    ### Choose your strategy
    _mode="$1"
    _strategy="$2"

    if [ "$_strategy" = "local" ]; then
        _merge_strategy="ours"
        echo "Using strategy: Keep local changes"
    else
        _merge_strategy="theirs"
        echo "Using strategy: Keep remote changes"
    fi

    if [ "$_mode" = "0" ]; then
        ### HTTPS URLs (Public repositories)
        clone_or_pull "$_merge_strategy" "profile" "https://github.com/diegonmarcos/diegonmarcos.git"
        clone_or_pull "$_merge_strategy" "back-Mylibs" "https://github.com/diegonmarcos/back-Mylibs.git"
        clone_or_pull "$_merge_strategy" "back-System" "https://github.com/diegonmarcos/back-System.git"
        clone_or_pull "$_merge_strategy" "back-Algo" "https://github.com/diegonmarcos/back-Algo.git"
        clone_or_pull "$_merge_strategy" "back-Graphic" "https://github.com/diegonmarcos/back-Graphic.git"
        clone_or_pull "$_merge_strategy" "website" "https://github.com/diegonmarcos/diegonmarcos.github.io.git"
        clone_or_pull "$_merge_strategy" "cyber-Cyberwarfare" "https://github.com/diegonmarcos/cyber-Cyberwarfare.git"
        clone_or_pull "$_merge_strategy" "ops-Tooling" "https://github.com/diegonmarcos/ops-Tooling.git"
        clone_or_pull "$_merge_strategy" "ml-MachineLearning" "https://github.com/diegonmarcos/ml-MachineLearning.git"
        clone_or_pull "$_merge_strategy" "ml-DataScience" "https://github.com/diegonmarcos/ml-DataScience.git"
        clone_or_pull "$_merge_strategy" "ml-Agentic" "https://github.com/diegonmarcos/ml-Agentic.git"

    elif [ "$_mode" = "1" ]; then
        ### SSH URLs (All repositories including private)
        clone_or_pull "$_merge_strategy" "profile" "git@github.com:diegonmarcos/diegonmarcos.git"
        clone_or_pull "$_merge_strategy" "back-Mylibs" "git@github.com:diegonmarcos/back-Mylibs.git"
        clone_or_pull "$_merge_strategy" "back-System" "git@github.com:diegonmarcos/back-System.git"
        clone_or_pull "$_merge_strategy" "back-Algo" "git@github.com:diegonmarcos/back-Algo.git"
        clone_or_pull "$_merge_strategy" "back-Graphic" "git@github.com:diegonmarcos/back-Graphic.git"
        clone_or_pull "$_merge_strategy" "website" "git@github.com:diegonmarcos/diegonmarcos.github.io.git"
        clone_or_pull "$_merge_strategy" "cyber-Cyberwarfare" "git@github.com:diegonmarcos/cyber-Cyberwarfare.git"
        clone_or_pull "$_merge_strategy" "ops-Tooling" "git@github.com:diegonmarcos/ops-Tooling.git"
        clone_or_pull "$_merge_strategy" "ml-MachineLearning" "git@github.com:diegonmarcos/ml-MachineLearning.git"
        clone_or_pull "$_merge_strategy" "ml-DataScience" "git@github.com:diegonmarcos/ml-DataScience.git"
        clone_or_pull "$_merge_strategy" "ml-Agentic" "git@github.com:diegonmarcos/ml-Agentic.git"
        clone_or_pull "$_merge_strategy" "front-Notes_md" "git@github.com:diegonmarcos/front-Notes_md.git"
        clone_or_pull "$_merge_strategy" "lecole42" "git@github.com:diegonmarcos/lecole42.git"
        clone_or_pull "$_merge_strategy" "dev" "git@github.com:diegonmarcos/dev.git"

    else
        echo "### USAGE"
        echo "  $0 [0 | 1] [local | remote]"
        echo ""
        echo "  Mode:"
        echo "    0: HTTPS - public repositories only"
        echo "    1: SSH   - all repositories (including private)"
        echo ""
        echo "  Strategy:"
        echo "    local  : Keep local changes on conflicts (merge -X ours)"
        echo "    remote : Keep remote changes on conflicts (merge -X theirs) [default]"
        echo ""
        echo "  Examples:"
        echo "    $0 0 remote  # Clone/pull public repos, prefer remote changes"
        echo "    $0 1 local   # Clone/pull all repos, prefer local changes"
    fi
}

main "$1" "$2"
