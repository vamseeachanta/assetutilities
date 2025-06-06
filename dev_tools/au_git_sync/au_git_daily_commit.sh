# shell script to perform daily git commit in a repository
repo_git_sync_home=$(pwd)

# source common utilities
if [ -f "${repo_git_sync_home}/common.sh" ]; then
    source ${repo_git_sync_home}/common.sh
else
    source $1/common.sh
fi

# get to repo root
repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"
repo_name=$(basename $(git rev-parse --show-toplevel))

daily_commit_message=$(date '+%Y%m%d')

cat << COM
Starting daily git routine. key details 
  - Repository name: $repo_name
  - Repository root: $repo_root
  - Daily Commit message: $daily_commit_message
Executing git operations now 
COM

if [ -n "$(git status --porcelain)" ]; then
    log_message "yellow" "Daily commit routine in $(basename "$dir") ... START"
    log_message "green" "Changes detected in repo: $(basename "$dir")"

    # get to repo root
    cd "$repo_root"

    # perform git operations
    git pull
    git add --all
    git commit -m "$daily_commit_message"
    git push
    log_message "green" "Daily commit routine in $(basename "$dir") ... FINISH"
else
    log_message "yellow" "No changes detected in $(basename "$dir") ..."
fi

cd "$repo_git_sync_home"
