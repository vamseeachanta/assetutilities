# shell script to perform daily git operations
repo_root=$(git rev-parse --show-toplevel)
# get to repo root
cd "$repo_root"

repo_name=$(basename $(git rev-parse --show-toplevel))
au_git_sync_home="dev_tools/au_git_sync"

# source common utilities
source ${au_git_sync_home}/common.sh

# Directory containing GitHub repositories
current_dir=$(pwd)
github_dir=$(dirname "$current_dir")
assetutilities_dir="${github_dir}/assetutilities"

# rel path top bash_tools dir, daily_commit_script
daily_commit_script_rel_path="${au_git_sync_home}/au_git_daily_commit.sh"

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
            daily_commit_script="${dir}/${daily_commit_script_rel_path}"
            log_message "green" "Daily routine ... START"
            if [ ! -f "$daily_commit_script" ]; then
                daily_commit_script="${assetutilities_dir}/${daily_commit_script_rel_path}"
            fi
            bash "$daily_commit_script"
            log_message "green" "Daily routine in $(basename "$dir") ... FINISH"


        else
            log_message "green" "No changes detected in $(basename "$dir") ..."
        fi

    fi
done

# Return to original directory
cd "$assetutilities_dir/$au_git_sync_home"
log_message "green" "Completed daily_routine for all repositories"
