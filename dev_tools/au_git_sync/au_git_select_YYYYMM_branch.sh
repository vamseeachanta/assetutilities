# shell script to select YYYYMM branch in a repository
au_git_sync_home=$(pwd)

# source common utilities
if [ ! -f "${au_git_sync_home}/common.sh" ]; then
    source ${au_git_sync_home}/common.sh
fi

# get to repo root
repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"
repo_name=$(basename $(git rev-parse --show-toplevel))

year_month=$(date '+%Y%m')
year_month_branch_name=$year_month

# Check current branch matches year_month_branch_name
current_branch=$(git branch --show-current)

git fetch
if git ls-remote --heads origin $year_month_branch_name | grep -q $year_month_branch_name; then
  # if branch exists at origin, checkout 
  c "Branch $year_month_branch_name exists"
  git checkout -b $year_month_branch_name origin/$year_month_branch_name
  log_message "green" "Repo : ${repo_name} : Checked out branch $year_month_branch_name exists at origin"
else
  # create new year_month_branch_name, checkout and push to origin
  log_message "green" "Creating new branch $year_month_branch_name"
  git checkout -b $year_month_branch_name
  git push -u origin $year_month_branch_name
  log_message "green" "Repo : ${repo_name} : Created new branch $year_month_branch_name and pushed to origin"
fi

exit 0
