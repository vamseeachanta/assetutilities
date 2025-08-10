#!/usr/bin/env python3
"""
Distribute Create Module Agent Command to All Repositories

This script distributes the /create-module-agent command to all
repositories in the GitHub ecosystem.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from assetutilities.agent_os.cross_repo.distributor import CrossRepoDistributor


def main():
    """Main distribution function."""
    print("🚀 Agent OS Cross-Repository Distribution")
    print("=" * 50)
    
    # Initialize distributor
    distributor = CrossRepoDistributor()
    
    # Check available repositories
    available_repos = distributor.get_available_repositories()
    print(f"\n📋 Found {len(available_repos)} repositories with Agent OS configuration:")
    for repo in available_repos:
        print(f"   - {repo}")
    
    # Auto-confirm distribution for automated execution
    print(f"\n✅ Proceeding with distribution to all {len(available_repos)} repositories...")
    
    # Distribute the command
    print("\n🔄 Starting distribution...")
    results = distributor.distribute_create_module_agent()
    
    # Create and display summary
    summary = distributor.create_distribution_summary(results)
    print(summary)
    
    # Save summary to file  
    summary_file = Path(__file__).parent / "distribution_summary.md"
    with open(summary_file, 'w') as f:
        f.write(summary)
    
    print(f"\n📄 Full summary saved to: {summary_file}")
    
    # Return appropriate exit code
    if results["failed"]:
        print(f"\n⚠️  Distribution completed with {len(results['failed'])} failures.")
        return 1
    else:
        print(f"\n🎉 Distribution completed successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(main())