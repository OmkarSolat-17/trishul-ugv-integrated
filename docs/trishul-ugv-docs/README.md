# Trishul UGV

Trishul is a simulation-based prototype for **vision-based autonomous navigation of an Unmanned Ground Vehicle (UGV)** in an outdoor-like environment.

The goal is to demonstrate a robot that can move from Point A to Point B, use camera-based perception to identify possible hazards, estimate its position, and avoid obstacles.

> **Project status:** Planning and development guide. Features must only be marked complete after they are implemented and tested. The first version is simulation-only; it is not evidence of real-world robot performance.
>
> **Subsystem Status Note:** The autonomous navigation subsystem (`trishul_navigation`) is fully implemented, verified, and operational on branch `trishul-navigation`. See [src/trishul_navigation/README.md](../../src/trishul_navigation/README.md) and root [README.md](../../README.md).

## Start here

1. Read [`PRODUCT.md`](PRODUCT.md) for the full project goal and scope.
2. Read [`TEAM_ROLES.md`](TEAM_ROLES.md) to find your role and work area.
3. Read [`SETUP_GUIDE.md`](SETUP_GUIDE.md) before installing tools.
4. Read [`GIT_WORKFLOW.md`](GIT_WORKFLOW.md) before changing or pushing code.
5. Read [`INTERFACES.md`](INTERFACES.md) before connecting modules.
6. Read [`TESTING_AND_DEMO.md`](TESTING_AND_DEMO.md) before integration or the hackathon demo.
7. Read [`AI_CODING_GUIDE.md`](AI_CODING_GUIDE.md) when using Antigravity or another AI coding assistant.

## Planned technology

- Windows 11 + WSL 2
- Ubuntu 24.04
- ROS 2 Jazzy
- Compatible Gazebo Harmonic integration
- RViz 2
- Python and OpenCV
- Nav2
- SLAM Toolbox for a range-sensor baseline, if selected
- A lightweight pretrained vision model, if feasible
- Git and GitHub

Confirm current compatibility and follow official installation documentation before installing.

## Main rule

One GitHub repository, five module owners, small feature branches, pull requests, tests, and one known-good demo laptop.

## Official learning links

- ROS 2 Jazzy installation: https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html
- ROS 2 tutorials: https://docs.ros.org/en/jazzy/Tutorials.html
- Nav2: https://docs.nav2.org/
- Gazebo Harmonic: https://gazebosim.org/docs/harmonic/
- GitHub Docs: https://docs.github.com/en
