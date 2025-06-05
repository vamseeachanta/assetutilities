## Introduction

Git is a Verson control tool

## VS code - Checking commits

![commit history](image.png)

Other history using flog
![alt text](image-1.png)

### Pull Request

Prior to pull request, make sure the branch is up to date with the master branch. The key steps in VS Code are below

- You should be in the branch you are currently modifying (not master) 
- First merge master into this branch: To do merging:
  - Under source control, click the three dots 
  - Select in the menu Branch -> Merge Branch (see screenshot)
- ![merge branch with master](image-2.png) 
  - Select Master. 
  - Based on changes, 
    - It may have conflicts that need to be resolve manually, 
    - Following conflict resolution, should be clear to go.

<https://phoenixnap.com/kb/git-merge-master-into-branch>
<https://www.git-tower.com/learn/git/faq/git-pull-origin-master>

## Rebase

- Manipulate commmits message
- deelete commits
- reorder commits
- Use to clean up local history

### Usage 1 - Change message

Find the existing commits and associated messages
<code>
git log --oneline
</code>

<code>
git rebase -i HEAD~3
</code>

- Editor window pops up. All range of commits (except HEAD) is shown
- Only action keyword is given in this editor window
  - eg: change "pick" to "reword"
- Save and close
- Editor window opens again
- Check the changes

<code>

git log --oneline
</code>

### Usage 1 - Combine commits

Find the existing commits and associated messages
<code>
git log --oneline
</code>

<code>
git rebase -i HEAD~4
</code>

- Editor window pops up. All range of commits (except HEAD) is shown
- Only action keyword is given in this editor window
  - eg: change "squash" to "reword"
- give commit message
- Save and close
- Editor window opens again
- Check the changes

<code>

git log --oneline
</code>

### CLI: Git

<https://stackoverflow.com/questions/14893399/rebase-feature-branch-onto-another-feature-branch>

<https://www.youtube.com/watch?v=qsTthZi23VE>

### Interface: VS Code, GitLens

Steps:

<https://blog.delpuppo.net/why-i-love-gitlens-in-my-vscode-interactive-rebase>

<https://www.youtube.com/watch?v=3o_01F04bZ4>

### Interface: VS Code, GitLens

### References

<https://stackoverflow.com/questions/4786972/get-a-list-of-all-git-commits-including-the-lost-ones>
