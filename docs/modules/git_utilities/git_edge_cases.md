### Git Edge Conditions

## Summary

- [Summary](#summary)
  - [Git undo last "N" commits](#git-undo-last-n-commits)

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