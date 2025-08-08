repos:
  - repo: local
    hooks:
      - id: pytest
        name: Run pytest
        entry: bash -c 'git diff --cached --name-only | grep -E "\.py$" && pytest || echo "No Python changes, skipping tests."'
        language: system
        pass_filenames: false