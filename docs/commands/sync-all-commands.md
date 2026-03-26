# Sync All Commands - Bidirectional Command Synchronization

## Overview

The `/sync-all-commands` script provides bidirectional synchronization of slash commands between the master repository (assetutilities) and all other repositories in your workspace. It can:

- **Collect** new commands from any repository
- **Detect** modifications to existing commands
- **Resolve** conflicts when multiple versions exist
- **Sync** changes back to the master repository
- **Distribute** updates to all repositories

## Features

### 🔍 Command Discovery
- Scans all repositories in parallel for slash commands
- Identifies commands in `.agent-os/commands/` directories
- Extracts metadata (version, author, description, hash)
- Creates comprehensive inventory of all commands

### 🆕 New Command Detection
- Finds commands that exist in other repos but not in master
- Automatically imports new commands to master
- Handles naming conflicts intelligently

### 🔧 Modification Tracking
- Detects when commands have been modified in other repos
- Compares file hashes to identify changes
- Shows diffs between versions
- Preserves modification history

### ⚠️ Conflict Resolution
- Handles multiple versions of the same command
- Auto-selects newest version by default
- Provides detailed comparison information
- Backs up existing versions before updates

### 📊 Reporting
- Generates detailed JSON reports
- Tracks all synchronization activities
- Maintains audit trail of changes
- Provides statistics and summaries

## Usage

### Basic Synchronization

```bash
# From assetutilities directory
cd /mnt/github/github/assetutilities
python .agent-os/commands/sync_all_commands.py
```

### Command Options

```bash
# Dry run - see what would be synced without making changes
python .agent-os/commands/sync_all_commands.py --dry-run

# Force updates without prompting
python .agent-os/commands/sync_all_commands.py --force

# Sync and then distribute updates to all repos
python .agent-os/commands/sync_all_commands.py --distribute

# Generate report only
python .agent-os/commands/sync_all_commands.py --report-only

# Specify custom workspace
python .agent-os/commands/sync_all_commands.py --workspace /path/to/repos

# Specify different master repository
python .agent-os/commands/sync_all_commands.py --master-repo /path/to/master
```

## Workflow Examples

### Example 1: Collect New Commands

Someone created a new `/data-migration` command in the `aceengineer-admin` repo:

```bash
# Run sync to collect it
cd /mnt/github/github/assetutilities
python .agent-os/commands/sync_all_commands.py

# Output:
🔍 Scanning all repositories for slash commands...
  📦 aceengineer-admin: 6 commands found
  📦 aceengineer-website: 5 commands found
  ...

🆕 Found 1 new command:
  • /data-migration (in aceengineer-admin)

📥 Syncing new commands to master...
  ✅ Synced new command: /data-migration from aceengineer-admin
```

### Example 2: Update Modified Commands

Someone improved the `/git-trunk-flow` command in another repo:

```bash
# Run sync to detect and update
python .agent-os/commands/sync_all_commands.py

# Output:
🔧 Found 1 modified command:
  • /git-trunk-flow (modified in aceengineer-website)

⚠️  Update modified commands in master? (y/n): y

📤 Updating modified commands in master...
  📋 Backed up: git_trunk_flow.py
  📝 Changes for /git-trunk-flow:
    + Added new feature for automatic PR labeling
    - Removed deprecated function
  ✅ Updated command: /git-trunk-flow from aceengineer-website
```

### Example 3: Full Synchronization Cycle

Collect, sync, and redistribute all commands:

```bash
# Complete synchronization with distribution
python .agent-os/commands/sync_all_commands.py --distribute

# This will:
# 1. Scan all repositories
# 2. Collect new commands
# 3. Update modified commands
# 4. Generate sync report
# 5. Distribute all updates back to all repos
```

## How It Works

### 1. Discovery Phase
```python
# The script scans all repositories in parallel
repos = discover_all_repositories()
for repo in repos:
    commands = scan_repository_commands(repo)
    # Extracts: name, hash, metadata, description
```

### 2. Analysis Phase
```python
# Identifies new and modified commands
new_commands = identify_new_commands()
modified_commands = identify_modified_commands()
```

### 3. Conflict Resolution
```python
# When multiple versions exist
if len(instances) > 1:
    # Auto-selects newest version
    # Shows comparison to user
    selected = resolve_conflict(cmd_name, instances)
```

### 4. Synchronization
```python
# Backs up existing files
backup_command(existing_file)
# Copies selected version to master
sync_command(selected_version)
```

### 5. Distribution (Optional)
```python
# Uses propagate_commands to distribute
distribute_updates()  # Sends to all repos
```

## Directory Structure

```
assetutilities/
├── .agent-os/
│   └── commands/
│       ├── sync_all_commands.py      # This sync script
│       ├── git_trunk_flow.py         # Commands collected
│       ├── data_migration.py         # from various repos
│       └── ...
├── .command-backups/                 # Automatic backups
│   └── 20240812_142530/
│       └── git_trunk_flow.py         # Backed up versions
└── .sync-reports/                    # Sync reports
    └── sync_report_20240812_142530.json
```

## Sync Report Format

The JSON sync report contains:

```json
{
  "timestamp": "2024-08-12T14:25:30",
  "workspace": "/mnt/github/github",
  "master_repo": "/mnt/github/github/assetutilities",
  "statistics": {
    "total_repositories": 25,
    "total_commands": 8,
    "new_commands": 2,
    "modified_commands": 1,
    "conflicts": 0
  },
  "new_commands": {
    "/data-migration": {
      "found_in": ["aceengineer-admin"],
      "selected_from": "aceengineer-admin"
    }
  },
  "modified_commands": {
    "/git-trunk-flow": {
      "modified_in": ["aceengineer-website", "energy"],
      "versions": 2
    }
  },
  "all_commands": {
    "/git-trunk-flow": {
      "repositories": ["assetutilities", "aceengineer-admin", ...],
      "versions": 1
    }
  }
}
```

## Backup and Recovery

### Automatic Backups
- Created before any file is modified
- Stored in `.command-backups/` with timestamp
- Preserves file permissions and metadata

### Manual Recovery
```bash
# Restore from backup
cp .command-backups/20240812_142530/git_trunk_flow.py \
   .agent-os/commands/git_trunk_flow.py
```

## Best Practices

### 1. Regular Synchronization
Run sync weekly or after creating new commands:
```bash
# Weekly sync
python .agent-os/commands/sync_all_commands.py --report-only
```

### 2. Review Before Syncing
Always use `--dry-run` first:
```bash
python .agent-os/commands/sync_all_commands.py --dry-run
```

### 3. Distribute After Major Updates
After syncing important changes:
```bash
python .agent-os/commands/sync_all_commands.py --distribute
```

### 4. Check Reports
Review sync reports for insights:
```bash
cat .sync-reports/sync_report_*.json | jq '.statistics'
```

## Conflict Resolution Strategy

When multiple versions of a command exist:

1. **Automatic Selection**: Newest version (by modification time)
2. **Hash Comparison**: Identifies truly different versions
3. **Diff Display**: Shows changes between versions
4. **Backup Creation**: Preserves existing version
5. **Manual Override**: User can intervene if needed

## Performance

- **Parallel Scanning**: Uses 10 worker threads
- **Efficient Hashing**: SHA256 for quick comparison
- **Lazy Loading**: Only reads files when needed
- **Batch Operations**: Processes multiple files together

## Troubleshooting

### "No commands found"
- Check that repositories have `.agent-os/commands/` directories
- Ensure Python files are named correctly (use underscores)
- Verify file permissions

### "Permission denied"
- Ensure write access to master repository
- Check file ownership in target directories

### "Conflict detected"
- Review the versions shown
- Check modification times
- Use `--force` to auto-resolve

### "Distribution failed"
- Ensure `propagate_commands.py` exists
- Check network/file system access
- Verify all repositories are accessible

## Integration with Other Commands

Works seamlessly with:
- `/propagate-commands` - For distribution
- `/git-trunk-flow` - For committing synced changes
- `/organize-structure` - For cleanup after sync

## Command Registration

After syncing, register the command:

```bash
# Update slash_commands.py to include new command
./slash_commands.py --list  # Verify it appears
```

## Security Considerations

- **No Code Execution**: Only copies files, doesn't run them
- **Hash Verification**: Ensures file integrity
- **Backup Protection**: Always backs up before changes
- **Audit Trail**: Complete history in sync reports

## Future Enhancements

Planned improvements:
- Interactive conflict resolution UI
- Dependency tracking between commands
- Version tagging and rollback
- Command testing before sync
- Git integration for automatic commits

---

*Keeping your slash commands synchronized across all repositories* 🔄