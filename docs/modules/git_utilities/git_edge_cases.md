### Git Edge Conditions

## Summary

- [Summary](#summary)
  - [Git undo last "N" commits](#git-undo-last-n-commits)
  - [Git commit files larger than 100MB](#git-commit-files-larger-than-100mb)

### Git undo last "N" commits

Applicability:
- Mistakenly wrote commit msg , click on commit button when there are changes to pull
- Mistakenly committed to wrong branch
- Committed a very large file (> 100 MB)

if you won't undo commit which leads merge branch commit issue.


Undo the Last Commit but Keep Changes

<code>
git reset --soft HEAD~1
</code>


<code>
git reset --soft HEAD~N
</code>


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

```bash
git commit -m "Your commit message"
```
Push to the remote repository.

```
git push origin 
```

Replace "main" with your branch name if necessary. Git LFS automatically handles the large files during the push.