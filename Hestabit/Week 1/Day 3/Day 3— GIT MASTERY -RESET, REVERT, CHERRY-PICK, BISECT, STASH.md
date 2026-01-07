## **DAY 3 
### Learning Outcomes

- Ability to recover from mistakes
- Proper commit discipline
- ### Tasks

1. Create repository with **8+ commits**
       - Intentionally introduce a bug in **commit 4**
2. Use `git bisect` to detect the faulty commit
3. Fix the bug, then **git revert** (not reset) the buggy commit
4. Use stash workflow:
		`git stash git pull git stash apply`
5. Using two clones of the same repo:
	○​ Edit the same line in same file
	○​ Merge and resolve conflict (must keep both changes)

| Deliverable           | Format                                |
| --------------------- | ------------------------------------- |
| `bisect-session.txt`  | Terminal log                          |
| `stash-session.txt`   | How stash fixed workflow              |
| `MERGE-POSTMORTEM.md` | Explanation + screenshot + resolution |
| `commits`             | Graph must show branches + merge      |
	