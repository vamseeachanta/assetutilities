#! /bin/bash
# common shell script utils 

# - [ ] #todo #13_siva_AceEngineer #ae_au have to use this all over the place

# Define ANSI color codes as static variables
readonly RED="\033[31m"
readonly GREEN="\033[32m"
readonly YELLOW="\033[33m"
readonly NORMAL="\033[37m"  # Normal/White Color
readonly RESET="\033[0m"

# Print a message with timestamp
log_message() {
    local color=$1
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    local msg=${timestamp}" | ${0} | "$2

    case $color in
        "red") echo -e "${RED}$msg${RESET}" ;;
        "green") echo -e "${GREEN}$msg${RESET}" ;;
        "yellow") echo -e "${YELLOW}$msg${RESET}" ;;
        "normal") echo -e "${NC}$msg${RESET}" ;;
        *) echo "[${timestamp}] ${msg}"
    esac
}


pause_for_user() {
    read -n 1 -s -r -p "Pausing - press any key to continue... "
    echo -e "\n"
}

go2ProjectRoot() {
    project_root=$(git rev-parse --show-toplevel)
    log_message "normal" "inside common.sh: project_root: $project_root"
    cd "$project_root"
}

# use following if any script wants to go to project home
# go2ProjectHome