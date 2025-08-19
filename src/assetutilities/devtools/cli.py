#!/usr/bin/env python
"""
AssetUtilities DevTools CLI - Command-line interface for repository management tools
"""

import sys
import argparse
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from .modernize_deps import (
    modernize_repository,
    find_python_repositories
)
from .propagate_commands import (
    CommandPropagator,
    find_repositories
)
from .organize_structure import (
    organize_repository
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def cmd_modernize_deps(args):
    """Execute the modernize-deps command."""
    base_dir = Path(args.target_dir).resolve()
    
    logger.info("🚀 Modernizing Dependencies Across Repositories")
    logger.info("=" * 50)
    
    # Find repositories
    if args.repos:
        repo_paths = [base_dir / repo for repo in args.repos]
        repo_paths = [p for p in repo_paths if p.exists()]
    else:
        repo_paths = find_python_repositories(base_dir)
    
    if not repo_paths:
        logger.error("❌ No Python repositories found!")
        return 1
    
    logger.info(f"📦 Found {len(repo_paths)} Python repositories")
    logger.info(f"🔧 Using {args.parallel} parallel workers")
    logger.info(f"💾 Backup: {'Enabled' if not args.no_backup else 'Disabled'}")
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be made")
        for repo in repo_paths:
            logger.info(f"  Would process: {repo.name}")
        return 0
    
    logger.info("")
    
    # Process repositories in parallel
    results = []
    with ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = {
            executor.submit(modernize_repository, repo, not args.no_backup): repo
            for repo in repo_paths
        }
        
        for future in as_completed(futures):
            repo = futures[future]
            try:
                result = future.result(timeout=60)
                results.append(result)
            except Exception as e:
                logger.error(f"❌ Failed to process {repo.name}: {e}")
                results.append({
                    "repo": repo.name,
                    "success": False,
                    "errors": [str(e)]
                })
    
    # Generate summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 Summary")
    logger.info("=" * 50)
    
    successful = sum(1 for r in results if r.get("success", False))
    failed = len(results) - successful
    
    logger.info(f"✅ Successful: {successful}/{len(results)} repositories")
    
    if failed > 0:
        logger.info(f"❌ Failed: {failed} repositories")
        logger.info("\nFailed repositories:")
        for result in results:
            if not result.get("success", False):
                logger.info(f"  • {result['repo']}: {', '.join(result.get('errors', ['Unknown error']))}")
    
    logger.info("\n✨ Dependency modernization complete!")
    
    return 0 if failed == 0 else 1


def cmd_organize_structure(args):
    """Execute the organize-structure command."""
    base_dir = Path(args.target_dir).resolve()
    
    logger.info("🚀 Organizing Project Structure")
    logger.info("=" * 50)
    
    # Find repositories
    if args.repos:
        repo_paths = [base_dir / repo for repo in args.repos]
        repo_paths = [p for p in repo_paths if p.exists()]
    else:
        # Process single repository if target is a repo
        if (base_dir / "pyproject.toml").exists() or (base_dir / "setup.py").exists():
            repo_paths = [base_dir]
        else:
            # Find all Python repositories
            repo_paths = find_python_repositories(base_dir)
    
    if not repo_paths:
        logger.error("❌ No repositories found!")
        return 1
    
    logger.info(f"📦 Found {len(repo_paths)} repositories")
    logger.info(f"🔧 Mode: {'DRY RUN' if args.dry_run else 'EXECUTE'}")
    
    # Process repositories
    results = []
    
    if len(repo_paths) == 1:
        # Single repository - process directly
        result = organize_repository(repo_paths[0], args.dry_run, args.force)
        results.append(result)
    else:
        # Multiple repositories - use parallel processing
        logger.info(f"⚡ Using {args.parallel} parallel workers\n")
        
        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            futures = {
                executor.submit(organize_repository, repo, args.dry_run, args.force): repo
                for repo in repo_paths
            }
            
            for future in as_completed(futures):
                repo = futures[future]
                try:
                    result = future.result(timeout=60)
                    results.append(result)
                except Exception as e:
                    logger.error(f"❌ Failed to process {repo.name}: {e}")
                    results.append({"success": False, "errors": [str(e)]})
    
    # Summary
    successful = sum(1 for r in results if r.get("success", False))
    logger.info(f"\n{'='*50}")
    logger.info(f"✅ Successfully organized: {successful}/{len(results)} repositories")
    
    return 0 if successful == len(results) else 1


def cmd_propagate_commands(args):
    """Execute the propagate-commands command."""
    # Determine source repository
    if args.source:
        source_repo = Path(args.source).resolve()
    else:
        # Try to find AssetUtilities
        assetutils_locations = [
            Path.cwd(),
            Path("/mnt/github/github/assetutilities"),
            Path.home() / "github" / "assetutilities",
        ]
        
        source_repo = None
        for location in assetutils_locations:
            if location.exists() and (location / ".agent-os/commands").exists():
                source_repo = location
                break
        
        if not source_repo:
            logger.error("❌ Could not find source repository with commands!")
            logger.info("Use --source to specify the repository containing commands")
            return 1
    
    target_base = Path(args.target_dir).resolve()
    
    logger.info("🚀 Propagating Commands to Repositories")
    logger.info("=" * 50)
    logger.info(f"📦 Source: {source_repo}")
    
    # Initialize propagator
    propagator = CommandPropagator(source_repo, target_base, args.force)
    
    # Discover commands
    discovered_commands = propagator.discover_commands()
    
    if not discovered_commands:
        logger.error("❌ No commands found in source repository!")
        return 1
    
    # Filter commands if specified
    if args.commands:
        discovered_commands = {
            k: v for k, v in discovered_commands.items()
            if k in args.commands
        }
    
    logger.info("📋 Commands to propagate:")
    for cmd_name in discovered_commands:
        logger.info(f"  • {cmd_name}")
    
    # Find target repositories
    if args.repos:
        repo_paths = [target_base / repo for repo in args.repos]
        repo_paths = [p for p in repo_paths if p.exists()]
    else:
        repo_paths = find_repositories(target_base)
    
    # Filter out source repository
    repo_paths = [r for r in repo_paths if r.resolve() != source_repo.resolve()]
    
    if not repo_paths:
        logger.error("❌ No target repositories found!")
        return 1
    
    logger.info(f"\n🎯 Target repositories: {len(repo_paths)}")
    
    if args.dry_run:
        logger.info("\n🔍 DRY RUN MODE - No changes will be made")
        for repo in repo_paths:
            logger.info(f"  Would propagate to: {repo.name}")
        return 0
    
    logger.info(f"🔧 Using {args.parallel} parallel workers")
    logger.info("")
    
    # Process repositories in parallel
    results = []
    logger.info("🔄 Processing repositories:")
    
    with ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = {
            executor.submit(propagator.propagate_to_repository, repo): repo
            for repo in repo_paths
        }
        
        for future in as_completed(futures):
            repo = futures[future]
            try:
                result = future.result(timeout=30)
                results.append(result)
                
                # Log progress
                if result.get("skipped"):
                    logger.info(f"  ⏭️  {result['repo']} [skipped - source repo]")
                elif result["success"]:
                    cmd_count = len(result["commands_installed"])
                    logger.info(f"  ✅ {result['repo']} [{cmd_count} commands installed]")
                else:
                    logger.info(f"  ❌ {result['repo']} [failed]")
                    
            except Exception as e:
                logger.error(f"  ❌ {repo.name} [error: {e}]")
                results.append({
                    "repo": repo.name,
                    "success": False,
                    "errors": [str(e)]
                })
    
    # Generate summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 Summary")
    logger.info("=" * 50)
    
    successful = sum(1 for r in results if r.get("success", False))
    failed = len(results) - successful
    
    logger.info(f"✅ Success: {successful}/{len(results)} repositories")
    
    if failed > 0:
        logger.info(f"❌ Failed: {failed} repositories")
    
    logger.info("\n✨ Command propagation complete!")
    
    return 0 if failed == 0 else 1


def main():
    """Main entry point for AssetUtilities DevTools CLI."""
    parser = argparse.ArgumentParser(
        prog='assetutils-devtools',
        description='AssetUtilities DevTools - Repository Management and Automation'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # modernize-deps command
    mod_parser = subparsers.add_parser(
        'modernize-deps',
        help='Modernize dependency management across repositories'
    )
    mod_parser.add_argument(
        '--target-dir',
        default='.',
        help='Directory containing repositories (default: current directory)'
    )
    mod_parser.add_argument(
        '--parallel',
        type=int,
        default=5,
        help='Number of parallel workers (default: 5)'
    )
    mod_parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating backups'
    )
    mod_parser.add_argument(
        '--repos',
        nargs='+',
        help='Specific repositories to process'
    )
    mod_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    # organize-structure command
    org_parser = subparsers.add_parser(
        'organize-structure',
        help='Enforce module-based project organization'
    )
    org_parser.add_argument(
        '--target-dir',
        default='.',
        help='Directory containing repositories (default: current directory)'
    )
    org_parser.add_argument(
        '--repos',
        nargs='+',
        help='Specific repositories to organize'
    )
    org_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    org_parser.add_argument(
        '--force',
        action='store_true',
        help='Force overwrite existing files'
    )
    org_parser.add_argument(
        '--parallel',
        type=int,
        default=1,
        help='Number of parallel workers (default: 1)'
    )
    
    # propagate-commands command
    prop_parser = subparsers.add_parser(
        'propagate-commands',
        help='Distribute slash commands across repositories'
    )
    prop_parser.add_argument(
        '--source',
        help='Source repository containing commands'
    )
    prop_parser.add_argument(
        '--target-dir',
        default='.',
        help='Directory containing target repositories'
    )
    prop_parser.add_argument(
        '--commands',
        nargs='+',
        help='Specific commands to propagate'
    )
    prop_parser.add_argument(
        '--parallel',
        type=int,
        default=5,
        help='Number of parallel workers (default: 5)'
    )
    prop_parser.add_argument(
        '--force',
        action='store_true',
        help='Force overwrite existing files'
    )
    prop_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done'
    )
    prop_parser.add_argument(
        '--repos',
        nargs='+',
        help='Specific repositories to target'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    if args.command == 'modernize-deps':
        return cmd_modernize_deps(args)
    elif args.command == 'propagate-commands':
        return cmd_propagate_commands(args)
    elif args.command == 'organize-structure':
        return cmd_organize_structure(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())