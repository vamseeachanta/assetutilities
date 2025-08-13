# CLAUDE.md Ecosystem Section Template

Add this section to all CLAUDE.md files across repositories:

---

## 🚀 MANDATORY: Slash Command Ecosystem Integration

**CRITICAL DIRECTIVE**: For EVERY improvement, automation, or repetitive task:

### AI Agents MUST:
1. **EVALUATE** if the improvement could benefit multiple repositories
2. **SUGGEST** creating a slash command when applicable  
3. **DESIGN** for reusability across all 25 repos
4. **INTEGRATE** with existing ecosystem via `/sync-all-commands`

### Immediate Triggers for Command Creation:
- ✅ Repetitive tasks that could be automated
- ✅ Functionality that would benefit other repos
- ✅ Multi-step processes that could be scripted
- ✅ Regular developer workflows
- ✅ Best practice standardization
- ✅ Common problem solutions

### Example Response Template:
```
💡 Slash Command Opportunity Detected!
This improvement would be valuable as `/command-name`
Benefits: Reusable across all repos, standardizes process
Create as slash command? (Recommended)
```

### Available Ecosystem Commands:
- `/git-trunk-flow` - Complete git workflow with best practices
- `/sync-all-commands` - Sync commands from all repos to master
- `/propagate-commands` - Distribute commands to all repos
- `/modernize-deps` - Update dependency management
- `/organize-structure` - Organize project structure

### Creating New Commands:
1. Implement in `.agent-os/commands/`
2. Test locally with `./slash_commands.py /command-name`
3. Sync to master with `/sync-all-commands`
4. Distribute with `/propagate-commands`

**Full Guidelines**: See MANDATORY_SLASH_COMMAND_ECOSYSTEM.md in assetutilities

---