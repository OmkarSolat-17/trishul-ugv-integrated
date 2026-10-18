# Git and GitHub Workflow

## Why we use GitHub

GitHub stores the team's shared repository. Git records changes and lets each member work on a separate branch. The goal is to avoid overwriting work and to keep `main` stable.

## One repository

Use one shared repository named `trishul-ugv`. Do not create separate repositories for simulation, AI, localization and navigation unless the team explicitly changes the architecture.

## Branches

`main` should contain the reviewed, stable version.

Suggested feature branches:
- `feature/simulation`
- `feature/vision`
- `feature/localization`
- `feature/navigation`
- `feature/integration`
- `fix/short-description`

A branch is a separate line of work. It is not a separate project.

## First-time clone

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd trishul-ugv
```

## Start a task

```bash
git switch main
git pull origin main
git switch -c feature/your-task
```

Replace `feature/your-task` with a short, meaningful branch name.

## Save work

Check what changed:

```bash
git status
git diff
```

Stage only the files relevant to your task:

```bash
git add path/to/your/file
git commit -m "Describe the change clearly"
git push -u origin feature/your-task
```

Avoid `git add .` if you are unsure whether generated files or secrets are present. Inspect `git status` first.

## Open a pull request

1. Open the repository on GitHub.
2. Create a pull request from your feature branch into `main`.
3. Explain what changed and how you tested it.
4. Request review from the integration lead or relevant module owner.
5. Fix requested changes and push updates to the same branch.
6. Merge only after review and required tests pass.

## After your pull request is merged

```bash
git switch main
git pull origin main
git switch -c feature/next-task
```

Use a new branch for a new task.

## Conflict prevention

- Keep pull requests small.
- Avoid editing another module's files without coordination.
- Agree on interfaces before connecting modules.
- Tell the team before changing shared configuration.
- Pull the latest `main` before starting new work.
- Never force-push to `main`.
- Do not merge code that breaks the known-good demo.
- If a conflict appears, stop and ask the owners to resolve it carefully; do not blindly choose one side.

## What not to commit

- `build/`, `install/`, `log/`
- `__pycache__/`, `.pytest_cache/`, local virtual environments
- API keys, passwords, tokens or personal settings
- Huge datasets or generated model caches
- Large model weights unless the team explicitly chooses a suitable storage method

## Commit message examples

- `Add outdoor Gazebo world`
- `Add camera image subscriber`
- `Configure baseline navigation`
- `Document localization frames`
- `Add integration smoke test`

## Pull request checklist

Before requesting review, confirm:
- [ ] I changed only files related to this task.
- [ ] I tested the change or clearly stated why testing is blocked.
- [ ] I did not commit generated build files or secrets.
- [ ] I updated documentation if commands or interfaces changed.
- [ ] I explained how the reviewer can verify the change.

## If the project breaks after a merge

1. Stop adding new features.
2. Read the failing launch/build/test output.
3. Identify the last known-good version and recent changes.
4. Reproduce the failure.
5. Fix or revert the specific change with the owner's agreement.
6. Re-run the full integration test before continuing.
