# Contributing to Trishul

## Team expectations
- Keep `main` stable.
- Use one branch per task.
- Keep pull requests small and easy to review.
- Test changes before requesting review.
- Update docs when setup commands or interfaces change.
- Coordinate edits to shared files.
- Never commit secrets, build output or unapproved large assets.

## Before starting
```bash
git switch main
git pull origin main
git switch -c feature/short-task-name
```

## Before committing
```bash
git status
git diff
```

Review the changed files. Stage only the relevant files.

```bash
git add path/to/changed-file
git commit -m "Describe the change"
git push -u origin feature/short-task-name
```

Open a pull request on GitHub and describe:
- What changed.
- Why it changed.
- How it was tested.
- Any limitations or follow-up work.

## Review requirements
The reviewer should confirm:
- The change belongs to the intended module.
- The agreed interfaces are respected.
- Tests were run or blockers are clearly stated.
- No generated build files, secrets or irrelevant changes are included.
- Documentation is updated when needed.

## Main branch
Do not push directly to `main` unless the team has explicitly agreed to an exceptional recovery procedure. Do not force-push to `main`.

## Large files
Avoid committing datasets, build output, local model caches or large model weights by default. Discuss Git LFS or another approved asset location if large files are required.
