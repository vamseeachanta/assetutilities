## Git Edge Conditions

## Summary

- [Git Edge Conditions](#git-edge-conditions)
- [Summary](#summary)
  - [Git undo last "N" commits](#git-undo-last-n-commits)
  - [Git commit files larger than 100MB](#git-commit-files-larger-than-100mb)
  - [Git Pull request error](#git-pull-request-error)

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

### Git Pull request error

Encountered below error while trying to create a pull request:

```
This comparison is taking too long to generate.
Unfortunately it looks like we can’t render this comparison for you right now. It might be too big, or there might be something weird with your repository.
You can try running this command locally to see the comparison on your machine:
git diff master...202506 
```
This error typically occurs when the pull request involves a large number of changes or a large number of files. Here are some steps to resolve this:

--> Use **GitHub CLI** to create the pull request instead of the web interface. This will bypass the limitations of the web interface.

```bash
gh pr create --base master --head 202506 --title "Your PR Title" --body "Your PR Description"
```
Ex: gh pr create --base master --head 202506 --title "202507" --body "202507"

Pull request will be created successfully , you can track it out in the browser.

