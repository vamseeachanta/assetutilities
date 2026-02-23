#!/bin/bash
# Bash completion for slash commands
# Source this file: source slash_completion.bash
# Or add to .bashrc/.zshrc

_slash_completions() {
    local cur prev commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Get list of available commands
    if [ "$COMP_CWORD" -eq 1 ]; then
        # Main commands
        commands="git-trunk-flow git-trunk-flow-enhanced git-sync search-commands 
                  modernize-deps organize-structure propagate-commands sync-all-commands
                  test-automation test-automation-enhanced install-ecosystem-awareness
                  --list --search --help"
        
        # Filter based on current input
        COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
    elif [ "$prev" == "--search" ] || [ "$prev" == "search-commands" ]; then
        # Suggest search categories
        categories="git testing dependencies organization distribution hooks multi-repo"
        COMPREPLY=( $(compgen -W "${categories}" -- ${cur}) )
    else
        # Command-specific options
        case "${COMP_WORDS[1]}" in
            git-trunk-flow*)
                COMPREPLY=( $(compgen -W "--help --dry-run --no-tests --force" -- ${cur}) )
                ;;
            search-commands)
                COMPREPLY=( $(compgen -W "--detailed --hooks --multi-repo --tags --repo --help-for --categories --export" -- ${cur}) )
                ;;
            propagate-commands)
                COMPREPLY=( $(compgen -W "--dry-run --target-dir --commands --help" -- ${cur}) )
                ;;
            sync-all-commands)
                COMPREPLY=( $(compgen -W "--dry-run --force --help" -- ${cur}) )
                ;;
            *)
                COMPREPLY=( $(compgen -W "--help" -- ${cur}) )
                ;;
        esac
    fi
    
    return 0
}

# Register completion for 'slash' command
complete -F _slash_completions slash

# Also register for direct path if needed
complete -F _slash_completions ./slash
complete -F _slash_completions /mnt/github/github/assetutilities/slash

echo "✅ Bash completion for 'slash' command loaded!"
echo "   Usage: slash <TAB><TAB> to see available commands"