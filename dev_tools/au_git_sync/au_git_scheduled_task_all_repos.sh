au_git_sync_home=$(pwd)

# rel path top bash_tools dir, daily_commit_script
daily_commit_script="${au_git_sync_home}/au_git_daily_commit_all_repos.sh"
select_year_month_branch="${au_git_sync_home}/au_git_select_YYYYMM_branch_all_repos.sh"
clean_stale_branches="${au_git_sync_home}/au_git_clean_stale_local_branches_all_repos.sh"

bash "${daily_commit_script}"
bash "${select_year_month_branch}"
bash "${clean_stale_branches}"
