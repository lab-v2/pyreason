
## Getting Started

Install the project requirements and the pre-commit framework:

```bash
pip install -r requirements.txt
pip install pre-commit
```

## Setting up Pre-Commit Hooks

To ensure code quality and consistency, enable the pre-commit hooks:

```bash
pre-commit install --hook-type pre-commit --hook-type pre-push
```

On every commit, the hooks will run the unit tests located in
`tests/unit/disable_jit` and `tests/unit/dont_disable_jit`. Functional tests in
`tests/functional` execute on every push. You can trigger all checks manually
with `pre-commit run --all-files`.

## Linting

We are working to update the codebase to comply with `ruff` linting rules. Run
this command to view linting results:

```bash
ruff check .
```

## Running Tests Manually

The automated hooks cover most scenarios, but you can invoke the test suites
directly:

```bash
pytest tests/unit
```

```bash
pytest tests/functional
```

Running tests locally before committing or pushing helps catch issues early and
speeds up code review.
