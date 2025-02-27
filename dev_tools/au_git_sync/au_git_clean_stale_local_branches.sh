# shell script to perform daily git commit in a repository
repo_git_sync_home=$(pwd)

# source common utilities
if [ -f "${repo_git_sync_home}/common.sh" ]; then
    source ${repo_git_sync_home}/common.sh
else
    source $1/common.sh
fi

# Function to determine if using 'main' or 'master' as the default branch
get_main_branch() {
    if git rev-parse --verify origin/main >/dev/null 2>&1; then
        echo "main"
    else
        echo "master"
    fi
}

# Get the default branch name
MAIN_BRANCH=$(get_main_branch)

# Fetch latest changes from remote
git fetch origin
# Update the default branch
git pull origin "$MAIN_BRANCH"

# Store the current branch
CURRENT_BRANCH=$(git branch --show-current)

# Get all local branches except the default branch
branches=()
eval "$(git for-each-ref --shell --format='branches+=(%(refname:short))' refs/heads/)"

# Process each local branch
for branch in "${branches[@]}"; do
    # Skip the default branch and the current working branch
    if [[ "$branch" != "$MAIN_BRANCH" && "$branch" != "$CURRENT_BRANCH" ]]; then
        # Checkout the branch
        if git checkout "$branch"; then
            log_message "yellow" "Processing branch: $branch"
            # Merge default branch into current branch
            if git merge "$MAIN_BRANCH"; then
                # Push to origin
                if git push origin "$branch"; then
                    # Create pull request using GitHub CLI if installed
                    if command -v gh &> /dev/null; then
                        gh pr create --base "$MAIN_BRANCH" --head "$branch" --title "Merge $branch into $MAIN_BRANCH" --body "Automated PR created by maintenance script"
                    else
                        log_message "yellow" "GitHub CLI not installed. Skipping PR creation for $branch"
                    fi

                    # Switch to the default branch before deleting
                    git checkout "$MAIN_BRANCH"
                    # Delete the stale branch locally
                    git branch -D "$branch"
                    log_message "green" "Cleaned stale local branch: $branch"
                else
                    log_message "yellow" "Failed to push $branch to origin"
                fi
            else
                log_message "yellow" "Failed to merge $MAIN_BRANCH into $branch"
            fi
        else
            log_message "yellow" "Failed to checkout $branch"
        fi
    else
        # Improved message for non-stale branches
        if [[ "$branch" == "$MAIN_BRANCH" ]]; then
            log_message "green" "Branch '$branch' is the default branch. It is not considered stale."
        elif [[ "$branch" == "$CURRENT_BRANCH" ]]; then
            log_message "yellow" "Branch '$branch' is the currently active branch. It is not considered stale."
        else
            log_message "yellow" "Branch '$branch' is not stale. No cleanup required."
        fi
    fi
done

# Return to the original branch
git checkout "$CURRENT_BRANCH"

cd "$au_git_sync_home"
log_message "green" "Branch maintenance complete!"
