# shell script to perform daily git operations - all repos
au_git_sync_home=$(pwd)
au_daily_commit_script="${au_git_sync_home}/au_git_daily_commit.sh"

# source common utilities
if [ ! -f "${au_git_sync_home}/common.sh" ]; then
    source ${au_git_sync_home}/common.sh
fi

# Check if current directory is a git repository
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    # get to repo root
    repo_root=$(git rev-parse --show-toplevel)
    cd "$repo_root"
    repo_name=$(basename $(git rev-parse --show-toplevel))
    # Directory containing GitHub repositories
    github_dir=$(dirname "$(pwd)")
else
    cd ../../
    github_dir=$(dirname "$(pwd)")
    log_message "yellow" "$(pwd) is not a git repository. Define a valid directory to run this script."
    exit 1
fi

cd ${github_dir}
log_message "normal" "Starting repository check-in routine process in $(pwd)..."

# Iterate through all directories in the GitHub folder
for dir in "$github_dir"/*/ ; do
    if [ -d "$dir" ]; then

        log_message "normal" "Processing repo: $(basename "$dir")"
        cd "$dir"

        # Check if there are any changes
        if [ -n "$(git status --porcelain)" ]; then
            log_message "yellow" "Changes detected in repo: $(basename "$dir")"

            # commit changes
            daily_commit_script="${dir}/dev_tools/au_git_sync/au_git_daily_commit.sh"
            log_message "green" "Daily routine ... START"
            if [ ! -f "$daily_commit_script" ]; then
                daily_commit_script="${au_daily_commit_script}"
            fi
            bash "$daily_commit_script"
            log_message "green" "Daily routine in $(basename "$dir") ... FINISH"

        else
            log_message "green" "No changes detected in $(basename "$dir") ..."
        fi

    fi
done

# Return to original directory
cd "$au_git_sync_home"
log_message "green" "Completed daily_routine for all repositories"
