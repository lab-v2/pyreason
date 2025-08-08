
## Setting up Pre-Commit Hooks

To ensure code quality and consistency, set up the pre-commit hooks by running the following command:

```bash
pre-commit install --hook-type pre-commit --hook-type pre-push
```

This will configure the necessary hooks to run automatically during commits and pushes.

## Running Tests

This codebase has a unit and functional test suite.  You can run the unit tests using `pytest` with the following command:

```bash
pytest tests/unit
```

```bash
pytest tests/functional
```

