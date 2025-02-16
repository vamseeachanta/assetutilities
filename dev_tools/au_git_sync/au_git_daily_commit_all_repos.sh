# shell script to perform daily git operations - all repos
au_git_sync_home=$(pwd)
au_daily_commit_script="${au_git_sync_home}/au_git_daily_commit.sh"

# source common utilities
if [ ! -f "${au_git_sync_home}/common.sh" ]; then
    source ${au_git_sync_home}/common.sh
fi

# Check if current directory is in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    cd ../../
    github_dir=$(dirname "$(pwd)")
    log_message "yellow" "$(pwd) is not a git repository. Define a valid directory to run this script."
else
    # get to repo root
    repo_root=$(git rev-parse --show-toplevel)
    cd "$repo_root"
    # Directory containing GitHub repositories
    github_dir=$(dirname "$(pwd)")
fi

cd ${github_dir}
log_message "normal" "Starting repository check-in routine process in $(pwd)..."

# Iterate through all directories in the GitHub folder
for dir in "$github_dir"/*/ ; do
    if [ -d "$dir" ]; then

        cd "$dir"

        if [ ! -f "$daily_commit_script" ]; then
            daily_commit_script="${au_daily_commit_script}"
        fi
        bash "$daily_commit_script"

    fi
done

# Return to original directory
cd "$au_git_sync_home"
log_message "green" "Completed daily_routine for all repositories"
