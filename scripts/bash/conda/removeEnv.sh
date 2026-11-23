# setup the env for the project
# uses gitbash 

# assumes/needs 
# 1. gitbash
# 2. python 
# 3. miniconda 

# Resolve the repository from the script location, independent of the caller.
proj_home="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)" || exit 1
env_file_path="${proj_home}/dev_tools"
env_file=${env_file_path}"/environment.yml"

if [[ ! -f "$env_file" ]]; then
    printf 'Environment definition not found.\n' >&2
    exit 1
fi

# locate the env name for this env 
env_name=$(grep 'name:' "$env_file" | awk '{print $2}')

# conda remove and deactivate env
if conda info --envs | grep -q "$env_name"; then
    conda deactivate
    conda env remove -n "$env_name"
    conda clean --all
    echo "Environment '$env_name' has been removed."
else
    echo "Environment '$env_name' does not exist."
fi