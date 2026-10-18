# Using Antigravity or Another AI Coding Assistant

AI tools can help the team understand code, draft small modules, explain errors, create tests and review changes. They can also generate incorrect code or modify unrelated files. Treat generated code as a proposal that must be reviewed and tested.

## Good tasks for AI

### Member 1 — Simulation
- Explain an existing URDF/SDF file.
- Draft a small robot-model change.
- Diagnose a Gazebo launch error using the full log.
- Explain a sensor topic and its message type.

### Member 2 — Vision/AI
- Draft a ROS 2 image subscriber.
- Explain OpenCV processing.
- Add a test for a detection-output format.
- Help interpret model runtime or dependency errors.

### Member 3 — Localization
- Explain coordinate frames and transforms.
- Review a localization configuration.
- Help diagnose missing transforms or mapping errors.
- Compare options without pretending a complex visual-SLAM integration is trivial.

### Member 4 — Navigation
- Explain Nav2 parameters.
- Help interpret planner/cost-map logs.
- Draft repeatable goal-navigation tests.
- Review obstacle scenarios.

### Member 5 — Integration
- Review pull requests.
- Check whether modules use the agreed interfaces.
- Draft launch/test scripts.
- Help diagnose clean-build failures.
- Improve setup and demo documentation.

## Master instruction to give an AI coding assistant

You are helping with the Trishul UGV repository. Read `README.md`, `PRODUCT.md`, `TEAM_ROLES.md`, `INTERFACES.md`, and the relevant package files before changing code.

Work only on the task I specify. Respect the module ownership and interface agreements. Do not rename topics, message types, frames, packages or launch entry points without explaining the reason and listing affected modules. Do not edit unrelated files. Do not claim that tests passed unless you actually ran them and saw the result. If a required tool, dependency, model weight or interface is missing, stop and explain what is needed. Before editing, summarize the intended changes. After editing, list files changed, commands to test, actual test results and remaining risks.

## Example task prompt

“Inspect the existing Trishul repository and the interface agreement. Work only in `src/trishul_perception/`. Implement a minimal Python node that subscribes to the already agreed camera image topic and publishes the agreed detection message. Do not invent topic names or message fields. If the interface is not yet defined, ask for clarification rather than guessing. Add a basic test and document dependencies. Show the proposed file changes before modifying unrelated code.”

## Rules for the team
- Give the AI the exact error and relevant files.
- Ask for small changes, not the whole robot at once.
- Read and understand generated code.
- Run the suggested commands yourself.
- Review `git diff` before committing.
- Do not paste passwords, access tokens or private keys.
- Do not let AI merge or push unreviewed code.
- Never describe a feature as complete based only on generated code.

## If AI-generated code breaks the project
1. Stop and save the error log.
2. Check `git status` and `git diff`.
3. Identify the exact files changed.
4. Ask the module owner to review the changes.
5. Revert only the problematic change with care.
6. Run the module test and full integration test again.
