## Git Edge Conditions

## Summary

- [Git Edge Conditions](#git-edge-conditions)
- [Summary](#summary)
  - [Git undo last "N" commits](#git-undo-last-n-commits)
  - [Git commit files larger than 100MB](#git-commit-files-larger-than-100mb)
  - [Git Large file Sync ( Local vs Git history)](#git-large-file-sync--local-vs-git-history)

### Git undo last "N" commits

Applicability:
- Mistakenly wrote commit msg , click on commit button when there are changes to pull
- Mistakenly committed to wrong branch
- Committed a very large file (> 100 MB)

Undo the Last Commit but Keep Changes

<code>
git reset --soft HEAD~1
</code>

<code>
git reset --soft HEAD~N
</code>

**Committed Too Soon? Here is How to Change Your Last Git Commit**
https://levelup.gitconnected.com/committed-too-soon-here-is-how-to-change-your-last-git-commit-30700d0d2732


### Git commit files larger than 100MB

encountered below error while pushing some refs to github :

```
git push origin 202502:202502 error: RPC failed; HTTP 408 curl 22 The requested URL returned error: 408 send-pack: unexpected disconnect while reading sideband packet fatal: the remote end hung up unexpectedly Everything up-to-date
```

GitHub restricts individual file sizes to 100MB. To commit files larger than this, Git Large File Storage (LFS) should be used. Here's how: Install Git LFS.
Code

```bash
git lfs install
```

Track the large file(s).

```bash
git lfs track "filename"
```

Replace "filename" with the actual name of your large file or a pattern like "*.zip" to include all zip files. This command creates or modifies a .gitattributes file. Add and commit.

Push to the remote repository.

```
git push origin 
```

### Git Large file Sync ( Local vs Git history)

Encountered below error while pushing changes to github which already deleted manually:

```
remote: error: File data/modules/bsee/zip/dsptsdelimit/dsptsdelimit.ZIP is 132.54 MB; this exceeds GitHub's file size limit of 100.00 MB
 ! [remote rejected] 202506 -> 202506 (pre-receive hook declined)
error: failed to push some refs to 'https://github.com/vamseeachanta/energydata.git'
```

To resolve this, you can use the following steps:

Install git-filter-repo via pip :
```bash
pip install git-filter-repo
```

run below command to remove the file from the git history:
```bash
git filter-repo --path data/modules/bsee/zip/dsptsdelimit/dsptsdelimit.ZIP --invert-paths
```

This will raise one warning as follows:
```
Aborting: Refusing to destructively overwrite repo history since
this does not look like a fresh clone.
  (expected freshly packed repo)
Please operate on a fresh clone instead.  If you want to proceed
anyway, use --force.
```

 Option 1: Recommended – Use a Fresh Clone
```bash
git clone --mirror https://github.com/vamseeachanta/energydata.git cleaned-repo
```

Go into the cloned repo:
```bash
cd cleaned-repo
```

run the filter-repo command again:
```bash
git filter-repo --path data/modules/bsee/zip/dsptsdelimit/dsptsdelimit.ZIP --invert-paths
```

Push the cleaned repo back to GitHub:
```bash
git push origin --force
```

If you get , below warning ,
```
fatal: The current branch master has no upstream branch.
To push the current branch and set the remote as upstream, use

    git push --set-upstream origin master

To have this happen automatically for branches without a tracking
upstream, see 'push.autoSetupRemote' in 'git help config'.
```

run this command 
```bash
git push --set-upstream origin 202506
```

if you again get anotehr warning called
```bash
fatal: 'origin' does not appear to be a git repository
fatal: Could not read from remote repository.

Please make sure you have the correct access rights
and the repository exists.
```
✅ Step 1: Check Remote Configuration
Run this to list your remotes:

```bash
git remote -v
```
If it returns nothing, then you don't have any remote (i.e., no origin).

✅ Step 2: Add Your GitHub Repo as a Remote
Since you're working with:
```bash
https://github.com/vamseeachanta/energydata.git
``` 
Run this:
```bash
git remote add origin https://github.com/vamseeachanta/energydata.git
```
Then confirm with:
```bash
git remote -v
```
You should now see:
```bash
origin  https://github.com/vamseeachanta/energydata.git (fetch)
origin  https://github.com/vamseeachanta/energydata.git (push)
```
✅ Step 3: Push Your Branch
Now push the 202506 branch and set the upstream:

```bash
git push --set-upstream origin 202506
```

Now , if you get 
```bash
To https://github.com/vamseeachanta/energydata.git
 ! [rejected]        202506 -> 202506 (fetch first)
error: failed to push some refs to 'https://github.com/vamseeachanta/energydata.git'
hint: Updates were rejected because the remote contains work that you do not
hint: have locally. This is usually caused by another repository pushing to
hint: the same ref. If you want to integrate the remote changes, use
hint: 'git pull' before pushing again.
hint: See the 'Note about fast-forwards' in 'git push --help' for details.
```
the reason for this ,

There are commits on GitHub that your local branch doesn’t have, and Git is being cautious to avoid overwriting remote changes.

Since you've rewritten history with git filter-repo, we don’t want to merge the remote changes — we want to overwrite them.

Solution: Force Push to Overwrite the Remote Branch
Since this is intentional and you cleaned the repo:
```bash
git push --force origin 202506
``` 

Done , you are good to go.