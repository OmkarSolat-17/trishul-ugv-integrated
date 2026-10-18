# Testing & QA Strategy

> **Owner**: Integration Lead (in coordination with all leads)

This directory will hold cross-package integration tests, system-level smoke tests, and linting harnesses.

## 1. Test Levels

1. **Static Analysis & Linters**:
   - Python code: `flake8`, `pep257`, `mypy`.
   - C++ code: `ament_cpplint`, `ament_uncrustify`, `ament_cmake_copyright`.
   - URDF / Xacro validation: `check_urdf <(xacro model.urdf.xacro)`.
2. **Unit Tests**:
   - Placed within each package's `test/` directory.
3. **Integration & Launch Tests**:
   - Uses `launch_testing` to launch nodes, simulate topic inputs, and assert that expected outputs are produced within specified timeouts.

## 2. Running Tests
Once packages are implemented and built:
```bash
# Run all tests in the workspace
colcon test

# View test result summary
colcon test-result --all
```
