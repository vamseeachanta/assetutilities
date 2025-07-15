#!/bin/bash
echo "Repository size before cleanup:"
du -sh .git

echo "Cleaning up..."
git reflog expire --expire=now --all
git gc --aggressive --prune=now
git remote prune origin
git fsck --unreachable
git prune --expire=now

echo "Repository size after cleanup:"
du -sh .git
