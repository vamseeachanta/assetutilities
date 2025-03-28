## Introduction

Git is a Verson control tool

## Summary

### Important Considerations

- Do not upload any file greater than 50 MB.
- If big output files (>1 MB) can be reproduced with little computational and manual effort, do not upload them.
- Working in a team:
  - Learn to pull.
  - Push will be done as team with the project lead.

## General Workflows

[https://guides.github.com/introduction/flow/](https://guides.github.com/introduction/flow/)

### Cloning a repo

Git cloning instructions:

- Copy the repository link in git bash
  - $git  clone <repository_url>
  - $git  clone <https://vamseeachanta@dev.azure.com/vamseeachanta/aceengineer/_git/aceengineer>

### Forking a repo

### Cloning vs. Forking

### Creating new repo from Existing Repo

[https://stackoverflow.com/questions/9844082/how-to-create-a-new-git-repository-from-an-existing-one](https://stackoverflow.com/questions/9844082/how-to-create-a-new-git-repository-from-an-existing-one)

### Code Development

The typical workflow followed in Azure Devops is given below:

- Pull the latest master code
- The typical workflow followed in Azure Devops is given below:
  - Pull the latest master code
  - Start working on your local branch
- Create a local branch (Never work in master on your computer)
  - git branch <branchname>
  - git branch <ExistingCodes>
  - or use GUI alternatively as below and create “New Branch”
- Checkout the local branch
  - Git branch (to view all the existing branches)
  - git checkout <branchname>
  - git checkout <ExistingCodes>
- Create files, edit codes per the project needs

When branch is ready for review (and/or approval):

- Push the branch to the origin
  - Commit the relevant files in following steps
  - Add the files:
    - git add –A (Add all files)
    - git add ASMEB31\ASMEB31Sizing.py (Add all files)
  - Git commit -m "Initial Push"
  - Push the files to the origin
    - git push -u origin <branch>
    - git push -u origin <ExistingCodes>
- Create a pull request
  - Go to Azure devops or github website
  - Create the pull request
- Copy the person who should be reviewing the code in the pull request.

### Rebase

Git Rebase. Always rebase the local branch that typically (way) behind master. Rebase is more easier to merge stale code than direct merge.

- Working steps in PyCharm:
  - Pre-steps:
    - Ensure the latest master branch (or intended commit) is pulled into local
  - Execution steps:
    - Select the select branch (intended) to rebase
    - Click (but do not select) on Master branch menu
    - Click rebase current (i.e. select branch) onto Selected (i.e. master).

- Working steps in Command prompt:
  - Pre-steps:
    - Ensure the latest master branch (or intended commit) is pulled into local
  - Execution steps:
    - Select the select branch (intended) to rebase
    - git rebase <reference_branch_will_remain_untouched>

- Key references:
<https://git-scm.com/docs/git-rebase>
<https://stackoverflow.com/questions/804115/when-do-you-use-git-rebase-instead-of-git-merge>
<https://www.perforce.com/blog/vcs/git-rebase-vs-merge-which-better>
<https://www.atlassian.com/git/tutorials/merging-vs-rebasing>

## Commands

To help summarize data
git log --graph --decorate --pretty=oneline --abbrev-commit

C:\Users\achantv\Documents\GitHub\client_projects>git log --graph --decorate --pretty=oneline --abbrev-commit

- 6f24f52 (HEAD -> main) Merge branch 'main' of <https://github.com/vamseeachanta/client_projects>
|\
| * c425885 (origin/main, origin/HEAD) Feature/orcaflex analysis (#2)
- | 0e4759b wip
- | db2d53c wip
- | 29d8a17 drilling
|/
- 8ab3d43 wip
- 30edef8 wip
- d49fbd9 Update README.md
- 06024c6 Update developers.md
- a4a7ede Feature/start ver (#1)
- 9fa9599 Update README.md
- 86ac5dc Initial commit

## Commit & Undo Commit

**Undo Commit**
step 1: Get the commit logs and ids using below
<code>
git log --oneline

Output:
8ffa550 (HEAD -> main) wip
3e8b1eb wip
256ec03 (origin/main, origin/HEAD) wip
27c5043 wip
1a04ce8 wip
</code>

step 2: Revert changes from each ID using below command
<code>
git revert 3c8ad5e
</code>

### Remove all local branch changes

git reset --hard origin/<branch_names>

## Installation

If version shows up, this means that git is successfully installed.
Check Installation and version
git –version

Install using the below link:

[https://git-scm.com/download/win](https://git-scm.com/download/win)

## Files to ignore guidance

|   Language |  Extensions |  Links |   comments |
|---|---|---|---|
| Python  | *.pyc | - | n/a |

## SSL verification

<pre>

</pre>

<https://stackoverflow.com/questions/9008309/how-do-i-set-git-ssl-no-verify-for-specific-repos-only>

## References

| S.No |   Short Description |  Comment |  Links |   Additional comments |
|---|---|---|---|---|
|  | Draft manual  | Git document | [https://realpython.com/python-git-github-intro/](docs\man\GIT-0001-01 Git and Working (DRAFT1).pdf) | Convert to this Markdown |
|  | Intro  | A great intro article | [https://realpython.com/python-git-github-intro/](https://realpython.com/python-git-github-intro/) | n/a |
|  | Intro  | A very good Git intro video | [https://www.youtube.com/watch?v=HVsySz-h9r4](https://www.youtube.com/watch?v=HVsySz-h9r4) | n/a |
|  | Add .gitignore file  | - | [https://stackoverflow.com/questions/10744305/how-to-create-gitignore-file](https://stackoverflow.com/questions/10744305/how-to-create-gitignore-file ) |  |
|  | Branch Features and Production  | - | [http://nvie.com/posts/a-successful-git-branching-model/](http://nvie.com/posts/a-successful-git-branching-model/) |  |
|  | sparseCheckout  | - | [http://scriptedonachip.com/git-sparse-checkout](http://scriptedonachip.com/git-sparse-checkout) |  |
|  | clone only a subdirectory  | - | [https://stackoverflow.com/questions/600079/how-do-i-clone-a-subdirectory-only-of-a-git-repository](https://stackoverflow.com/questions/600079/how-do-i-clone-a-subdirectory-only-of-a-git-repository) |  |
|  | submodules  | - | [https://git-scm.com/book/en/v2/Git-Tools-Submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) |  |
|  | cheatsheet  | - | [https://github.com/github/training-kit/blob/master/downloads/github-git-cheat-sheet.md](https://github.com/github/training-kit/blob/master/downloads/github-git-cheat-sheet.md) |  |
|  | Pro Git Book  | - | <https://git-scm.com/book/en/v2>](<https://git-scm.com/book/en/v2>) |  |

## VS code - Checking commits

![commit history](image.png)
