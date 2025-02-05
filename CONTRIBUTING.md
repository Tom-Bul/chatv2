# Contributing to Village Life

First off, thank you for considering contributing to Village Life! It's people like you that make Village Life such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include screenshots if possible

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* Use a clear and descriptive title
* Provide a step-by-step description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and explain which behavior you expected to see instead
* Explain why this enhancement would be useful

### Pull Requests

* Fork the repo and create your branch from `develop`
* If you've added code that should be tested, add tests
* If you've changed APIs, update the documentation
* Ensure the test suite passes
* Make sure your code lints
* Issue that pull request!

## Development Process

1. Fork the repo
2. Create a new branch: `git checkout -b feature/VL-{number}-{description}`
3. Make your changes
4. Run tests: `python -m pytest`
5. Commit your changes using a descriptive commit message that follows our commit message conventions
6. Push to your fork and submit a pull request to the `develop` branch

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line
* Consider starting the commit message with an applicable prefix:
    * [core] for changes to core functionality
    * [ui] for user interface changes
    * [docs] for documentation changes
    * [test] for test-related changes
    * [perf] for performance improvements
    * [refactor] for code refactoring
    * [style] for formatting changes
    * [deps] for dependency updates

### Branch Naming Convention

* `feature/VL-{number}-{description}` for features
* `bugfix/VL-{number}-{description}` for bug fixes
* `hotfix/VL-{number}-{description}` for critical fixes
* `release/v{version}` for release branches

### Testing

* Write test cases for all new features
* Ensure all tests pass before submitting PR
* Maintain or improve test coverage
* Use pytest for testing

### Documentation

* Update README.md with details of changes to the interface
* Update CHANGELOG.md following the Keep a Changelog format
* Add docstrings to all new functions/methods
* Comment complex code sections

## Style Guide

### Python Style Guide

* Follow PEP 8
* Use type hints
* Write docstrings for all public methods
* Keep functions focused and small
* Use descriptive variable names

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality. Install them with:

```bash
pip install pre-commit
pre-commit install
```

### Development Environment

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -e .
```

3. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

## Questions?

Feel free to open an issue with your question or contact the maintainers directly.
